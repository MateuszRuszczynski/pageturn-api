from django.db import models

from borrowings.models import Borrowing


class Payment(models.Model):
    class StatusChoices(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PAID = "PAID", "Paid"
        EXPIRED = "EXPIRED", "Expired"

    class TypeChoices(models.TextChoices):
        PAYMENT = "PAYMENT", "Payment"
        FINE = "FINE", "Fine"

    status = models.CharField(
        max_length=10,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING,
    )
    type = models.CharField(max_length=10, choices=TypeChoices.choices)
    borrowing = models.ForeignKey(
        Borrowing, on_delete=models.CASCADE, related_name="payments"
    )
    session_url = models.URLField(max_length=1024, null=True, blank=True)
    session_id = models.CharField(max_length=255, null=True, blank=True)
    money_to_pay = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        payment_id = self.id if self.id else "New"
        return f"Payment {payment_id}: {self.type} - {self.status} - {self.money_to_pay} USD"
