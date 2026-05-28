from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from books.models import Book
from borrowings.models import Borrowing
from payments.models import Payment


class PaymentModelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="testuser@library.com", password="Password123!"
        )
        self.book = Book.objects.create(
            title="Test Title",
            author="Test Author",
            cover="HARD",
            inventory=5,
            daily_fee=Decimal("2.00"),
        )
        self.borrowing = Borrowing.objects.create(
            expected_return_date="2026-06-10",
            book=self.book,
            user=self.user,
        )

    def _create_payment(self, status, type, session_suffix, money):
        return Payment.objects.create(
            status=status,
            type=type,
            borrowing=self.borrowing,
            session_url=f"https://checkout.stripe.com/pay/{session_suffix}",
            session_id=f"cs_{session_suffix}",
            money_to_pay=Decimal(money),
        )

    def test_payment_str_representation(self):
        payment = self._create_payment(
            status=Payment.StatusChoices.PENDING,
            type=Payment.TypeChoices.PAYMENT,
            session_suffix="test_str",
            money="10.00",
        )

        expected_str = (
            f"Payment {payment.id}: {payment.type} - {payment.status} - "
            f"{payment.money_to_pay} USD"
        )
        self.assertEqual(str(payment), expected_str)

    def test_payment_fields_and_relations(self):
        payment = self._create_payment(
            status=Payment.StatusChoices.PAID,
            type=Payment.TypeChoices.FINE,
            session_suffix="test_fields",
            money="4.50",
        )

        self.assertEqual(payment.status, Payment.StatusChoices.PAID)
        self.assertEqual(payment.type, Payment.TypeChoices.FINE)
        self.assertEqual(payment.borrowing, self.borrowing)
        self.assertEqual(
            payment.session_url, "https://checkout.stripe.com/pay/test_fields"
        )
        self.assertEqual(payment.session_id, "cs_test_fields")
        self.assertEqual(payment.money_to_pay, Decimal("4.50"))
