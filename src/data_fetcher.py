import pandas as pd
import yfinance as yf
from tqdm import tqdm
from ta.trend import sma_indicator
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands
from requests_html import HTMLSession
from src.config import TradingConfig

class TradingOpportunities:
    """
    Scrapes Yahoo Finance to find potential trading opportunities among stocks and crypto.
    Also fetches technical analysis indicators for a list of assets.
    """
    def __init__(self, n_stocks=25, n_crypto=25):
        self.n_stocks = n_stocks
        self.n_crypto = n_crypto
        self.all_tickers = []
        self.opportunities_df = pd.DataFrame()

    @staticmethod
    def _raw_get_daily_info(site):
        """Helper method to scrape a table from a given URL."""
        session = HTMLSession()
        try:
            response = session.get(site)
            response.raise_for_status()  # Raise an exception for bad status codes
            tables = pd.read_html(response.html.raw_html)
            df = tables[0].copy()
            df.columns = tables[0].columns
            df = df.drop(columns=df.columns[df.isna().all()])
            df = df.loc[~df.isna().all(axis=1)]
            return df
        finally:
            session.close()

    def find_opportunities(self):
        """
        Fetches top crypto and losing stocks from Yahoo Finance to identify opportunities.
        """
        print("Finding trading opportunities...")
        # --- Crypto ---
        df_crypto_list = []
        # Yahoo finance shows 100 per page, so we only need one loop for n_crypto <= 100
        try:
            df_crypto_page = self._raw_get_daily_info(
                "https://finance.yahoo.com/crypto/?count=100&offset=0"
            )
            df_crypto_page["asset_type"] = "crypto"
            # Map symbol for Alpaca API (e.g., BTC-USD -> BTC/USD)
            df_crypto_page["alpaca_symbol"] = df_crypto_page["Symbol"].str.replace("-", "/") + "USD"
            df_crypto_list.append(df_crypto_page)
        except Exception as e:
            print(f"Could not fetch crypto data: {e}")

        df_crypto = pd.concat(df_crypto_list, axis=0).reset_index(drop=True).head(self.n_crypto)

        # --- Stocks (Top Losers) ---
        df_stock_list = []
        try:
            df_stock_page = self._raw_get_daily_info(
                "https://finance.yahoo.com/losers?offset=0&count=100"
            )
            df_stock_page["asset_type"] = "stock"
            df_stock_page["alpaca_symbol"] = df_stock_page["Symbol"]
            df_stock_list.append(df_stock_page)
        except Exception as e:
            print(f"Could not fetch stock data: {e}")

        df_stock = pd.concat(df_stock_list, axis=0).reset_index(drop=True).head(self.n_stocks)

        self.opportunities_df = pd.concat([df_crypto, df_stock], axis=0).reset_index(drop=True)
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
        data = yf.download(self.all_tickers, period="1y", interval="1d", group_by='ticker', auto_adjust=True, threads=True)

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
