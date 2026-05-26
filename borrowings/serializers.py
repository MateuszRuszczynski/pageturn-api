from datetime import date, timedelta
from django.db import transaction
from rest_framework import serializers
from books.models import Book
from books.serializers import BookSerializer
from borrowings.models import Borrowing


class BorrowingReadSerializer(serializers.ModelSerializer):
    book = BookSerializer(read_only=True)
    user = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "book",
            "user",
        )
        read_only_fields = fields


class BorrowingCreateSerializer(serializers.ModelSerializer):
    expected_return_date = serializers.DateField(required=False)

    class Meta:
        model = Borrowing
        fields = ("id", "book", "expected_return_date")

    def validate_book(self, value):
        if value.inventory <= 0:
            raise serializers.ValidationError("This book is out of stock.")
        return value

    def validate(self, attrs):
        expected_date = attrs.get("expected_return_date")

        if expected_date:
            if expected_date < date.today():
                raise serializers.ValidationError(
                    {
                        "expected_return_date": "The expected return date cannot be in the past."
                    }
                )
        else:
            attrs["expected_return_date"] = date.today() + timedelta(days=14)

        return attrs

    def create(self, validated_data):
        with transaction.atomic():
            book = validated_data["book"]
            book.inventory -= 1
            book.save()

            return Borrowing.objects.create(**validated_data)
