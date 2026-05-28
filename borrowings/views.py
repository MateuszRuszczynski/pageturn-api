from datetime import date
from decimal import Decimal

from django.db import transaction
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    extend_schema,
    extend_schema_view,
)
from rest_framework import mixins, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from borrowings.models import Borrowing
from borrowings.serializers import (
    BorrowingCreateSerializer,
    BorrowingReadSerializer,
)
from payments.models import Payment
from payments.services import create_stripe_checkout_session


@extend_schema_view(
    list=extend_schema(
        summary="List borrowings",
        description="Retrieve a list of borrowings. Regular users see only their own, while Admins get a global view. Supports filtering by `user_id` and `is_active`.",
        parameters=[
            OpenApiParameter(
                name="is_active",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter by active status: 'true' (not returned) or 'false' (returned).",
                required=False,
            ),
            OpenApiParameter(
                name="user_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="[ADMIN ONLY] Filter borrowings by a specific User ID.",
                required=False,
            ),
        ],
    ),
    retrieve=extend_schema(
        summary="Get borrowing details",
        description="Retrieve detailed information about a specific borrowing record, including nested book data.",
    ),
    create=extend_schema(
        summary="Create a new borrowing",
        description="Allow authenticated users to borrow a book. Validates book inventory, automatically calculates the expected return date, and initializes a Stripe payment session.",
    ),
    return_book=extend_schema(
        summary="Return a borrowed book",
        description="Endpoint to handle book returns. If the return is overdue, the system automatically calculates a fine and generates an associated Stripe payment session.",
    ),
)
@extend_schema(tags=["Borrowings & Returns"])
class BorrowingViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = Borrowing.objects.select_related("book", "user")

        if not self.request.user.is_staff:
            return queryset.filter(user=self.request.user)
        else:
            user_id = self.request.query_params.get("user_id")
            if user_id:
                queryset = queryset.filter(user_id=user_id)

        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            is_active_bool = is_active.lower() in ("true", "1")
            queryset = queryset.filter(actual_return_date__isnull=is_active_bool)

        return queryset

    def get_serializer_class(self):
        if self.action in ("list", "retrieve", "return_book"):
            return BorrowingReadSerializer
        return BorrowingCreateSerializer

    @action(methods=["POST"], detail=True, url_path="return")
    def return_book(self, request, pk=None):
        borrowing = self.get_object()

        if borrowing.actual_return_date is not None:
            return Response(
                {"detail": "This book has already been returned."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            borrowing.actual_return_date = date.today()
            borrowing.save()

            book = borrowing.book
            book.inventory += 1
            book.save()

            if date.today() > borrowing.expected_return_date:
                overdue_days = (date.today() - borrowing.expected_return_date).days

                fine_amount = Decimal(overdue_days) * book.daily_fee * Decimal("2.0")

                Payment.objects.create(
                    status=Payment.StatusChoices.PENDING,
                    type=Payment.TypeChoices.FINE,
                    borrowing=borrowing,
                    money_to_pay=fine_amount,
                )

        serializer = self.get_serializer(borrowing)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @transaction.atomic
    def perform_create(self, serializer):
        borrowing = serializer.save(user=self.request.user)

        days = (borrowing.expected_return_date - borrowing.borrow_date).days
        rental_days = max(days, 1)
        total_price = Decimal(rental_days) * borrowing.book.daily_fee

        payment = Payment.objects.create(
            status=Payment.StatusChoices.PENDING,
            type=Payment.TypeChoices.PAYMENT,
            borrowing=borrowing,
            money_to_pay=total_price,
        )

        stripe_data = create_stripe_checkout_session(payment, self.request)

        if stripe_data:
            payment.session_url = stripe_data.get("session_url")
            payment.session_id = stripe_data.get("session_id")
            payment.save()
        else:
            raise serializers.ValidationError(
                {
                    "payment": "External billing gateway session creation failed. Transaction aborted."
                }
            )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        self.perform_create(serializer)

        return_serializer = BorrowingReadSerializer(
            serializer.instance, context={"request": request}
        )
        headers = self.get_success_headers(return_serializer.data)
        return Response(
            return_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )
