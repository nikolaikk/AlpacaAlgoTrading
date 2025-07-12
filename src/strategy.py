import pandas as pd
from enum import Enum
from src.config import TradingConfig

class Action(Enum):
    """Enumeration for trading actions."""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

class BaseStrategy:
    """
    Abstract base class for a trading strategy.
    Ensures that any new strategy implements the 'decide_action' method.
    """
    def __init__(self, config: TradingConfig):
        self.config = config

    def decide_action(self, asset_data: pd.Series, existing_position=None) -> Action:
        """
        Makes a trading decision for a single asset.

        Args:
            asset_data (pd.Series): A row of data for one asset, including technical indicators.
            existing_position: An Alpaca position object if one exists for this asset.

        Returns:
            Action: The decision (BUY, SELL, or HOLD).
        """
        raise NotImplementedError("This method should be implemented by subclasses.")


class SimpleRSIStrategy(BaseStrategy):
    """
    A simple trading strategy based on RSI.
    - BUY when RSI is oversold.
    - SELL when a take profit/stop loss is hit or RSI is overbought.
    """
    def decide_action(self, asset_data: pd.Series, existing_position=None) -> Action:
        """
        Implements the simple RSI strategy.
        """
        try:
            rsi_14 = asset_data['rsi14']
            current_price = asset_data['Close']

            # --- SELL LOGIC ---
            if existing_position:
                entry_price = float(existing_position.avg_entry_price)
                
                # Take Profit
                if current_price >= entry_price * (1 + self.config.TAKE_PROFIT_PERCENTAGE / 100):
                    print(f"{asset_data['Symbol']}: TAKE PROFIT triggered.")
                    return Action.SELL
                
                # Stop Loss
                if current_price <= entry_price * (1 - self.config.STOP_LOSS_PERCENTAGE / 100):
                    print(f"{asset_data['Symbol']}: STOP LOSS triggered.")
                    return Action.SELL
                
                # RSI Overbought
                if rsi_14 > self.config.RSI_OVERBOUGHT_THRESHOLD:
                    print(f"{asset_data['Symbol']}: RSI OVERBOUGHT triggered.")
                    return Action.SELL

            # --- BUY LOGIC ---
            else: # No existing position, so only consider buying
                if rsi_14 < self.config.RSI_OVERSOLD_THRESHOLD:
                    print(f"{asset_data['Symbol']}: RSI OVERSOLD triggered.")
                    return Action.BUY

            # --- HOLD LOGIC ---
            return Action.HOLD

        except (KeyError, TypeError):
            # This can happen if technical indicator data is missing for an asset
            return Action.HOLD
