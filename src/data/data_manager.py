"""Data manager for collecting and storing stock data."""

import pandas as pd
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from ..api import YahooFinanceClient
from .database import Database
from ..utils import log, settings


class DataManager:
    """Manager for collecting and storing stock data."""

    def __init__(self):
        """Initialize data manager."""
        self.client = YahooFinanceClient()
        self.db = Database()
        log.info("Data manager initialized")

    def fetch_and_store_data(
        self,
        symbols: List[str],
        period: Optional[str] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
        interval: str = "1d"
    ):
        """
        Fetch data from Yahoo Finance and store in database.

        Args:
            symbols: List of stock ticker symbols
            period: Data period
            start: Start date
            end: End date
            interval: Data interval
        """
        log.info(f"Fetching data for {len(symbols)} symbols")

        for symbol in symbols:
            try:
                # Fetch data
                data = self.client.get_historical_data(
                    symbol=symbol,
                    period=period,
                    start=start,
                    end=end,
                    interval=interval
                )

                if not data.empty:
                    # Store in database
                    self.db.save_stock_data(symbol, data)
                    log.info(f"Stored data for {symbol}")
                else:
                    log.warning(f"No data fetched for {symbol}")

            except Exception as e:
                log.error(f"Error processing {symbol}: {e}")

    def get_latest_data(
        self,
        symbol: str,
        days: int = 365
    ) -> pd.DataFrame:
        """
        Get latest data for a symbol from database or fetch if not available.

        Args:
            symbol: Stock ticker symbol
            days: Number of days to retrieve

        Returns:
            DataFrame with stock data
        """
        # Try to get from database first
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        df = self.db.get_stock_data(
            symbol,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )

        # If not enough data, fetch from API
        if df.empty or len(df) < days * 0.7:  # Allow 30% missing data tolerance
            log.info(f"Fetching fresh data for {symbol}")
            data = self.client.get_historical_data(
                symbol=symbol,
                period=f"{days}d",
                interval="1d"
            )

            if not data.empty:
                self.db.save_stock_data(symbol, data)
                df = data

        return df

    def update_all_symbols(self, symbols: Optional[List[str]] = None):
        """
        Update data for all tracked symbols.

        Args:
            symbols: List of symbols to update (uses default if None)
        """
        if symbols is None:
            symbols = settings.symbols_list

        log.info(f"Updating data for {len(symbols)} symbols")

        # Fetch latest data (last 7 days to catch up)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        self.fetch_and_store_data(
            symbols=symbols,
            start=start_date.strftime('%Y-%m-%d'),
            end=end_date.strftime('%Y-%m-%d'),
            interval="1d"
        )

    def get_current_prices(self, symbols: List[str]) -> Dict[str, float]:
        """
        Get current prices for multiple symbols.

        Args:
            symbols: List of stock ticker symbols

        Returns:
            Dictionary mapping symbols to current prices
        """
        prices = {}

        for symbol in symbols:
            price = self.client.get_current_price(symbol)
            if price is not None:
                prices[symbol] = price

        log.info(f"Retrieved current prices for {len(prices)} symbols")
        return prices

    def close(self):
        """Close database connection."""
        self.db.close()
