"""Main trading agent orchestrator."""

import time
from typing import List, Optional, Dict
from datetime import datetime
from ..data import DataManager
from ..strategies import BaseStrategy, MACrossoverStrategy, RSIStrategy
from ..backtest import Backtester
from ..risk import RiskManager
from ..monitoring import Monitor
from ..indicators import TechnicalIndicators, FundamentalIndicators
from ..utils import log, settings


class TradingAgent:
    """Main trading agent orchestrating all components."""

    def __init__(
        self,
        strategy: Optional[BaseStrategy] = None,
        symbols: Optional[List[str]] = None
    ):
        """
        Initialize trading agent.

        Args:
            strategy: Trading strategy to use
            symbols: List of symbols to trade
        """
        self.symbols = symbols or settings.symbols_list
        self.strategy = strategy or MACrossoverStrategy()

        # Initialize components
        self.data_manager = DataManager()
        self.risk_manager = RiskManager()
        self.monitor = Monitor()
        self.fundamental = FundamentalIndicators()

        log.info(f"Trading Agent initialized with {self.strategy.name}")
        log.info(f"Tracking symbols: {', '.join(self.symbols)}")

    def run_backtest(self, symbol: str, days: int = 365):
        """
        Run backtest for a symbol.

        Args:
            symbol: Stock symbol
            days: Number of days to backtest
        """
        log.info(f"Running backtest for {symbol}")

        # Fetch data
        df = self.data_manager.get_latest_data(symbol, days=days)

        if df.empty:
            log.error(f"No data available for {symbol}")
            return None

        # Run backtest
        backtester = Backtester(
            strategy=self.strategy,
            initial_capital=settings.initial_capital
        )

        results = backtester.run(df, symbol)
        backtester.print_results()

        return results

    def run_backtest_all(self, days: int = 365):
        """
        Run backtest for all symbols.

        Args:
            days: Number of days to backtest
        """
        log.info("Running backtest for all symbols")

        results = {}
        for symbol in self.symbols:
            try:
                result = self.run_backtest(symbol, days)
                if result:
                    results[symbol] = result
            except Exception as e:
                log.error(f"Error backtesting {symbol}: {e}")

        # Summary
        if results:
            print("\n" + "="*80)
            print("BACKTEST SUMMARY - ALL SYMBOLS")
            print("="*80)
            print(f"{'Symbol':<10} {'Return':<12} {'Trades':<10} {'Win Rate':<12} {'Sharpe':<10} {'Max DD':<10}")
            print("-"*80)

            for symbol, r in results.items():
                print(f"{symbol:<10} {r['total_return']:>10.2f}% {r['total_trades']:>8} "
                      f"{r['win_rate']:>10.2f}% {r['sharpe_ratio']:>8.2f} {r['max_drawdown']:>8.2f}%")

            print("="*80 + "\n")

        return results

    def analyze_symbol(self, symbol: str, days: int = 90):
        """
        Analyze a symbol with technical indicators.

        Args:
            symbol: Stock symbol
            days: Number of days to analyze
        """
        log.info(f"Analyzing {symbol}")

        # Fetch data
        df = self.data_manager.get_latest_data(symbol, days=days)

        if df.empty:
            log.error(f"No data available for {symbol}")
            return None

        # Add indicators
        df = TechnicalIndicators.add_all_indicators(df)
        df = TechnicalIndicators.get_signals(df)

        # Get latest values
        latest = df.iloc[-1]

        def _v(key, default=0):
            """Get value safely, replacing NaN/None with default."""
            import math
            val = latest.get(key, default)
            if val is None:
                return default
            try:
                if math.isnan(val):
                    return default
            except TypeError:
                return default
            return val

        print(f"\n{'='*60}")
        print(f"ANALYSIS: {symbol}")
        print(f"{'='*60}")
        print(f"Date:           {latest.name}")
        print(f"Close:          ${latest['Close']:.2f}")
        print(f"\nMoving Averages:")
        print(f"  SMA 20:       ${_v('SMA_20'):.2f}")
        print(f"  SMA 50:       ${_v('SMA_50'):.2f}")
        print(f"  SMA 200:      ${_v('SMA_200'):.2f}")
        print(f"\nMomentum Indicators:")
        print(f"  RSI:          {_v('RSI_14'):.2f}")
        print(f"  MACD:         {_v('MACD_12_26_9'):.2f}")
        print(f"  MACD Signal:  {_v('MACDs_12_26_9'):.2f}")
        print(f"\nVolatility:")
        print(f"  ATR:          ${_v('ATR_14'):.2f}")
        print(f"  BB Upper:     ${_v('BB_upper_20'):.2f}")
        print(f"  BB Lower:     ${_v('BB_lower_20'):.2f}")
        print(f"\nSignals:")
        print(f"  MA Signal:    {_v('MA_cross_signal')}")
        print(f"  RSI Signal:   {_v('RSI_signal')}")
        print(f"  MACD Signal:  {_v('MACD_signal')}")
        print(f"  Combined:     {_v('combined_signal')}")
        print(f"{'='*60}\n")

        return df

    def update_data(self):
        """Update data for all tracked symbols."""
        log.info("Updating data for all symbols")
        self.data_manager.update_all_symbols(self.symbols)

    def get_portfolio_status(self):
        """Get current portfolio status."""
        summary = self.risk_manager.get_portfolio_summary()
        self.monitor.log_portfolio_update(summary)
        return summary

    def simulate_live_trading(self, days: int = 30):
        """
        Simulate live trading for demonstration.

        Args:
            days: Number of days to simulate
        """
        log.info(f"Simulating live trading for {days} days")

        for symbol in self.symbols:
            try:
                # Fetch data
                df = self.data_manager.get_latest_data(symbol, days=days)

                if df.empty:
                    log.warning(f"No data for {symbol}")
                    continue

                # Add indicators
                df = TechnicalIndicators.add_all_indicators(df)

                # Simulate trading day by day
                for i in range(50, len(df)):  # Start after enough data for indicators
                    current_price = df['Close'].iloc[i]
                    current_date = df.index[i]

                    # Check if we have a position
                    if symbol in self.risk_manager.positions:
                        # Update position
                        self.risk_manager.update_position(symbol, current_price)

                        # Check exit conditions
                        entry_price = self.risk_manager.positions[symbol]['entry_price']

                        if self.strategy.should_sell(df, i, entry_price):
                            shares = self.risk_manager.positions[symbol]['shares']
                            pnl = self.risk_manager.remove_position(symbol, current_price)

                            self.monitor.log_trade(symbol, 'SELL', shares, current_price, pnl)

                    else:
                        # Check entry conditions
                        if self.strategy.should_buy(df, i):
                            shares = self.risk_manager.calculate_position_size(
                                symbol,
                                current_price,
                                atr=df.get('ATR_14', pd.Series([None])).iloc[i]
                            )

                            if shares > 0:
                                cost = shares * current_price * 1.001  # Include commission

                                if self.risk_manager.can_open_position(cost):
                                    self.risk_manager.add_position(symbol, shares, current_price)
                                    self.risk_manager.current_capital -= cost

                                    self.monitor.log_trade(symbol, 'BUY', shares, current_price)

            except Exception as e:
                log.error(f"Error simulating trading for {symbol}: {e}")

        # Final portfolio status
        summary = self.get_portfolio_status()
        self.monitor.check_risk_alerts(summary)

        return summary

    def analyze_fundamentals(self, symbol: str) -> Dict:
        """
        Analyze a symbol with fundamental indicators.

        Args:
            symbol: Stock symbol

        Returns:
            Full fundamental analysis dictionary
        """
        log.info(f"Analyzing fundamentals for {symbol}")
        analysis = self.fundamental.get_full_analysis(symbol)

        if not analysis:
            log.error(f"No fundamental data for {symbol}")
            return {}

        fmt = self.fundamental.format_number
        val = analysis.get('valuation', {})
        prof = analysis.get('profitability', {})
        health = analysis.get('financial_health', {})
        eps = analysis.get('eps', {})
        div = analysis.get('dividends', {})
        risk = analysis.get('risk', {})
        analyst = analysis.get('analyst', {})
        val_interp = analysis.get('valuation_interpretation', {})
        prof_interp = analysis.get('profitability_interpretation', {})
        health_interp = analysis.get('health_interpretation', {})

        print(f"\n{'='*60}")
        print(f"FUNDAMENTAL ANALYSIS: {symbol} - {analysis.get('name', '')}")
        print(f"Sector: {analysis.get('sector')} | Industry: {analysis.get('industry')}")
        print(f"{'='*60}")
        print(f"Price: ${analysis.get('current_price', 0):.2f} | Market Cap: {fmt(analysis.get('market_cap'), prefix='$')}")
        print(f"\n--- Valuation ---")
        print(f"  PER (trailing):  {val.get('trailing_pe', 0):.2f}  [{val_interp.get('pe_rating', 'N/A')}]")
        print(f"  PER (forward):   {val.get('forward_pe', 0):.2f}")
        print(f"  PBR:             {val.get('price_to_book', 0):.2f}  [{val_interp.get('pb_rating', 'N/A')}]")
        print(f"  PSR:             {val.get('price_to_sales', 0):.2f}")
        print(f"  PEG:             {val.get('peg_ratio', 0):.2f}  [{val_interp.get('peg_rating', 'N/A')}]")
        print(f"  EV/EBITDA:       {val.get('ev_to_ebitda', 0):.2f}  [{val_interp.get('ev_ebitda_rating', 'N/A')}]")
        print(f"  EV/Revenue:      {val.get('ev_to_revenue', 0):.2f}")
        print(f"  Overall:         [{val_interp.get('overall_rating', 'N/A')}] (score: {val_interp.get('overall_score', 0):.1f}/5)")
        print(f"\n--- Profitability ---")
        print(f"  ROE:             {prof.get('return_on_equity', 0)*100:.2f}%  [{prof_interp.get('roe_rating', 'N/A')}]")
        print(f"  ROA:             {prof.get('return_on_assets', 0)*100:.2f}%  [{prof_interp.get('roa_rating', 'N/A')}]")
        print(f"  Gross Margin:    {prof.get('gross_margins', 0)*100:.2f}%")
        print(f"  Operating:       {prof.get('operating_margins', 0)*100:.2f}%")
        print(f"  Net Margin:      {prof.get('profit_margins', 0)*100:.2f}%  [{prof_interp.get('margin_rating', 'N/A')}]")
        print(f"\n--- EPS ---")
        print(f"  TTM EPS:         ${eps.get('trailing_eps', 0):.2f}")
        print(f"  Forward EPS:     ${eps.get('forward_eps', 0):.2f}")
        print(f"  Revenue/Share:   ${eps.get('revenue_per_share', 0):.2f}")
        print(f"\n--- Growth ---")
        growth = analysis.get('growth', {})
        print(f"  Revenue Growth:  {growth.get('revenue_growth', 0)*100:.2f}%")
        print(f"  Earnings Growth: {growth.get('earnings_growth', 0)*100:.2f}%")
        print(f"\n--- Financial Health ---")
        print(f"  Current Ratio:   {health.get('current_ratio', 0):.2f}  [{health_interp.get('current_ratio_rating', 'N/A')}]")
        print(f"  Debt/Equity:     {health.get('debt_to_equity', 0):.2f}  [{health_interp.get('debt_rating', 'N/A')}]")
        print(f"  Total Cash:      {fmt(health.get('total_cash'), prefix='$')}")
        print(f"  Total Debt:      {fmt(health.get('total_debt'), prefix='$')}")
        print(f"  Free Cash Flow:  {fmt(health.get('free_cashflow'), prefix='$')}  [{health_interp.get('fcf_rating', 'N/A')}]")
        print(f"\n--- Dividends ---")
        print(f"  Yield:           {div.get('dividend_yield', 0)*100:.2f}%")
        print(f"  Payout Ratio:    {div.get('payout_ratio', 0)*100:.2f}%")
        print(f"  5Y Avg Yield:    {div.get('five_year_avg_yield', 0):.2f}%")
        print(f"\n--- Analyst Consensus ---")
        print(f"  Recommendation:  {analyst.get('recommendation', 'N/A').upper()}")
        print(f"  Target (mean):   ${analyst.get('target_mean', 0):.2f}")
        print(f"  Target Range:    ${analyst.get('target_low', 0):.2f} - ${analyst.get('target_high', 0):.2f}")
        print(f"  # Analysts:      {analyst.get('num_analysts', 0)}")
        print(f"\n--- Risk ---")
        print(f"  Beta:            {risk.get('beta', 0):.3f}")
        print(f"  52W Range:       ${risk.get('52_week_low', 0):.2f} - ${risk.get('52_week_high', 0):.2f}")
        print(f"{'='*60}\n")

        return analysis

    def compare_fundamentals(self, symbols: Optional[List[str]] = None) -> Dict:
        """
        Compare fundamental metrics across symbols.

        Args:
            symbols: List of symbols (uses default if None)

        Returns:
            Comparison dictionary
        """
        if symbols is None:
            symbols = self.symbols

        comparisons = self.fundamental.compare_symbols(symbols)

        if comparisons:
            fmt = self.fundamental.format_number
            print(f"\n{'='*100}")
            print("FUNDAMENTAL COMPARISON")
            print(f"{'='*100}")
            print(f"{'Symbol':<8} {'Price':>10} {'PER':>8} {'PBR':>8} {'ROE':>8} {'Margin':>8} {'D/E':>8} {'Yield':>8} {'Rec':>8}")
            print(f"{'-'*100}")

            for sym, data in comparisons.items():
                val = data.get('valuation', {})
                prof = data.get('profitability', {})
                health = data.get('financial_health', {})
                div = data.get('dividends', {})
                analyst = data.get('analyst', {})

                print(f"{sym:<8} "
                      f"${data.get('current_price', 0):>8.2f} "
                      f"{val.get('trailing_pe', 0):>7.1f} "
                      f"{val.get('price_to_book', 0):>7.1f} "
                      f"{prof.get('return_on_equity', 0)*100:>6.1f}% "
                      f"{prof.get('profit_margins', 0)*100:>6.1f}% "
                      f"{health.get('debt_to_equity', 0):>7.1f} "
                      f"{div.get('dividend_yield', 0)*100:>6.2f}% "
                      f"{analyst.get('recommendation', 'N/A'):>8}")

            print(f"{'='*100}\n")

        return comparisons

    def close(self):
        """Clean up resources."""
        self.data_manager.close()
        log.info("Trading agent closed")


# Import pandas for simulate_live_trading
import pandas as pd
