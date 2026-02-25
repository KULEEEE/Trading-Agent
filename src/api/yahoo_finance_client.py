"""Yahoo Finance API client for fetching stock data."""

import yfinance as yf
import pandas as pd
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from ..utils import log


class YahooFinanceClient:
    """Client for interacting with Yahoo Finance API."""

    def __init__(self):
        """Initialize Yahoo Finance client."""
        log.info("Yahoo Finance client initialized")

    def get_historical_data(
        self,
        symbol: str,
        period: Optional[str] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
        interval: str = "1d"
    ) -> pd.DataFrame:
        """
        Fetch historical stock data.

        Args:
            symbol: Stock ticker symbol
            period: Data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            start: Start date (YYYY-MM-DD)
            end: End date (YYYY-MM-DD)
            interval: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)

        Returns:
            DataFrame with OHLCV data
        """
        try:
            ticker = yf.Ticker(symbol)

            if period:
                data = ticker.history(period=period, interval=interval)
            elif start and end:
                data = ticker.history(start=start, end=end, interval=interval)
            else:
                # Default to 1 year
                data = ticker.history(period="1y", interval=interval)

            if data.empty:
                log.warning(f"No data found for {symbol}")
                return pd.DataFrame()

            log.info(f"Fetched {len(data)} rows of data for {symbol}")
            return data

        except Exception as e:
            log.error(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()

    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        Get current stock price.

        Args:
            symbol: Stock ticker symbol

        Returns:
            Current price or None if error
        """
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1d", interval="1m")

            if data.empty:
                log.warning(f"No current price data for {symbol}")
                return None

            current_price = data['Close'].iloc[-1]
            log.debug(f"Current price for {symbol}: ${current_price:.2f}")
            return float(current_price)

        except Exception as e:
            log.error(f"Error fetching current price for {symbol}: {e}")
            return None

    def get_stock_info(self, symbol: str) -> Dict:
        """
        Get detailed stock information.

        Args:
            symbol: Stock ticker symbol

        Returns:
            Dictionary with stock information
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            log.debug(f"Fetched info for {symbol}")
            return info

        except Exception as e:
            log.error(f"Error fetching info for {symbol}: {e}")
            return {}

    def get_multiple_tickers(
        self,
        symbols: List[str],
        period: str = "1y",
        interval: str = "1d"
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch historical data for multiple tickers.

        Args:
            symbols: List of stock ticker symbols
            period: Data period
            interval: Data interval

        Returns:
            Dictionary mapping symbols to DataFrames
        """
        result = {}

        for symbol in symbols:
            data = self.get_historical_data(
                symbol=symbol,
                period=period,
                interval=interval
            )
            if not data.empty:
                result[symbol] = data

        log.info(f"Fetched data for {len(result)}/{len(symbols)} symbols")
        return result

    def get_dividends(self, symbol: str) -> pd.Series:
        """
        Get dividend history.

        Args:
            symbol: Stock ticker symbol

        Returns:
            Series with dividend data
        """
        try:
            ticker = yf.Ticker(symbol)
            dividends = ticker.dividends
            log.debug(f"Fetched {len(dividends)} dividends for {symbol}")
            return dividends

        except Exception as e:
            log.error(f"Error fetching dividends for {symbol}: {e}")
            return pd.Series()

    def get_splits(self, symbol: str) -> pd.Series:
        """
        Get stock split history.

        Args:
            symbol: Stock ticker symbol

        Returns:
            Series with stock split data
        """
        try:
            ticker = yf.Ticker(symbol)
            splits = ticker.splits
            log.debug(f"Fetched {len(splits)} splits for {symbol}")
            return splits

        except Exception as e:
            log.error(f"Error fetching splits for {symbol}: {e}")
            return pd.Series()
