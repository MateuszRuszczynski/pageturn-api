from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from books.models import Book
from borrowings.models import Borrowing
from payments.models import Payment
from payments.serializers import PaymentSerializer
from rest_framework.test import APIRequestFactory


class PaymentSerializerTests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="patron@library.com", password="SecurePassword123!"
        )
        self.book = Book.objects.create(
            title="Dune",
            author="Frank Herbert",
            cover="SOFT",
            inventory=2,
            daily_fee=Decimal("3.00"),
        )
        self.borrowing = Borrowing.objects.create(
            expected_return_date="2026-06-05",
            book=self.book,
            user=self.user,
        )
        self.payment = Payment.objects.create(
            status=Payment.StatusChoices.PENDING,
            type=Payment.TypeChoices.PAYMENT,
            borrowing=self.borrowing,
            session_url="https://checkout.stripe.com/pay/session_123",
            session_id="cs_test_123",
            money_to_pay=Decimal("15.00"),
        )

    def _get_serializer_context(self):
        factory = APIRequestFactory()
        request = factory.get("/api/payments/")
        request.user = self.user
        return {"request": request}

    def test_payment_serializer_outputs_correct_data(self):
        context = self._get_serializer_context()
        serializer = PaymentSerializer(self.payment, context=context)

        self.assertEqual(serializer.data["id"], self.payment.id)
        self.assertEqual(serializer.data["status"], "PENDING")
        self.assertEqual(serializer.data["type"], "PAYMENT")
        self.assertEqual(serializer.data["borrowing"], self.borrowing.id)
        self.assertEqual(
            serializer.data["session_url"],
            "https://checkout.stripe.com/pay/session_123",
        )
        self.assertEqual(serializer.data["session_id"], "cs_test_123")
        self.assertEqual(serializer.data["money_to_pay"], "15.00")

    def test_payment_serializer_read_only_fields(self):
        context = self._get_serializer_context()
        payload = {
            "status": "PAID",
            "money_to_pay": "500.00",
        }

        serializer = PaymentSerializer(
            instance=self.payment, data=payload, context=context, partial=True
        )

        self.assertTrue(serializer.is_valid())
        serializer.save()

        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.StatusChoices.PENDING)
        self.assertEqual(self.payment.money_to_pay, Decimal("15.00"))
