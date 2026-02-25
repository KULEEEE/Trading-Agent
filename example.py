"""Example usage of Trading Agent."""

from src.agent import TradingAgent
from src.strategies import MACrossoverStrategy, RSIStrategy
from src.utils import settings

# Example 1: Run backtest with MA Crossover strategy
def example_backtest_ma():
    """Run backtest with Moving Average Crossover strategy."""
    print("\n" + "="*80)
    print("Example 1: Backtest with MA Crossover Strategy")
    print("="*80)

    strategy = MACrossoverStrategy(short_period=20, long_period=50)
    agent = TradingAgent(strategy=strategy, symbols=['AAPL'])

    # Run backtest for AAPL
    results = agent.run_backtest('AAPL', days=365)

    agent.close()
    return results


# Example 2: Run backtest with RSI strategy
def example_backtest_rsi():
    """Run backtest with RSI strategy."""
    print("\n" + "="*80)
    print("Example 2: Backtest with RSI Strategy")
    print("="*80)

    strategy = RSIStrategy(period=14, oversold=30, overbought=70)
    agent = TradingAgent(strategy=strategy, symbols=['GOOGL'])

    # Run backtest for GOOGL
    results = agent.run_backtest('GOOGL', days=365)

    agent.close()
    return results


# Example 3: Analyze multiple symbols
def example_analyze():
    """Analyze multiple symbols with technical indicators."""
    print("\n" + "="*80)
    print("Example 3: Analyze Multiple Symbols")
    print("="*80)

    agent = TradingAgent(symbols=['AAPL', 'GOOGL', 'MSFT'])

    # Analyze each symbol
    for symbol in agent.symbols:
        agent.analyze_symbol(symbol, days=90)

    agent.close()


# Example 4: Run backtest for all configured symbols
def example_backtest_all():
    """Run backtest for all configured symbols."""
    print("\n" + "="*80)
    print("Example 4: Backtest All Symbols")
    print("="*80)

    strategy = MACrossoverStrategy(short_period=20, long_period=50)
    agent = TradingAgent(strategy=strategy)

    # Run backtest for all symbols
    results = agent.run_backtest_all(days=365)

    agent.close()
    return results


# Example 5: Simulate live trading
def example_simulate():
    """Simulate live trading."""
    print("\n" + "="*80)
    print("Example 5: Simulate Live Trading")
    print("="*80)

    strategy = MACrossoverStrategy(short_period=20, long_period=50)
    agent = TradingAgent(strategy=strategy, symbols=['AAPL', 'GOOGL'])

    # Simulate trading for 30 days
    summary = agent.simulate_live_trading(days=30)

    print("\nFinal Portfolio Summary:")
    print(f"Portfolio Value: ${summary['portfolio_value']:,.2f}")
    print(f"Cash: ${summary['cash']:,.2f}")
    print(f"Positions: {summary['num_positions']}")
    print(f"Total PnL: ${summary['total_pnl']:,.2f} ({summary['total_pnl_pct']:.2f}%)")

    agent.close()
    return summary


if __name__ == "__main__":
    # Uncomment the example you want to run

    # example_backtest_ma()
    # example_backtest_rsi()
    # example_analyze()
    example_backtest_all()
    # example_simulate()
