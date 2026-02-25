"""Moving Average Crossover Strategy."""

import pandas as pd
from .base_strategy import BaseStrategy
from ..indicators import TechnicalIndicators
from ..utils import log


class MACrossoverStrategy(BaseStrategy):
    """Moving Average Crossover trading strategy."""

    def __init__(
        self,
        short_period: int = 20,
        long_period: int = 50,
        stop_loss_pct: float = 0.05,
        take_profit_pct: float = 0.15
    ):
        """
        Initialize MA Crossover strategy.

        Args:
            short_period: Short MA period
            long_period: Long MA period
            stop_loss_pct: Stop loss percentage
            take_profit_pct: Take profit percentage
        """
        super().__init__(f"MA_Crossover_{short_period}_{long_period}")
        self.short_period = short_period
        self.long_period = long_period
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate signals based on MA crossover.

        Args:
            df: DataFrame with price data

        Returns:
            DataFrame with signals added
        """
        # Add moving averages if not present
        if f'SMA_{self.short_period}' not in df.columns:
            df = TechnicalIndicators.add_sma(df, period=self.short_period)

        if f'SMA_{self.long_period}' not in df.columns:
            df = TechnicalIndicators.add_sma(df, period=self.long_period)

        # Generate signals
        df['signal'] = 0

        # Buy signal: short MA crosses above long MA
        df.loc[
            (df[f'SMA_{self.short_period}'] > df[f'SMA_{self.long_period}']) &
            (df[f'SMA_{self.short_period}'].shift(1) <= df[f'SMA_{self.long_period}'].shift(1)),
            'signal'
        ] = 1

        # Sell signal: short MA crosses below long MA
        df.loc[
            (df[f'SMA_{self.short_period}'] < df[f'SMA_{self.long_period}']) &
            (df[f'SMA_{self.short_period}'].shift(1) >= df[f'SMA_{self.long_period}'].shift(1)),
            'signal'
        ] = -1

        log.debug(f"Generated {(df['signal'] != 0).sum()} signals")
        return df

    def should_buy(self, df: pd.DataFrame, current_idx: int) -> bool:
        """
        Check if should buy at current index.

        Args:
            df: DataFrame with price data
            current_idx: Current index

        Returns:
            True if should buy
        """
        if not self.validate_signal(df, current_idx):
            return False

        idx = df.index[current_idx]
        prev_idx = df.index[current_idx - 1]

        short_ma = f'SMA_{self.short_period}'
        long_ma = f'SMA_{self.long_period}'

        # Ensure columns exist
        if short_ma not in df.columns or long_ma not in df.columns:
            df = self.generate_signals(df)

        # Buy when short MA crosses above long MA
        if (df.loc[idx, short_ma] > df.loc[idx, long_ma] and
            df.loc[prev_idx, short_ma] <= df.loc[prev_idx, long_ma]):
            return True

        return False

    def should_sell(self, df: pd.DataFrame, current_idx: int, entry_price: float) -> bool:
        """
        Check if should sell at current index.

        Args:
            df: DataFrame with price data
            current_idx: Current index
            entry_price: Entry price

        Returns:
            True if should sell
        """
        idx = df.index[current_idx]
        prev_idx = df.index[current_idx - 1] if current_idx > 0 else idx

        current_price = df.loc[idx, 'Close']

        # Stop loss check
        if current_price <= entry_price * (1 - self.stop_loss_pct):
            log.info(f"Stop loss triggered at {current_price:.2f}")
            return True

        # Take profit check
        if current_price >= entry_price * (1 + self.take_profit_pct):
            log.info(f"Take profit triggered at {current_price:.2f}")
            return True

        # Crossover sell signal
        short_ma = f'SMA_{self.short_period}'
        long_ma = f'SMA_{self.long_period}'

        if short_ma in df.columns and long_ma in df.columns:
            if (df.loc[idx, short_ma] < df.loc[idx, long_ma] and
                df.loc[prev_idx, short_ma] >= df.loc[prev_idx, long_ma]):
                log.info("MA crossover sell signal")
                return True

        return False
