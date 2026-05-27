from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated
from payments.models import Payment
from payments.serializers import PaymentSerializer


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
