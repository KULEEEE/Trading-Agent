"""Configuration management using pydantic-settings."""

from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False
    )

    # General Settings
    app_name: str = Field(default="Trading-Agent", description="Application name")
    app_env: str = Field(default="development", description="Application environment")
    log_level: str = Field(default="INFO", description="Logging level")

    # Trading Settings
    default_symbols: str = Field(default="AAPL,GOOGL,MSFT,TSLA", description="Default stock symbols")
    data_interval: str = Field(default="1d", description="Data interval (1m, 5m, 1h, 1d, etc.)")
    lookback_period: int = Field(default=365, description="Lookback period in days")

    # Strategy Settings
    initial_capital: float = Field(default=100000.0, description="Initial capital")
    position_size_pct: float = Field(default=0.1, description="Position size as percentage of capital")
    max_positions: int = Field(default=5, description="Maximum number of positions")
    stop_loss_pct: float = Field(default=0.05, description="Stop loss percentage")
    take_profit_pct: float = Field(default=0.15, description="Take profit percentage")

    # Risk Management
    max_daily_loss_pct: float = Field(default=0.03, description="Maximum daily loss percentage")
    max_portfolio_risk_pct: float = Field(default=0.20, description="Maximum portfolio risk percentage")

    # Database
    db_path: str = Field(default="./data/trading_agent.db", description="Database path")

    # Monitoring
    enable_alerts: bool = Field(default=True, description="Enable alerts")
    alert_email: str = Field(default="", description="Alert email address")

    # Backtest Settings
    backtest_start_date: str = Field(default="2020-01-01", description="Backtest start date")
    backtest_end_date: str = Field(default="2024-12-31", description="Backtest end date")

    @property
    def symbols_list(self) -> List[str]:
        """Get list of symbols from comma-separated string."""
        return [s.strip() for s in self.default_symbols.split(',')]


# Global settings instance
settings = Settings()
