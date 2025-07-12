import time
import sys
from src.config import TradingConfig
from src.data_fetcher import TradingOpportunities
from src.notifications import Notifier
from src.strategy import SimpleRSIStrategy
from src.trader import AlpacaTrader

def main():
    """
    Main function to initialize and run the trading bot.
    """
    print("--- Starting Trading Bot ---")

    try:
        # 1. Initialize Configuration
        config = TradingConfig()

        # 2. Initialize Services
        notifier = Notifier(config)
        strategy = SimpleRSIStrategy(config)
        trader = AlpacaTrader(config, strategy, notifier)
        data_fetcher = TradingOpportunities(n_stocks=50, n_crypto=50)

        # 3. Send startup notification
        notifier.send_telegram_message("🤖 **Trading Bot Started** 🤖\nMode: {}"
                                       .format(config.MODE.upper()))

        # --- Main Trading Logic ---
        # This example runs once. For a real bot, you would wrap this in a
        # scheduler (e.g., APScheduler) to run at regular intervals.
        
        # Step 1: Find potential assets
        opportunities_df = data_fetcher.find_opportunities()

        # Step 2: Get technical data for them
        enriched_df = data_fetcher.get_technical_indicators()

        # Step 3: Evaluate existing positions to see if any should be sold
        trader.evaluate_positions()
        
        # Step 4: Scan new opportunities and execute trades
        trader.run_scan(enriched_df)

    except (ValueError, Exception) as e:
        print(f"An unexpected error occurred: {e}")
        # Attempt to notify on critical failure
        try:
            config_for_notify = TradingConfig()
            notifier_for_notify = Notifier(config_for_notify)
            notifier_for_notify.send_telegram_message(f"🚨 **CRITICAL ERROR** 🚨\nBot shutting down. Error: {e}")
        except Exception as notify_e:
            print(f"Could not send failure notification: {notify_e}")
        sys.exit(1) # Exit with an error code
    finally:
        print("\n--- Trading Bot Run Finished ---")
        # Ensure notifier is initialized before trying to use it in finally block
        if 'notifier' in locals():
            notifier.send_telegram_message("🏁 **Trading Bot Run Finished** 🏁")


if __name__ == "__main__":
    main()
