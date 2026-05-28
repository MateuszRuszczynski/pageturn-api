import os
from datetime import date

import requests
from celery import shared_task

from borrowings.models import Borrowing

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def send_telegram_message(message: str) -> None:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Failed to send background alert to Telegram: {e}")


@shared_task
def check_overdue_borrowings():
    overdue_list = Borrowing.objects.filter(
        expected_return_date__lt=date.today(), actual_return_date__isnull=True
    ).select_related("user", "book")

    if not overdue_list.exists():
        send_telegram_message(
            "🔍 *Library Audit:* No overdue borrowings detected today!"
        )
        return

    body = ""
    for borrowing in overdue_list:
        overdue_days = (date.today() - borrowing.expected_return_date).days

        body += (
            f"⚠️ *OVERDUE BORROWINGS ALERT ({date.today()})*\n"
            f"The following users have exceeded their return deadlines:\n\n"
            f"👤 *User:* {borrowing.user.email}\n"
            f"📖 *Book:* _{borrowing.book.title}_\n"
            f"📅 *Deadline was:* {borrowing.expected_return_date}\n"
            f"🚨 *Overdue by:* `{overdue_days} days`\n"
        )

    send_telegram_message(body)
