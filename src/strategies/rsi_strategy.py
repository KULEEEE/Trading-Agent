"""RSI-based trading strategy."""

import pandas as pd
from .base_strategy import BaseStrategy
from ..indicators import TechnicalIndicators
from ..utils import log


class RSIStrategy(BaseStrategy):
    """RSI (Relative Strength Index) trading strategy."""

    def __init__(
        self,
        period: int = 14,
        oversold: int = 30,
        overbought: int = 70,
        stop_loss_pct: float = 0.05,
        take_profit_pct: float = 0.10
    ):
        """
        Initialize RSI strategy.

        Args:
            period: RSI period
            oversold: Oversold threshold (buy signal)
            overbought: Overbought threshold (sell signal)
            stop_loss_pct: Stop loss percentage
            take_profit_pct: Take profit percentage
        """
        super().__init__(f"RSI_{period}")
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate signals based on RSI.

        Args:
            df: DataFrame with price data

        Returns:
            DataFrame with signals added
        """
        # Add RSI if not present
        if f'RSI_{self.period}' not in df.columns:
            df = TechnicalIndicators.add_rsi(df, period=self.period)

        # Generate signals
        df['signal'] = 0

        rsi_col = f'RSI_{self.period}'

        # Buy signal: RSI crosses above oversold from below
        df.loc[
            (df[rsi_col] > self.oversold) &
            (df[rsi_col].shift(1) <= self.oversold),
            'signal'
        ] = 1

        # Sell signal: RSI crosses below overbought from above
        df.loc[
            (df[rsi_col] < self.overbought) &
            (df[rsi_col].shift(1) >= self.overbought),
            'signal'
        ] = -1

        log.debug(f"Generated {(df['signal'] != 0).sum()} RSI signals")
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

        rsi_col = f'RSI_{self.period}'

        # Ensure RSI column exists
        if rsi_col not in df.columns:
            df = self.generate_signals(df)

        # Buy when RSI crosses above oversold threshold
        if (df.loc[idx, rsi_col] > self.oversold and
            df.loc[prev_idx, rsi_col] <= self.oversold):
            log.debug(f"RSI buy signal: {df.loc[idx, rsi_col]:.2f}")
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

        # RSI overbought sell signal
        rsi_col = f'RSI_{self.period}'

        if rsi_col in df.columns:
            if (df.loc[idx, rsi_col] < self.overbought and
                df.loc[prev_idx, rsi_col] >= self.overbought):
                log.info(f"RSI sell signal: {df.loc[idx, rsi_col]:.2f}")
                return True

        return False
