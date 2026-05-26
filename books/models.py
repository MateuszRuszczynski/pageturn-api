from django.core.validators import MinValueValidator
from django.db import models


class Book(models.Model):
    COVER_CHOICES = {
        "HARD": "Hardcover",
        "SOFT": "Softcover"
    }

    title = models.CharField(max_length=100)
    author = models.CharField(max_length=50)
    cover = models.CharField(max_length=4, choices=COVER_CHOICES)
    inventory = models.PositiveIntegerField(validators=[MinValueValidator(0)])
    daily_fee = models.DecimalField(
        max_digits=8, decimal_places=2, validators=[MinValueValidator(0.0)]
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(inventory__gte=0), name="book_inventory_gte_0"
            ),
            models.CheckConstraint(
                condition=models.Q(daily_fee__gte=0), name="book_daily_fee_gte_0"
            ),
        ]

    def __str__(self):
        return f"{self.title} by {self.author} ({self.cover})"
