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
