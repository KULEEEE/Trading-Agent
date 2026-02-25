"""Backtesting engine for trading strategies."""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
from ..strategies import BaseStrategy
from ..indicators import TechnicalIndicators
from ..utils import log, settings


class Backtester:
    """Backtesting engine for evaluating trading strategies."""

    def __init__(
        self,
        strategy: BaseStrategy,
        initial_capital: float = None,
        commission: float = 0.001
    ):
        """
        Initialize backtester.

        Args:
            strategy: Trading strategy to backtest
            initial_capital: Starting capital
            commission: Commission rate (as decimal)
        """
        self.strategy = strategy
        self.initial_capital = initial_capital or settings.initial_capital
        self.commission = commission
        self.results = None
        log.info(f"Backtester initialized with {strategy.name}")

    def run(self, df: pd.DataFrame, symbol: str = "UNKNOWN") -> Dict:
        """
        Run backtest on historical data.

        Args:
            df: DataFrame with OHLCV data
            symbol: Stock symbol

        Returns:
            Dictionary with backtest results
        """
        log.info(f"Running backtest for {symbol} with {len(df)} bars")

        # Add indicators
        df = TechnicalIndicators.add_all_indicators(df.copy())

        # Initialize tracking variables
        capital = self.initial_capital
        position = 0  # Number of shares
        entry_price = 0
        trades = []
        equity_curve = []

        # Simulate trading
        for i in range(len(df)):
            current_price = df['Close'].iloc[i]
            current_date = df.index[i]

            # Calculate current equity
            position_value = position * current_price
            total_equity = capital + position_value
            equity_curve.append({
                'date': current_date,
                'equity': total_equity,
                'cash': capital,
                'position_value': position_value
            })

            # Check if we should sell
            if position > 0:
                if self.strategy.should_sell(df, i, entry_price):
                    # Sell position
                    proceeds = position * current_price
                    commission_cost = proceeds * self.commission
                    capital += proceeds - commission_cost

                    pnl = proceeds - (position * entry_price)
                    pnl_pct = (current_price / entry_price - 1) * 100

                    trades.append({
                        'symbol': symbol,
                        'type': 'SELL',
                        'date': current_date,
                        'price': current_price,
                        'shares': position,
                        'value': proceeds,
                        'commission': commission_cost,
                        'pnl': pnl,
                        'pnl_pct': pnl_pct
                    })

                    log.debug(f"SELL {position} @ ${current_price:.2f}, PnL: ${pnl:.2f} ({pnl_pct:.2f}%)")

                    position = 0
                    entry_price = 0

            # Check if we should buy
            elif position == 0:
                if self.strategy.should_buy(df, i):
                    # Calculate position size
                    max_shares = int(capital * settings.position_size_pct / current_price)

                    if max_shares > 0:
                        # Buy shares
                        cost = max_shares * current_price
                        commission_cost = cost * self.commission
                        total_cost = cost + commission_cost

                        if total_cost <= capital:
                            capital -= total_cost
                            position = max_shares
                            entry_price = current_price

                            trades.append({
                                'symbol': symbol,
                                'type': 'BUY',
                                'date': current_date,
                                'price': current_price,
                                'shares': max_shares,
                                'value': cost,
                                'commission': commission_cost,
                                'pnl': 0,
                                'pnl_pct': 0
                            })

                            log.debug(f"BUY {max_shares} @ ${current_price:.2f}")

        # Close any open position at end
        if position > 0:
            current_price = df['Close'].iloc[-1]
            proceeds = position * current_price
            commission_cost = proceeds * self.commission
            capital += proceeds - commission_cost

            pnl = proceeds - (position * entry_price)
            pnl_pct = (current_price / entry_price - 1) * 100

            trades.append({
                'symbol': symbol,
                'type': 'SELL',
                'date': df.index[-1],
                'price': current_price,
                'shares': position,
                'value': proceeds,
                'commission': commission_cost,
                'pnl': pnl,
                'pnl_pct': pnl_pct
            })

            position = 0

        # Calculate metrics
        final_equity = capital
        total_return = (final_equity - self.initial_capital) / self.initial_capital * 100

        # Create equity curve DataFrame
        equity_df = pd.DataFrame(equity_curve)
        equity_df.set_index('date', inplace=True)

        # Calculate additional metrics
        metrics = self._calculate_metrics(equity_df, trades)

        results = {
            'symbol': symbol,
            'strategy': self.strategy.name,
            'initial_capital': self.initial_capital,
            'final_capital': final_equity,
            'total_return': total_return,
            'total_trades': len(trades),
            'equity_curve': equity_df,
            'trades': pd.DataFrame(trades) if trades else pd.DataFrame(),
            **metrics
        }

        self.results = results
        log.info(f"Backtest complete: Return={total_return:.2f}%, Trades={len(trades)}")

        return results

    def _calculate_metrics(self, equity_df: pd.DataFrame, trades: List[Dict]) -> Dict:
        """
        Calculate performance metrics.

        Args:
            equity_df: Equity curve DataFrame
            trades: List of trades

        Returns:
            Dictionary with metrics
        """
        metrics = {}

        # Returns
        equity_df['returns'] = equity_df['equity'].pct_change()

        # Sharpe ratio (assuming 252 trading days, 0% risk-free rate)
        if len(equity_df['returns']) > 0:
            sharpe = np.sqrt(252) * equity_df['returns'].mean() / equity_df['returns'].std() if equity_df['returns'].std() != 0 else 0
            metrics['sharpe_ratio'] = sharpe
        else:
            metrics['sharpe_ratio'] = 0

        # Maximum drawdown
        equity_df['cummax'] = equity_df['equity'].cummax()
        equity_df['drawdown'] = (equity_df['equity'] - equity_df['cummax']) / equity_df['cummax']
        metrics['max_drawdown'] = equity_df['drawdown'].min() * 100

        # Win rate and average win/loss
        if trades:
            trades_df = pd.DataFrame(trades)
            sell_trades = trades_df[trades_df['type'] == 'SELL']

            if len(sell_trades) > 0:
                winning_trades = sell_trades[sell_trades['pnl'] > 0]
                losing_trades = sell_trades[sell_trades['pnl'] <= 0]

                metrics['win_rate'] = len(winning_trades) / len(sell_trades) * 100 if len(sell_trades) > 0 else 0
                metrics['avg_win'] = winning_trades['pnl'].mean() if len(winning_trades) > 0 else 0
                metrics['avg_loss'] = losing_trades['pnl'].mean() if len(losing_trades) > 0 else 0
                metrics['profit_factor'] = abs(winning_trades['pnl'].sum() / losing_trades['pnl'].sum()) if len(losing_trades) > 0 and losing_trades['pnl'].sum() != 0 else 0
            else:
                metrics['win_rate'] = 0
                metrics['avg_win'] = 0
                metrics['avg_loss'] = 0
                metrics['profit_factor'] = 0
        else:
            metrics['win_rate'] = 0
            metrics['avg_win'] = 0
            metrics['avg_loss'] = 0
            metrics['profit_factor'] = 0

        return metrics

    def print_results(self):
        """Print backtest results summary."""
        if not self.results:
            log.warning("No results to print. Run backtest first.")
            return

        r = self.results

        print("\n" + "="*60)
        print(f"BACKTEST RESULTS: {r['symbol']} - {r['strategy']}")
        print("="*60)
        print(f"Initial Capital:    ${r['initial_capital']:,.2f}")
        print(f"Final Capital:      ${r['final_capital']:,.2f}")
        print(f"Total Return:       {r['total_return']:.2f}%")
        print(f"Total Trades:       {r['total_trades']}")
        print(f"Win Rate:           {r['win_rate']:.2f}%")
        print(f"Avg Win:            ${r['avg_win']:.2f}")
        print(f"Avg Loss:           ${r['avg_loss']:.2f}")
        print(f"Profit Factor:      {r['profit_factor']:.2f}")
        print(f"Sharpe Ratio:       {r['sharpe_ratio']:.2f}")
        print(f"Max Drawdown:       {r['max_drawdown']:.2f}%")
        print("="*60 + "\n")
