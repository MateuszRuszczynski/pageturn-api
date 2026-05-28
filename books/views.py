from rest_framework import viewsets

from books.models import Book
from books.permissions import IsAdminOrReadOnly
from books.serializers import BookSerializer


class BookViewSet(viewsets.ModelViewSet):
    serializer_class = BookSerializer
    permission_classes = (IsAdminOrReadOnly,)

    def get_queryset(self):
        return Book.objects.all().order_by("title")
