"""Base strategy class for trading strategies."""

from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, Optional, Tuple
from ..utils import log


class BaseStrategy(ABC):
    """Abstract base class for trading strategies."""

    def __init__(self, name: str):
        """
        Initialize strategy.

        Args:
            name: Strategy name
        """
        self.name = name
        log.info(f"Initialized strategy: {name}")

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals based on strategy logic.

        Args:
            df: DataFrame with price data and indicators

        Returns:
            DataFrame with signal column added (1=buy, -1=sell, 0=hold)
        """
        pass

    @abstractmethod
    def should_buy(self, df: pd.DataFrame, current_idx: int) -> bool:
        """
        Determine if should buy at current index.

        Args:
            df: DataFrame with price data and indicators
            current_idx: Current index position

        Returns:
            True if should buy, False otherwise
        """
        pass

    @abstractmethod
    def should_sell(self, df: pd.DataFrame, current_idx: int, entry_price: float) -> bool:
        """
        Determine if should sell at current index.

        Args:
            df: DataFrame with price data and indicators
            current_idx: Current index position
            entry_price: Entry price of position

        Returns:
            True if should sell, False otherwise
        """
        pass

    def get_position_size(
        self,
        capital: float,
        price: float,
        risk_per_trade: float = 0.02
    ) -> int:
        """
        Calculate position size based on capital and risk.

        Args:
            capital: Available capital
            price: Current price
            risk_per_trade: Risk per trade as fraction of capital

        Returns:
            Number of shares to buy
        """
        max_investment = capital * risk_per_trade
        shares = int(max_investment / price)
        return max(shares, 0)

    def validate_signal(self, df: pd.DataFrame, idx: int) -> bool:
        """
        Validate signal before execution.

        Args:
            df: DataFrame with price data
            idx: Current index

        Returns:
            True if signal is valid
        """
        # Basic validation - ensure we have enough data
        if idx < 50:  # Need at least 50 bars for most indicators
            return False

        # Ensure price data is valid
        if pd.isna(df.loc[df.index[idx], 'Close']):
            return False

        return True

    def __str__(self):
        """String representation of strategy."""
        return f"Strategy: {self.name}"
