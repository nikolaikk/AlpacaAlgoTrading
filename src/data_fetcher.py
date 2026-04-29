import pandas as pd
import yfinance as yf
from tqdm import tqdm
from ta.trend import sma_indicator
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands

class TradingOpportunities:
    """
    Uses the yfinance Screener to find potential trading opportunities among stocks and crypto.
    Also fetches technical analysis indicators for a list of assets.
    """
    def __init__(self, n_stocks=25, n_crypto=25):
        self.n_stocks = n_stocks
        self.n_crypto = n_crypto
        self.all_tickers = []
        self.opportunities_df = pd.DataFrame()

    @staticmethod
    def _screener_to_df(predefined_id, size, asset_type, alpaca_symbol_fn):
        """Fetches a Yahoo Finance predefined screener and returns a minimal DataFrame."""
        screener = yf.Screener()
        screener.set_predefined_body(predefined_id)
        screener.size = size
        quotes = screener.response.get("quotes", [])
        if not quotes:
            return pd.DataFrame()
        df = pd.DataFrame(quotes)
        # yfinance returns lowercase 'symbol'
        if "symbol" in df.columns:
            df = df.rename(columns={"symbol": "Symbol"})
        df = df[["Symbol"]].head(size).copy()
        df["asset_type"] = asset_type
        df["alpaca_symbol"] = df["Symbol"].apply(alpaca_symbol_fn)
        return df

    def find_opportunities(self):
        """
        Fetches top crypto and losing stocks from Yahoo Finance to identify opportunities.
        Uses yfinance Screener (no browser/Chromium required).
        """
        print("Finding trading opportunities...")
        dfs = []

        # --- Crypto (top by market cap) ---
        try:
            df_crypto = self._screener_to_df(
                predefined_id="all_cryptocurrencies_us",
                size=self.n_crypto,
                asset_type="crypto",
                # BTC-USD -> BTC/USD  (replace hyphen, no extra suffix needed)
                alpaca_symbol_fn=lambda s: s.replace("-", "/"),
            )
            if not df_crypto.empty:
                dfs.append(df_crypto)
        except Exception as e:
            print(f"Could not fetch crypto data: {e}")

        # --- Stocks (Top Losers) ---
        try:
            df_stock = self._screener_to_df(
                predefined_id="day_losers",
                size=self.n_stocks,
                asset_type="stock",
                alpaca_symbol_fn=lambda s: s,
            )
            if not df_stock.empty:
                dfs.append(df_stock)
        except Exception as e:
            print(f"Could not fetch stock data: {e}")

        if not dfs:
            print("No opportunities found.")
            return self.opportunities_df

        self.opportunities_df = pd.concat(dfs, axis=0).reset_index(drop=True)
        self.all_tickers = self.opportunities_df["Symbol"].tolist()
        print(f"Found {len(self.opportunities_df)} potential opportunities.")
        return self.opportunities_df

    def get_technical_indicators(self):
        """
        Fetches historical data and calculates technical indicators for the found opportunities.
        """
        if self.opportunities_df.empty:
            print("No opportunities found to fetch technical data for.")
            return pd.DataFrame()

        print(f"Grabbing technical metrics for {len(self.all_tickers)} assets...")
        df_tech_list = []
        
        # Use yfinance's download for efficiency
        data = yf.download(self.all_tickers, period="1y", interval="1d", group_by='ticker', auto_adjust=True)

        for symbol in tqdm(self.all_tickers, desc="Calculating Indicators"):
            try:
                hist = data[symbol].copy() if len(self.all_tickers) > 1 else data
                if hist.empty or 'Close' not in hist.columns:
                    # print(f"Warning: No data or 'Close' column for {symbol}. Skipping.")
                    continue

                # Calculate indicators
                for n in [14, 50]: # Using fewer indicators for simplicity
                    hist[f"ma{n}"] = sma_indicator(close=hist["Close"], window=n, fillna=False)
                    hist[f"rsi{n}"] = RSIIndicator(close=hist["Close"], window=n).rsi()
                
                # Bollinger Bands
                bb = BollingerBands(close=hist["Close"], window=20, window_dev=2)
                hist["bb_high"] = bb.bollinger_hband()
                hist["bb_low"] = bb.bollinger_lband()

                df_tech_temp = hist.tail(1).copy()
                df_tech_temp["Symbol"] = symbol
                df_tech_list.append(df_tech_temp)

            except Exception as e:
                # print(f"Could not process {symbol}: {e}")
                pass
        
        if not df_tech_list:
            return pd.DataFrame()

        df_tech = pd.concat(df_tech_list).reset_index()
        # Merge technicals back with the original opportunities dataframe
        self.opportunities_df = self.opportunities_df.merge(df_tech, on="Symbol", how="left")
        
        print(f"Successfully enriched {self.opportunities_df['rsi14'].notna().sum()} assets with technical data.")
        return self.opportunities_df
