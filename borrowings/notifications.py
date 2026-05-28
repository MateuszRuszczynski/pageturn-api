import logging
import os

import requests

logger = logging.getLogger(__name__)


def send_telegram_notification(message: str) -> None:
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        logger.warning(
            "Telegram notification skipped: TELEGRAM_BOT_TOKEN"
            "or TELEGRAM_CHAT_ID not configured."
        )
        return

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Failed to send Telegram notification: {str(e)}")
