"""Technical indicators calculation using pandas_ta."""

import pandas as pd
import pandas_ta as ta
import numpy as np
from typing import Optional
from ..utils import log


class TechnicalIndicators:
    """Calculate various technical indicators for stock data."""

    @staticmethod
    def add_sma(df: pd.DataFrame, period: int = 20, column: str = 'Close') -> pd.DataFrame:
        """
        Add Simple Moving Average.

        Args:
            df: DataFrame with OHLCV data
            period: SMA period
            column: Column to calculate SMA on

        Returns:
            DataFrame with SMA column added
        """
        df[f'SMA_{period}'] = ta.sma(df[column], length=period)
        return df

    @staticmethod
    def add_ema(df: pd.DataFrame, period: int = 20, column: str = 'Close') -> pd.DataFrame:
        """
        Add Exponential Moving Average.

        Args:
            df: DataFrame with OHLCV data
            period: EMA period
            column: Column to calculate EMA on

        Returns:
            DataFrame with EMA column added
        """
        df[f'EMA_{period}'] = ta.ema(df[column], length=period)
        return df

    @staticmethod
    def add_rsi(df: pd.DataFrame, period: int = 14, column: str = 'Close') -> pd.DataFrame:
        """
        Add Relative Strength Index.

        Args:
            df: DataFrame with OHLCV data
            period: RSI period
            column: Column to calculate RSI on

        Returns:
            DataFrame with RSI column added
        """
        df[f'RSI_{period}'] = ta.rsi(df[column], length=period)
        return df

    @staticmethod
    def add_macd(
        df: pd.DataFrame,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9,
        column: str = 'Close'
    ) -> pd.DataFrame:
        """
        Add MACD (Moving Average Convergence Divergence).

        Args:
            df: DataFrame with OHLCV data
            fast: Fast EMA period
            slow: Slow EMA period
            signal: Signal line period
            column: Column to calculate MACD on

        Returns:
            DataFrame with MACD columns added
        """
        macd = ta.macd(df[column], fast=fast, slow=slow, signal=signal)
        df[f'MACD_{fast}_{slow}_{signal}'] = macd[f'MACD_{fast}_{slow}_{signal}']
        df[f'MACDh_{fast}_{slow}_{signal}'] = macd[f'MACDh_{fast}_{slow}_{signal}']
        df[f'MACDs_{fast}_{slow}_{signal}'] = macd[f'MACDs_{fast}_{slow}_{signal}']
        return df

    @staticmethod
    def add_bollinger_bands(
        df: pd.DataFrame,
        period: int = 20,
        std: float = 2.0,
        column: str = 'Close'
    ) -> pd.DataFrame:
        """
        Add Bollinger Bands.

        Args:
            df: DataFrame with OHLCV data
            period: Period for moving average
            std: Number of standard deviations
            column: Column to calculate on

        Returns:
            DataFrame with Bollinger Bands columns added
        """
        bbands = ta.bbands(df[column], length=period, std=std)
        # pandas-ta >= 0.4.x uses double std suffix: BBL_{period}_{std}_{std}
        suffix = f'{period}_{std}_{std}' if f'BBL_{period}_{std}_{std}' in bbands.columns else f'{period}_{std}'
        df[f'BB_lower_{period}'] = bbands[f'BBL_{suffix}']
        df[f'BB_middle_{period}'] = bbands[f'BBM_{suffix}']
        df[f'BB_upper_{period}'] = bbands[f'BBU_{suffix}']
        df[f'BB_bandwidth_{period}'] = bbands[f'BBB_{suffix}']
        df[f'BB_percent_{period}'] = bbands[f'BBP_{suffix}']
        return df

    @staticmethod
    def add_stochastic(
        df: pd.DataFrame,
        k_period: int = 14,
        d_period: int = 3,
        smooth_k: int = 3
    ) -> pd.DataFrame:
        """
        Add Stochastic Oscillator.

        Args:
            df: DataFrame with OHLCV data
            k_period: %K period
            d_period: %D period
            smooth_k: Smoothing for %K

        Returns:
            DataFrame with Stochastic columns added
        """
        stoch = ta.stoch(df['High'], df['Low'], df['Close'], k=k_period, d=d_period, smooth_k=smooth_k)
        df[f'STOCH_k_{k_period}'] = stoch[f'STOCHk_{k_period}_{d_period}_{smooth_k}']
        df[f'STOCH_d_{k_period}'] = stoch[f'STOCHd_{k_period}_{d_period}_{smooth_k}']
        return df

    @staticmethod
    def add_atr(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """
        Add Average True Range.

        Args:
            df: DataFrame with OHLCV data
            period: ATR period

        Returns:
            DataFrame with ATR column added
        """
        df[f'ATR_{period}'] = ta.atr(df['High'], df['Low'], df['Close'], length=period)
        return df

    @staticmethod
    def add_adx(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """
        Add Average Directional Index.

        Args:
            df: DataFrame with OHLCV data
            period: ADX period

        Returns:
            DataFrame with ADX columns added
        """
        adx = ta.adx(df['High'], df['Low'], df['Close'], length=period)
        df[f'ADX_{period}'] = adx[f'ADX_{period}']
        df[f'DMP_{period}'] = adx[f'DMP_{period}']
        df[f'DMN_{period}'] = adx[f'DMN_{period}']
        return df

    @staticmethod
    def add_obv(df: pd.DataFrame) -> pd.DataFrame:
        """
        Add On-Balance Volume.

        Args:
            df: DataFrame with OHLCV data

        Returns:
            DataFrame with OBV column added
        """
        df['OBV'] = ta.obv(df['Close'], df['Volume'])
        return df

    @staticmethod
    def add_vwap(df: pd.DataFrame) -> pd.DataFrame:
        """
        Add Volume Weighted Average Price.

        Args:
            df: DataFrame with OHLCV data

        Returns:
            DataFrame with VWAP column added
        """
        df['VWAP'] = ta.vwap(df['High'], df['Low'], df['Close'], df['Volume'])
        return df

    @staticmethod
    def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """
        Add all common technical indicators.

        Args:
            df: DataFrame with OHLCV data

        Returns:
            DataFrame with all indicators added
        """
        try:
            # Moving Averages
            df = TechnicalIndicators.add_sma(df, period=20)
            df = TechnicalIndicators.add_sma(df, period=50)
            df = TechnicalIndicators.add_sma(df, period=200)
            df = TechnicalIndicators.add_ema(df, period=12)
            df = TechnicalIndicators.add_ema(df, period=26)

            # Momentum Indicators
            df = TechnicalIndicators.add_rsi(df, period=14)
            df = TechnicalIndicators.add_macd(df)
            df = TechnicalIndicators.add_stochastic(df)

            # Volatility Indicators
            df = TechnicalIndicators.add_bollinger_bands(df, period=20)
            df = TechnicalIndicators.add_atr(df, period=14)

            # Trend Indicators
            df = TechnicalIndicators.add_adx(df, period=14)

            # Volume Indicators
            df = TechnicalIndicators.add_obv(df)
            df = TechnicalIndicators.add_vwap(df)

            log.debug("Added all technical indicators")
            return df

        except Exception as e:
            log.error(f"Error adding indicators: {e}")
            return df

    @staticmethod
    def get_signals(df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals based on indicators.

        Args:
            df: DataFrame with indicators

        Returns:
            DataFrame with signal columns added
        """
        try:
            # MA Crossover signals
            df['MA_cross_signal'] = 0
            if 'SMA_20' in df.columns and 'SMA_50' in df.columns:
                df.loc[df['SMA_20'] > df['SMA_50'], 'MA_cross_signal'] = 1
                df.loc[df['SMA_20'] < df['SMA_50'], 'MA_cross_signal'] = -1

            # RSI signals
            df['RSI_signal'] = 0
            if 'RSI_14' in df.columns:
                df.loc[df['RSI_14'] < 30, 'RSI_signal'] = 1  # Oversold - Buy
                df.loc[df['RSI_14'] > 70, 'RSI_signal'] = -1  # Overbought - Sell

            # MACD signals
            df['MACD_signal'] = 0
            if 'MACD_12_26_9' in df.columns and 'MACDs_12_26_9' in df.columns:
                df.loc[df['MACD_12_26_9'] > df['MACDs_12_26_9'], 'MACD_signal'] = 1
                df.loc[df['MACD_12_26_9'] < df['MACDs_12_26_9'], 'MACD_signal'] = -1

            # Bollinger Bands signals
            df['BB_signal'] = 0
            if 'BB_lower_20' in df.columns and 'BB_upper_20' in df.columns:
                df.loc[df['Close'] < df['BB_lower_20'], 'BB_signal'] = 1  # Buy
                df.loc[df['Close'] > df['BB_upper_20'], 'BB_signal'] = -1  # Sell

            # Combine signals
            signal_columns = ['MA_cross_signal', 'RSI_signal', 'MACD_signal', 'BB_signal']
            df['combined_signal'] = df[signal_columns].sum(axis=1)

            log.debug("Generated trading signals")
            return df

        except Exception as e:
            log.error(f"Error generating signals: {e}")
            return df
