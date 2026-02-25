"""Monitoring and alerting system for trading agent."""

from typing import Dict, Optional
from datetime import datetime
from ..utils import log


class Monitor:
    """Monitor trading activity and send alerts."""

    def __init__(self):
        """Initialize monitor."""
        self.alerts = []
        log.info("Monitor initialized")

    def log_trade(
        self,
        symbol: str,
        trade_type: str,
        quantity: int,
        price: float,
        pnl: Optional[float] = None
    ):
        """
        Log a trade execution.

        Args:
            symbol: Stock symbol
            trade_type: 'BUY' or 'SELL'
            quantity: Number of shares
            price: Trade price
            pnl: Profit/loss (for sell trades)
        """
        timestamp = datetime.now()

        trade_log = {
            'timestamp': timestamp,
            'symbol': symbol,
            'type': trade_type,
            'quantity': quantity,
            'price': price,
            'value': quantity * price,
            'pnl': pnl
        }

        if trade_type == 'BUY':
            log.info(f"TRADE: BUY {quantity} {symbol} @ ${price:.2f}")
        else:
            pnl_str = f", PnL: ${pnl:.2f}" if pnl is not None else ""
            log.info(f"TRADE: SELL {quantity} {symbol} @ ${price:.2f}{pnl_str}")

        self.alerts.append(trade_log)

    def log_portfolio_update(self, portfolio_summary: Dict):
        """
        Log portfolio status update.

        Args:
            portfolio_summary: Portfolio summary dictionary
        """
        log.info(f"PORTFOLIO: Value=${portfolio_summary['portfolio_value']:.2f}, "
                f"Cash=${portfolio_summary['cash']:.2f}, "
                f"Positions={portfolio_summary['num_positions']}, "
                f"PnL={portfolio_summary['total_pnl_pct']:.2f}%")

    def send_alert(self, message: str, level: str = "INFO"):
        """
        Send alert message.

        Args:
            message: Alert message
            level: Alert level (INFO, WARNING, ERROR)
        """
        alert = {
            'timestamp': datetime.now(),
            'level': level,
            'message': message
        }

        self.alerts.append(alert)

        if level == "ERROR":
            log.error(f"ALERT: {message}")
        elif level == "WARNING":
            log.warning(f"ALERT: {message}")
        else:
            log.info(f"ALERT: {message}")

    def check_risk_alerts(self, portfolio_summary: Dict):
        """
        Check for risk-related alerts.

        Args:
            portfolio_summary: Portfolio summary dictionary
        """
        # Check for daily loss limit
        if portfolio_summary['daily_pnl'] < 0:
            loss_pct = abs(portfolio_summary['daily_pnl'] / portfolio_summary['portfolio_value']) * 100
            if loss_pct > 2.0:  # Alert if daily loss > 2%
                self.send_alert(
                    f"Daily loss exceeds 2%: {loss_pct:.2f}%",
                    level="WARNING"
                )

        # Check if trading halted
        if portfolio_summary.get('trading_halted', False):
            self.send_alert(
                "Trading halted due to risk limits",
                level="ERROR"
            )

    def get_recent_alerts(self, count: int = 10):
        """
        Get recent alerts.

        Args:
            count: Number of recent alerts to return

        Returns:
            List of recent alerts
        """
        return self.alerts[-count:] if self.alerts else []

    def clear_alerts(self):
        """Clear all alerts."""
        self.alerts = []
        log.info("Alerts cleared")
