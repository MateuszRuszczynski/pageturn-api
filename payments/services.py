import os

import stripe
from django.urls import reverse

from payments.models import Payment

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


def create_stripe_checkout_session(payment: Payment, request) -> dict:
    success_url = (
        request.build_absolute_uri(reverse("api:payment-success"))
        + "?session_id={CHECKOUT_SESSION_ID}"
    )

    cancel_url = request.build_absolute_uri(reverse("api:payment-cancel"))

    amount_in_cents = int(payment.money_to_pay * 100)

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": f"Library {payment.get_type_display()} Fee",
                            "description": (
                                f"Payment for Borrowing ID: {payment.borrowing.id}"
                            ),
                        },
                        "unit_amount": amount_in_cents,
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={"payment_id": payment.id},
        )

        return {"session_url": session.url, "session_id": session.id}

    except stripe.error.StripeError as e:
        print(f"Stripe API Session Creation Failed: {e}")
        return {}
