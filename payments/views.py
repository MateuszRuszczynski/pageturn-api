import stripe
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from payments.models import Payment
from payments.serializers import PaymentSerializer
from payments.services import create_stripe_checkout_session
from borrowings.models import Borrowing
from decimal import Decimal


class PaymentViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = PaymentSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = Payment.objects.select_related("borrowing__book", "borrowing__user")
        if not self.request.user.is_staff:
            return queryset.filter(borrowing__user=self.request.user)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        borrowing_id = request.data.get("borrowing")
        try:
            borrowing = Borrowing.objects.get(id=borrowing_id)
        except Borrowing.DoesNotExist:
            return Response(
                {"detail": "Specified borrowing does not exist."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        duration = (borrowing.expected_return_date - borrowing.borrow_date).days
        days = max(duration, 1)

        calculated_amount = Decimal(days) * borrowing.book.daily_fee

        payment = serializer.save(money_to_pay=calculated_amount)

        stripe_data = create_stripe_checkout_session(payment, request)

        if stripe_data:
            payment.session_url = stripe_data.get("session_url")
            payment.session_id = stripe_data.get("session_id")
            payment.save()

            return Response(
                self.get_serializer(payment).data, status=status.HTTP_201_CREATED
            )

        return Response(
            {"detail": "Failed to initialize external billing gateway session."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    @action(methods=["GET"], detail=False, url_path="success")
    def success(self, request):
        session_id = request.query_params.get("session_id")
        if not session_id:
            return Response(
                {"detail": "Missing session_id"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            payment = Payment.objects.get(session_id=session_id)
            session = stripe.checkout.Session.retrieve(session_id)

            if session.payment_status == "paid":
                payment.status = Payment.StatusChoices.PAID
                payment.save()
                return Response(
                    {"detail": "Payment successful!", "status": payment.status}
                )

            return Response(
                {"detail": "Payment pending"}, status=status.HTTP_400_BAD_REQUEST
            )
        except (Payment.DoesNotExist, stripe.error.StripeError):
            return Response(
                {"detail": "Error verification"}, status=status.HTTP_400_BAD_REQUEST
            )

    @action(methods=["GET"], detail=False, url_path="cancel")
    def cancel(self, request):
        return Response({"detail": "Payment process was paused or cancelled."})
