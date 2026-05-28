from rest_framework import viewsets
from drf_spectacular.utils import extend_schema, extend_schema_view

from books.models import Book
from books.permissions import IsAdminOrReadOnly
from books.serializers import BookSerializer


@extend_schema_view(
    list=extend_schema(
        summary="List all books",
        description="Retrieve a list of all available books in the library. Supports filtering options.",
    ),
    retrieve=extend_schema(
        summary="Get book details",
        description="Retrieve detailed information about a specific book by its ID.",
    ),
    create=extend_schema(
        summary="Add a new book",
        description="[ADMIN] Allow staff to add a new book entry to the catalog.",
    ),
    update=extend_schema(
        summary="Update a book completely",
        description="[ADMIN] Fully update a book's information (PUT).",
    ),
    partial_update=extend_schema(
        summary="Update a book partially",
        description="[ADMIN] Partially update a book's fields (PATCH).",
    ),
    destroy=extend_schema(
        summary="Delete a book",
        description="[ADMIN] Permanently remove a book entry from the database.",
    ),
)
@extend_schema(tags=["Books Management"])
class BookViewSet(viewsets.ModelViewSet):
    serializer_class = BookSerializer
    permission_classes = (IsAdminOrReadOnly,)

    def get_queryset(self):
        return Book.objects.all().order_by("title")
