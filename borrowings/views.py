from rest_framework import viewsets, mixins, status
from rest_framework.permissions import IsAuthenticated
from borrowings.models import Borrowing
from borrowings.serializers import (
    BorrowingReadSerializer,
    BorrowingCreateSerializer,
)
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from datetime import date
from payments.models import Payment
from payments.services import create_stripe_checkout_session
from decimal import Decimal
from rest_framework import serializers


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
                overdue_days = (today - borrowing.expected_return_date).days

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

        return_serializer = BorrowingDetailSerializer(
            serializer.instance, context={"request": request}
        )
        headers = self.get_success_headers(return_serializer.data)
        return Response(
            return_serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )
