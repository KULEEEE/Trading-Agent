"""Database management for storing stock data."""

import sqlite3
import pandas as pd
from pathlib import Path
from typing import Optional, List
from datetime import datetime
from ..utils import log, settings


class Database:
    """SQLite database manager for stock data."""

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize database connection.

        Args:
            db_path: Path to database file
        """
        self.db_path = db_path or settings.db_path
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
        self._connect()
        self._create_tables()

    def _connect(self):
        """Establish database connection."""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            log.info(f"Connected to database: {self.db_path}")
        except Exception as e:
            log.error(f"Error connecting to database: {e}")
            raise

    def _create_tables(self):
        """Create necessary tables if they don't exist."""
        try:
            cursor = self.conn.cursor()

            # Stock price data table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stock_prices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    date TIMESTAMP NOT NULL,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume INTEGER,
                    dividends REAL,
                    stock_splits REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(symbol, date)
                )
            """)

            # Trades table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    trade_type TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    price REAL NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    strategy TEXT,
                    pnl REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Portfolio positions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS positions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL UNIQUE,
                    quantity INTEGER NOT NULL,
                    avg_price REAL NOT NULL,
                    current_price REAL,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Performance metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TIMESTAMP NOT NULL,
                    total_value REAL,
                    cash REAL,
                    positions_value REAL,
                    daily_return REAL,
                    cumulative_return REAL,
                    sharpe_ratio REAL,
                    max_drawdown REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            self.conn.commit()
            log.info("Database tables created/verified")

        except Exception as e:
            log.error(f"Error creating tables: {e}")
            raise

    def save_stock_data(self, symbol: str, data: pd.DataFrame):
        """
        Save stock price data to database.

        Args:
            symbol: Stock ticker symbol
            data: DataFrame with OHLCV data
        """
        try:
            if data.empty:
                log.warning(f"No data to save for {symbol}")
                return

            # Prepare data
            df = data.copy()
            df['symbol'] = symbol
            df['date'] = df.index.tz_localize(None) if df.index.tz else df.index

            # Select columns
            columns = ['symbol', 'date', 'Open', 'High', 'Low', 'Close', 'Volume']

            # Add optional columns if they exist
            if 'Dividends' in df.columns:
                columns.append('Dividends')
            if 'Stock Splits' in df.columns:
                columns.append('Stock Splits')

            df = df[columns]

            # Rename columns to match database schema
            df.columns = [col.lower().replace(' ', '_') for col in df.columns]

            # Delete existing data for this symbol/date range to avoid duplicates
            if not df.empty:
                min_date = str(df['date'].min())[:10]
                max_date = str(df['date'].max())[:10]
                cursor = self.conn.cursor()
                cursor.execute(
                    "DELETE FROM stock_prices WHERE symbol = ? AND date(date) BETWEEN ? AND ?",
                    (symbol, min_date, max_date)
                )
                self.conn.commit()

            # Save to database
            df.to_sql('stock_prices', self.conn, if_exists='append', index=False)

            log.info(f"Saved {len(df)} rows for {symbol}")

        except Exception as e:
            log.error(f"Error saving data for {symbol}: {e}")

    def get_stock_data(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Retrieve stock price data from database.

        Args:
            symbol: Stock ticker symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            DataFrame with stock data
        """
        try:
            query = "SELECT * FROM stock_prices WHERE symbol = ?"
            params = [symbol]

            if start_date:
                query += " AND date >= ?"
                params.append(start_date)

            if end_date:
                query += " AND date <= ?"
                params.append(end_date)

            query += " ORDER BY date"

            df = pd.read_sql_query(query, self.conn, params=params)

            if not df.empty:
                df['date'] = pd.to_datetime(df['date'], utc=True).dt.tz_localize(None)
                df.set_index('date', inplace=True)

            log.debug(f"Retrieved {len(df)} rows for {symbol}")
            return df

        except Exception as e:
            log.error(f"Error retrieving data for {symbol}: {e}")
            return pd.DataFrame()

    def save_trade(
        self,
        symbol: str,
        trade_type: str,
        quantity: int,
        price: float,
        timestamp: datetime,
        strategy: Optional[str] = None,
        pnl: Optional[float] = None
    ):
        """
        Save trade to database.

        Args:
            symbol: Stock ticker symbol
            trade_type: 'BUY' or 'SELL'
            quantity: Number of shares
            price: Trade price
            timestamp: Trade timestamp
            strategy: Strategy name
            pnl: Profit/loss
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO trades (symbol, trade_type, quantity, price, timestamp, strategy, pnl)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (symbol, trade_type, quantity, price, timestamp, strategy, pnl))

            self.conn.commit()
            log.info(f"Saved {trade_type} trade: {quantity} {symbol} @ ${price:.2f}")

        except Exception as e:
            log.error(f"Error saving trade: {e}")

    def get_trades(
        self,
        symbol: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Retrieve trades from database.

        Args:
            symbol: Optional symbol filter
            start_date: Optional start date
            end_date: Optional end date

        Returns:
            DataFrame with trades
        """
        try:
            query = "SELECT * FROM trades WHERE 1=1"
            params = []

            if symbol:
                query += " AND symbol = ?"
                params.append(symbol)

            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date)

            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date)

            query += " ORDER BY timestamp"

            df = pd.read_sql_query(query, self.conn, params=params)
            log.debug(f"Retrieved {len(df)} trades")
            return df

        except Exception as e:
            log.error(f"Error retrieving trades: {e}")
            return pd.DataFrame()

    def update_position(
        self,
        symbol: str,
        quantity: int,
        avg_price: float,
        current_price: Optional[float] = None
    ):
        """
        Update or insert position.

        Args:
            symbol: Stock ticker symbol
            quantity: Number of shares
            avg_price: Average purchase price
            current_price: Current market price
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO positions (symbol, quantity, avg_price, current_price, last_updated)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(symbol) DO UPDATE SET
                    quantity = excluded.quantity,
                    avg_price = excluded.avg_price,
                    current_price = excluded.current_price,
                    last_updated = excluded.last_updated
            """, (symbol, quantity, avg_price, current_price, datetime.now()))

            self.conn.commit()
            log.debug(f"Updated position for {symbol}: {quantity} shares @ ${avg_price:.2f}")

        except Exception as e:
            log.error(f"Error updating position for {symbol}: {e}")

    def get_positions(self) -> pd.DataFrame:
        """
        Get all current positions.

        Returns:
            DataFrame with positions
        """
        try:
            df = pd.read_sql_query("SELECT * FROM positions WHERE quantity > 0", self.conn)
            log.debug(f"Retrieved {len(df)} positions")
            return df

        except Exception as e:
            log.error(f"Error retrieving positions: {e}")
            return pd.DataFrame()

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            log.info("Database connection closed")
