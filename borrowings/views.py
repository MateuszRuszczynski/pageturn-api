from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated
from borrowings.models import Borrowing
from borrowings.serializers import (
    BorrowingReadSerializer,
    BorrowingCreateSerializer,
)


class BorrowingViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = Borrowing.objects.select_related(
            "book",
            "user"
        )
        if not self.request.user.is_staff:
            return queryset.filter(user=self.request.user)
        return queryset

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return BorrowingReadSerializer
        return BorrowingCreateSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
