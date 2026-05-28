from datetime import date, timedelta

from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from books.serializers import BookSerializer
from borrowings.models import Borrowing
from borrowings.notifications import send_telegram_notification
from payments.models import Payment
from payments.serializers import PaymentSerializer


class BorrowingReadSerializer(serializers.ModelSerializer):
    book = BookSerializer(read_only=True)
    user = serializers.EmailField(source="user.email", read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "book",
            "user",
            "payments",
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
        user = self.context["request"].user

        has_pending_payments = Payment.objects.filter(
            borrowing__user=user, status=Payment.StatusChoices.PENDING
        ).exists()

        if has_pending_payments:
            raise ValidationError(
                "You cannot borrow new books because you have unpaid payments or fines. "
                "Please settle your pending balances first."
            )

        expected_date = attrs.get("expected_return_date")

        if expected_date:
            if expected_date < date.today():
                raise ValidationError(
                    {
                        "expected_return_date": "The expected return date cannot be in the past."
                    }
                )
        else:
            attrs["expected_return_date"] = date.today() + timedelta(days=14)

        book = attrs.get("book")
        if book.inventory <= 0:
            raise ValidationError(
                f"Sorry, '{book.title}' is currently out of stock."
            )

        return attrs

    def create(self, validated_data):
        with transaction.atomic():
            book = validated_data["book"]
            book.inventory -= 1
            book.save()

            borrowing = Borrowing.objects.create(**validated_data)

        notification_message = (
            f"🚀 *New Borrowing Created!*\n\n"
            f"• *User ID:* {borrowing.user.id}\n"
            f"• *Book:* '{book.title}' by {book.author}\n"
            f"• *Expected Return:* {borrowing.expected_return_date}"
        )
        send_telegram_notification(notification_message)

        return borrowing
