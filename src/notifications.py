import requests
from src.config import TradingConfig

class Notifier:
    """
    Handles sending notifications to external services like Telegram.
    """
    def __init__(self, config: TradingConfig):
        self.config = config

    def send_telegram_message(self, message: str):
        """
        Sends a message to the configured Telegram channel.

        Args:
            message (str): The message content to send.
        """
        if not self.config.TELEGRAM_URL or not self.config.TELEGRAM_CHAT_ID or "YOUR_TELEGRAM" in self.config.TELEGRAM_URL:
            # print(f"Telegram not configured. Message not sent: {message}")
            return

        payload = {
            'chat_id': self.config.TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'
        }
        try:
            response = requests.post(self.config.TELEGRAM_URL, data=payload, timeout=10)
            response.raise_for_status()
            print("Telegram notification sent successfully.")
        except requests.exceptions.RequestException as e:
            print(f"Error sending Telegram notification: {e}")
