"""Main entry point for Trading Agent."""

import argparse
from .trading_agent import TradingAgent
from ..strategies import MACrossoverStrategy, RSIStrategy
from ..utils import log, settings


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Trading Agent - Yahoo Finance Stock Trading')

    parser.add_argument(
        '--mode',
        type=str,
        choices=['backtest', 'analyze', 'simulate', 'update'],
        default='backtest',
        help='Operation mode'
    )

    parser.add_argument(
        '--strategy',
        type=str,
        choices=['ma_cross', 'rsi'],
        default='ma_cross',
        help='Trading strategy to use'
    )

    parser.add_argument(
        '--symbol',
        type=str,
        help='Stock symbol to analyze/backtest (if not specified, uses all configured symbols)'
    )

    parser.add_argument(
        '--days',
        type=int,
        default=365,
        help='Number of days for backtest or analysis'
    )

    args = parser.parse_args()

    # Banner
    print("\n" + "="*80)
    print(" "*20 + "TRADING AGENT - Yahoo Finance Stock Trading")
    print("="*80)
    print(f"Environment: {settings.app_env}")
    print(f"Strategy: {args.strategy}")
    print(f"Mode: {args.mode}")
    print("="*80 + "\n")

    # Select strategy
    if args.strategy == 'ma_cross':
        strategy = MACrossoverStrategy(
            short_period=20,
            long_period=50,
            stop_loss_pct=settings.stop_loss_pct,
            take_profit_pct=settings.take_profit_pct
        )
    else:  # rsi
        strategy = RSIStrategy(
            period=14,
            oversold=30,
            overbought=70,
            stop_loss_pct=settings.stop_loss_pct,
            take_profit_pct=settings.take_profit_pct
        )

    # Initialize agent
    symbols = [args.symbol] if args.symbol else None
    agent = TradingAgent(strategy=strategy, symbols=symbols)

    try:
        if args.mode == 'backtest':
            # Run backtest
            if args.symbol:
                agent.run_backtest(args.symbol, days=args.days)
            else:
                agent.run_backtest_all(days=args.days)

        elif args.mode == 'analyze':
            # Analyze symbol(s)
            if args.symbol:
                agent.analyze_symbol(args.symbol, days=args.days)
            else:
                for symbol in agent.symbols:
                    agent.analyze_symbol(symbol, days=args.days)

        elif args.mode == 'simulate':
            # Simulate live trading
            log.info("Starting live trading simulation...")
            agent.simulate_live_trading(days=args.days)

        elif args.mode == 'update':
            # Update data
            agent.update_data()
            log.info("Data update complete")

    except KeyboardInterrupt:
        log.info("Interrupted by user")

    except Exception as e:
        log.error(f"Error in main: {e}", exc_info=True)

    finally:
        agent.close()

    print("\n" + "="*80)
    print(" "*30 + "Trading Agent Completed")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
