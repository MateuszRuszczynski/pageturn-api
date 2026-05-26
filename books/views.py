from rest_framework import viewsets
from books.serializers import BookSerializer
from books.permissions import IsAdminOrReadOnly
from books.models import Book


class BookViewSet(viewsets.ModelViewSet):
    serializer_class = BookSerializer
    permission_classes = (IsAdminOrReadOnly,)

    def get_queryset(self):
        return Book.objects.all().order_by("title")
