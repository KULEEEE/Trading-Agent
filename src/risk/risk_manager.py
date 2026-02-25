"""Risk management for trading operations."""

import pandas as pd
from typing import Dict, Optional
from ..utils import log, settings


class RiskManager:
    """Manage trading risk and position sizing."""

    def __init__(
        self,
        initial_capital: float = None,
        max_position_size: float = None,
        max_portfolio_risk: float = None,
        max_daily_loss: float = None,
        stop_loss_pct: float = None,
        take_profit_pct: float = None
    ):
        """
        Initialize risk manager.

        Args:
            initial_capital: Starting capital
            max_position_size: Max position size as fraction of capital
            max_portfolio_risk: Max portfolio risk as fraction
            max_daily_loss: Max daily loss as fraction
            stop_loss_pct: Default stop loss percentage
            take_profit_pct: Default take profit percentage
        """
        self.initial_capital = initial_capital or settings.initial_capital
        self.current_capital = self.initial_capital
        self.max_position_size = max_position_size or settings.position_size_pct
        self.max_portfolio_risk = max_portfolio_risk or settings.max_portfolio_risk_pct
        self.max_daily_loss = max_daily_loss or settings.max_daily_loss_pct
        self.stop_loss_pct = stop_loss_pct or settings.stop_loss_pct
        self.take_profit_pct = take_profit_pct or settings.take_profit_pct

        self.daily_pnl = 0
        self.positions: Dict = {}
        self.trading_halted = False

        log.info("Risk manager initialized")

    def calculate_position_size(
        self,
        symbol: str,
        price: float,
        atr: Optional[float] = None
    ) -> int:
        """
        Calculate optimal position size.

        Args:
            symbol: Stock symbol
            price: Current price
            atr: Average True Range (volatility measure)

        Returns:
            Number of shares to buy
        """
        # Basic position sizing based on max position size
        max_investment = self.current_capital * self.max_position_size
        base_shares = int(max_investment / price)

        # Adjust for volatility if ATR provided
        if atr and atr > 0:
            # More volatile = smaller position
            volatility_adjustment = 1.0 - min(atr / price, 0.5)
            adjusted_shares = int(base_shares * volatility_adjustment)
        else:
            adjusted_shares = base_shares

        # Ensure we don't exceed maximum position count
        if len(self.positions) >= settings.max_positions:
            log.warning(f"Maximum positions ({settings.max_positions}) reached")
            return 0

        log.debug(f"Position size for {symbol}: {adjusted_shares} shares @ ${price:.2f}")
        return max(adjusted_shares, 0)

    def can_open_position(self, cost: float) -> bool:
        """
        Check if we can open a new position.

        Args:
            cost: Total cost of position

        Returns:
            True if position can be opened
        """
        # Check if trading is halted
        if self.trading_halted:
            log.warning("Trading halted due to risk limits")
            return False

        # Check capital availability
        if cost > self.current_capital:
            log.warning(f"Insufficient capital: ${self.current_capital:.2f} < ${cost:.2f}")
            return False

        # Check max positions
        if len(self.positions) >= settings.max_positions:
            log.warning(f"Maximum positions ({settings.max_positions}) reached")
            return False

        # Check daily loss limit
        if self.daily_pnl < -self.current_capital * self.max_daily_loss:
            log.warning(f"Daily loss limit reached: ${self.daily_pnl:.2f}")
            self.trading_halted = True
            return False

        # Check portfolio risk
        total_exposure = sum(pos['value'] for pos in self.positions.values())
        new_exposure = total_exposure + cost

        if new_exposure > self.current_capital * self.max_portfolio_risk:
            log.warning(f"Portfolio risk limit exceeded")
            return False

        return True

    def add_position(
        self,
        symbol: str,
        shares: int,
        entry_price: float,
        current_price: Optional[float] = None
    ):
        """
        Add a new position.

        Args:
            symbol: Stock symbol
            shares: Number of shares
            entry_price: Entry price
            current_price: Current price (defaults to entry_price)
        """
        if current_price is None:
            current_price = entry_price

        self.positions[symbol] = {
            'shares': shares,
            'entry_price': entry_price,
            'current_price': current_price,
            'value': shares * current_price,
            'pnl': shares * (current_price - entry_price),
            'pnl_pct': (current_price / entry_price - 1) * 100,
            'stop_loss': entry_price * (1 - self.stop_loss_pct),
            'take_profit': entry_price * (1 + self.take_profit_pct)
        }

        log.info(f"Added position: {shares} {symbol} @ ${entry_price:.2f}")

    def update_position(self, symbol: str, current_price: float):
        """
        Update position with current price.

        Args:
            symbol: Stock symbol
            current_price: Current price
        """
        if symbol not in self.positions:
            log.warning(f"Position {symbol} not found")
            return

        pos = self.positions[symbol]
        pos['current_price'] = current_price
        pos['value'] = pos['shares'] * current_price
        pos['pnl'] = pos['shares'] * (current_price - pos['entry_price'])
        pos['pnl_pct'] = (current_price / pos['entry_price'] - 1) * 100

        log.debug(f"Updated {symbol}: ${current_price:.2f}, PnL: ${pos['pnl']:.2f} ({pos['pnl_pct']:.2f}%)")

    def remove_position(self, symbol: str, exit_price: float) -> float:
        """
        Remove a position and calculate PnL.

        Args:
            symbol: Stock symbol
            exit_price: Exit price

        Returns:
            Realized PnL
        """
        if symbol not in self.positions:
            log.warning(f"Position {symbol} not found")
            return 0

        pos = self.positions[symbol]
        pnl = pos['shares'] * (exit_price - pos['entry_price'])

        # Update daily PnL
        self.daily_pnl += pnl

        # Update capital
        self.current_capital += pnl

        log.info(f"Closed position: {symbol}, PnL: ${pnl:.2f}")

        del self.positions[symbol]
        return pnl

    def check_stop_loss(self, symbol: str, current_price: float) -> bool:
        """
        Check if stop loss triggered.

        Args:
            symbol: Stock symbol
            current_price: Current price

        Returns:
            True if stop loss triggered
        """
        if symbol not in self.positions:
            return False

        pos = self.positions[symbol]
        if current_price <= pos['stop_loss']:
            log.warning(f"Stop loss triggered for {symbol}: ${current_price:.2f} <= ${pos['stop_loss']:.2f}")
            return True

        return False

    def check_take_profit(self, symbol: str, current_price: float) -> bool:
        """
        Check if take profit triggered.

        Args:
            symbol: Stock symbol
            current_price: Current price

        Returns:
            True if take profit triggered
        """
        if symbol not in self.positions:
            return False

        pos = self.positions[symbol]
        if current_price >= pos['take_profit']:
            log.info(f"Take profit triggered for {symbol}: ${current_price:.2f} >= ${pos['take_profit']:.2f}")
            return True

        return False

    def get_portfolio_value(self) -> float:
        """
        Calculate total portfolio value.

        Returns:
            Total portfolio value
        """
        positions_value = sum(pos['value'] for pos in self.positions.values())
        return self.current_capital + positions_value

    def get_portfolio_summary(self) -> Dict:
        """
        Get portfolio summary.

        Returns:
            Dictionary with portfolio metrics
        """
        portfolio_value = self.get_portfolio_value()
        positions_value = sum(pos['value'] for pos in self.positions.values())
        total_pnl = sum(pos['pnl'] for pos in self.positions.values())
        total_pnl_pct = (portfolio_value / self.initial_capital - 1) * 100 if self.initial_capital > 0 else 0

        return {
            'portfolio_value': portfolio_value,
            'cash': self.current_capital,
            'positions_value': positions_value,
            'num_positions': len(self.positions),
            'unrealized_pnl': total_pnl,
            'daily_pnl': self.daily_pnl,
            'total_pnl': portfolio_value - self.initial_capital,
            'total_pnl_pct': total_pnl_pct,
            'trading_halted': self.trading_halted
        }

    def reset_daily_metrics(self):
        """Reset daily tracking metrics."""
        self.daily_pnl = 0
        self.trading_halted = False
        log.info("Daily metrics reset")
