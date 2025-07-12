import alpaca_trade_api as tradeapi
from alpaca_trade_api.rest import APIError
from src.config import TradingConfig
from src.notifications import Notifier
from src.strategy import BaseStrategy, Action
import pandas as pd

class AlpacaTrader:
    """
    The main trader class that connects to Alpaca, manages trades,
    and executes decisions based on a given strategy.
    """
    def __init__(self, config: TradingConfig, strategy: BaseStrategy, notifier: Notifier):
        self.config = config
        self.strategy = strategy
        self.notifier = notifier
        self.api = tradeapi.REST(
            key_id=self.config.API_KEY,
            secret_key=self.config.API_SECRET,
            base_url=self.config.BASE_URL,
            api_version='v2'
        )
        self.account_info = None
        self.positions = {}
        self._update_account_and_positions()

    def _update_account_and_positions(self):
        """Fetches the latest account info and open positions from Alpaca."""
        try:
            self.account_info = self.api.get_account()
            print(f"Account Status: {self.account_info.status}, Buying Power: {self.account_info.buying_power}")
            
            # Update positions, keyed by symbol
            positions_list = self.api.list_positions()
            self.positions = {pos.symbol: pos for pos in positions_list}
            print(f"Currently holding {len(self.positions)} positions.")

        except APIError as e:
            print(f"Error updating account info from Alpaca: {e}")
            self.notifier.send_telegram_message(f"🚨 **CRITICAL ERROR** 🚨\nCould not connect to Alpaca API: {e}")
            raise

    def submit_order(self, symbol: str, qty: float, side: str):
        """
        Submits a market order to Alpaca and sends a notification.

        Args:
            symbol (str): The symbol of the asset to trade.
            qty (float): The quantity to trade.
            side (str): 'buy' or 'sell'.
        """
        print(f"Attempting to submit {side} order for {qty} of {symbol}.")
        try:
            order = self.api.submit_order(
                symbol=symbol,
                qty=qty,
                side=side,
                type='market',
                time_in_force='day' # 'day' is often safer for market orders
            )
            message = f"✅ **{side.upper()} ORDER SUBMITTED** ✅\nSymbol: {symbol}\nQuantity: {qty}"
            self.notifier.send_telegram_message(message)
            print(message)
            return order
        except APIError as e:
            print(f"Error submitting {side} order for {symbol}: {e}")
            error_message = f"⚠️ **ORDER FAILED** ⚠️\nSymbol: {symbol}\nSide: {side}\nError: {e}"
            self.notifier.send_telegram_message(error_message)
            return None

    def evaluate_positions(self):
        """
        This method is conceptually useful but its logic is integrated into run_scan
        to avoid redundant data fetching. It ensures every held position is evaluated
        against the latest market data during the main scan.
        """
        print("\n--- Evaluating Existing Positions (as part of main scan) ---")
        if not self.positions:
            print("No open positions to evaluate.")
        else:
            print(f"{len(self.positions)} positions will be checked against the strategy.")


    def run_scan(self, opportunities_df: pd.DataFrame):
        """
        The main trading logic loop. It iterates through potential opportunities
        and existing positions, applies the strategy, and executes trades.
        """
        if opportunities_df.empty:
            print("No opportunities to scan.")
            return
            
        self._update_account_and_positions()
        buying_power = float(self.account_info.buying_power)
        
        # Combine opportunities with existing positions to evaluate all in one loop
        all_symbols_to_check = set(opportunities_df['alpaca_symbol'].unique()) | set(self.positions.keys())
        
        print(f"\n--- Scanning {len(all_symbols_to_check)} total symbols (Opportunities + Positions) ---")
        
        for symbol in all_symbols_to_check:
            # Get the asset data from the opportunities dataframe
            asset_data_row = opportunities_df[opportunities_df['alpaca_symbol'] == symbol]
            
            if asset_data_row.empty:
                # This happens for positions we hold that are not in today's "opportunity" list.
                # A robust implementation would fetch fresh data for this specific symbol.
                # For this version, we'll skip it to keep it simple.
                # print(f"No fresh data for held position {symbol}, skipping evaluation.")
                continue

            asset_data = asset_data_row.iloc[0]
            current_price = asset_data.get('Close')
            
            if pd.isna(current_price) or pd.isna(asset_data.get('rsi14')):
                continue

            existing_position = self.positions.get(symbol)
            action = self.strategy.decide_action(asset_data, existing_position)

            if action == Action.BUY and not existing_position:
                # Calculate position size based on risk
                trade_risk_amount = float(self.account_info.portfolio_value) * self.config.RISK_PER_TRADE
                qty_to_buy = trade_risk_amount / current_price
                
                # Ensure we don't try to buy more than we can afford
                if buying_power < (qty_to_buy * current_price):
                    print(f"Skipping BUY for {symbol}: Insufficient buying power.")
                    continue

                # For crypto, Alpaca may have notional size minimums (e.g., $1)
                if "USD" in symbol and (qty_to_buy * current_price < 1.0):
                    qty_to_buy = 1.0 / current_price # Adjust to $1 notional
                
                print(f"Decision: {action} {symbol}")
                self.submit_order(symbol=symbol, qty=round(qty_to_buy, 5), side='buy')
                buying_power -= (qty_to_buy * current_price)

            elif action == Action.SELL and existing_position:
                print(f"Decision: {action} {symbol}")
                qty_to_sell = float(existing_position.qty)
                self.submit_order(symbol=symbol, qty=qty_to_sell, side='sell')
