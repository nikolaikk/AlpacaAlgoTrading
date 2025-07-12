import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class TradingConfig:
    """
    Configuration class for the trading bot.
    Loads settings from environment variables.
    """
    # Trading mode: 'paper' or 'live'
    MODE = os.getenv('ALPACA_MODE', 'paper')

    # Alpaca API credentials
    API_KEY = os.getenv('ALPACA_API_KEY_ID_PAPER') if MODE == 'paper' else os.getenv('ALPACA_API_KEY_ID_LIVE')
    API_SECRET = os.getenv('ALPACA_API_SECRET_KEY_PAPER') if MODE == 'paper' else os.getenv('ALPACA_API_SECRET_KEY_LIVE')
    BASE_URL = 'https://paper-api.alpaca.markets' if MODE == 'paper' else 'https://api.alpaca.markets'

    # Notification service URLs
    TELEGRAM_URL = f"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN')}/sendMessage"
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

    # Risk Management: Percentage of portfolio to risk on a single trade
    RISK_PER_TRADE = 0.01  # Risk 1% of portfolio per trade
    
    # Strategy specific settings
    RSI_OVERSOLD_THRESHOLD = 30
    RSI_OVERBOUGHT_THRESHOLD = 70
    TAKE_PROFIT_PERCENTAGE = 5.0 # 5% take profit
    STOP_LOSS_PERCENTAGE = 2.0 # 2% stop loss

    def __init__(self):
        # Basic validation to ensure essential variables are set
        if not all([self.API_KEY, self.API_SECRET]):
            raise ValueError("API_KEY and API_SECRET must be set in the environment variables.")
        if not all([os.getenv('TELEGRAM_BOT_TOKEN'), self.TELEGRAM_CHAT_ID]):
            print("Warning: Telegram notification variables are not fully set.")

