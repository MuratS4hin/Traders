"""
Top 20 most valuable stocks (by market cap) and yfinance data fetching utilities.
"""

import yfinance as yf
import pandas as pd

TOP_20_TICKERS = [
    "AAPL",  # Apple
    "MSFT",  # Microsoft
    "NVDA",  # NVIDIA
    "GOOGL", # Alphabet
    "AMZN",  # Amazon
    "META",  # Meta Platforms
    "BRK-B", # Berkshire Hathaway
    "LLY",   # Eli Lilly
    "AVGO",  # Broadcom
    "TSLA",  # Tesla
    "WMT",   # Walmart
    "JPM",   # JPMorgan Chase
    "V",     # Visa
    "UNH",   # UnitedHealth
    "XOM",   # ExxonMobil
    "ORCL",  # Oracle
    "MA",    # Mastercard
    "COST",  # Costco
    "HD",    # Home Depot
    "PG",    # Procter & Gamble
]


def fetch_stock_data(ticker: str, period: str = "5d", interval: str = "1d") -> pd.DataFrame:
    """
    Fetch OHLCV data for a given ticker symbol.

    :param ticker: Stock ticker symbol (e.g. "AAPL")
    :param period: Data period to fetch (default "5d")
    :param interval: Data interval (default "1d")
    :return: DataFrame with columns [Open, High, Low, Close, Volume]
    """
    stock = yf.Ticker(ticker)
    df = stock.history(period=period, interval=interval)
    if df.empty:
        raise ValueError(f"No data returned for ticker '{ticker}'")
    return df


def get_latest_ohlc(ticker: str) -> dict:
    """
    Return the most recent OHLC values for a ticker.

    :param ticker: Stock ticker symbol
    :return: dict with keys open, high, low, close
    """
    df = fetch_stock_data(ticker, period="5d", interval="1d")
    latest = df.iloc[-1]
    return {
        "open": round(float(latest["Open"]), 4),
        "high": round(float(latest["High"]), 4),
        "low": round(float(latest["Low"]), 4),
        "close": round(float(latest["Close"]), 4),
    }
