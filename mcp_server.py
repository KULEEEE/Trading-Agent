#!/usr/bin/env python3
"""MCP Server for Trading Agent - Claude Code Integration."""

import asyncio
import json
from typing import Any, Optional
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from src.agent import TradingAgent
from src.strategies import MACrossoverStrategy, RSIStrategy
from src.indicators import FundamentalIndicators
from src.utils import log, settings

# Initialize MCP server
app = Server("trading-agent")


# Tool definitions
@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available trading tools."""
    return [
        Tool(
            name="backtest_stock",
            description="Run backtest on a stock symbol with specified strategy. Returns performance metrics including return %, win rate, Sharpe ratio, and max drawdown.",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock ticker symbol (e.g., AAPL, GOOGL, MSFT)"
                    },
                    "strategy": {
                        "type": "string",
                        "enum": ["ma_crossover", "rsi"],
                        "description": "Trading strategy: ma_crossover (Moving Average Crossover) or rsi (RSI strategy)",
                        "default": "ma_crossover"
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days to backtest (default: 365)",
                        "default": 365
                    }
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="analyze_stock",
            description="Analyze a stock with technical indicators. Returns current price, moving averages, RSI, MACD, volatility metrics, and trading signals.",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock ticker symbol (e.g., AAPL, GOOGL, MSFT)"
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days to analyze (default: 90)",
                        "default": 90
                    }
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="backtest_multiple",
            description="Run backtest on multiple stocks and compare performance. Returns summary table with metrics for all symbols.",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbols": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of stock ticker symbols (e.g., ['AAPL', 'GOOGL', 'MSFT']). If not provided, uses configured default symbols."
                    },
                    "strategy": {
                        "type": "string",
                        "enum": ["ma_crossover", "rsi"],
                        "description": "Trading strategy to use",
                        "default": "ma_crossover"
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days to backtest",
                        "default": 365
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="simulate_trading",
            description="Simulate live trading with the strategy. Shows how the strategy would perform in a live environment with position management.",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbols": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of stock ticker symbols to trade"
                    },
                    "strategy": {
                        "type": "string",
                        "enum": ["ma_crossover", "rsi"],
                        "description": "Trading strategy to use",
                        "default": "ma_crossover"
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days to simulate",
                        "default": 30
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_portfolio_status",
            description="Get current portfolio status including positions, cash, and P&L.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="analyze_fundamentals",
            description="Analyze a stock's fundamental indicators: PER, PBR, EPS, ROE, ROA, profit margins, debt ratio, dividends, analyst consensus, and more. Provides valuation ratings and interpretations.",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock ticker symbol (e.g., AAPL, GOOGL, MSFT)"
                    }
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="compare_fundamentals",
            description="Compare fundamental metrics (PER, PBR, ROE, margins, dividends) across multiple stocks side by side.",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbols": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of stock ticker symbols to compare (e.g., ['AAPL', 'MSFT', 'GOOGL'])"
                    }
                },
                "required": ["symbols"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""
    try:
        if name == "backtest_stock":
            return await backtest_stock(arguments)
        elif name == "analyze_stock":
            return await analyze_stock(arguments)
        elif name == "backtest_multiple":
            return await backtest_multiple(arguments)
        elif name == "simulate_trading":
            return await simulate_trading(arguments)
        elif name == "get_portfolio_status":
            return await get_portfolio_status(arguments)
        elif name == "analyze_fundamentals":
            return await analyze_fundamentals_tool(arguments)
        elif name == "compare_fundamentals":
            return await compare_fundamentals_tool(arguments)
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    except Exception as e:
        log.error(f"Error in tool {name}: {e}", exc_info=True)
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def backtest_stock(args: dict) -> list[TextContent]:
    """Run backtest on a single stock."""
    symbol = args["symbol"].upper()
    strategy_name = args.get("strategy", "ma_crossover")
    days = args.get("days", 365)

    # Create strategy
    if strategy_name == "ma_crossover":
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

    # Run backtest
    agent = TradingAgent(strategy=strategy, symbols=[symbol])
    results = agent.run_backtest(symbol, days=days)
    agent.close()

    if not results:
        return [TextContent(type="text", text=f"Failed to backtest {symbol}")]

    # Format results
    output = f"""
📊 **BACKTEST RESULTS: {symbol}**
Strategy: {results['strategy']}
Period: {days} days

💰 **Performance:**
- Initial Capital: ${results['initial_capital']:,.2f}
- Final Capital: ${results['final_capital']:,.2f}
- Total Return: {results['total_return']:.2f}%

📈 **Trading Stats:**
- Total Trades: {results['total_trades']}
- Win Rate: {results['win_rate']:.2f}%
- Average Win: ${results['avg_win']:.2f}
- Average Loss: ${results['avg_loss']:.2f}
- Profit Factor: {results['profit_factor']:.2f}

📉 **Risk Metrics:**
- Sharpe Ratio: {results['sharpe_ratio']:.2f}
- Max Drawdown: {results['max_drawdown']:.2f}%
"""

    return [TextContent(type="text", text=output)]


async def analyze_stock(args: dict) -> list[TextContent]:
    """Analyze a stock with technical indicators."""
    import math

    def safe(val, default=0):
        """Return default if value is None or NaN."""
        if val is None:
            return default
        try:
            if math.isnan(val):
                return default
        except TypeError:
            return default
        return val

    def signal_label(val):
        v = safe(val, 0)
        if v > 0:
            return "BUY"
        elif v < 0:
            return "SELL"
        return "HOLD"

    symbol = args["symbol"].upper()
    days = args.get("days", 90)

    agent = TradingAgent(symbols=[symbol])
    df = agent.analyze_symbol(symbol, days=days)
    agent.close()

    if df is None or df.empty:
        return [TextContent(type="text", text=f"Failed to analyze {symbol}")]

    # Get latest values
    latest = df.iloc[-1]

    rsi_val = safe(latest.get('RSI_14'), 50)
    rsi_status = "Oversold" if rsi_val < 30 else "Overbought" if rsi_val > 70 else "Neutral"
    combined = safe(latest.get('combined_signal'), 0)
    if combined > 2:
        combined_label = "STRONG BUY"
    elif combined > 0:
        combined_label = "BUY"
    elif combined < -2:
        combined_label = "STRONG SELL"
    elif combined < 0:
        combined_label = "SELL"
    else:
        combined_label = "HOLD"

    output = f"""
**TECHNICAL ANALYSIS: {symbol}**
Date: {latest.name}
Current Price: ${safe(latest['Close']):.2f}

**Moving Averages:**
- SMA 20: ${safe(latest.get('SMA_20')):.2f}
- SMA 50: ${safe(latest.get('SMA_50')):.2f}
- SMA 200: ${safe(latest.get('SMA_200')):.2f}
- EMA 12: ${safe(latest.get('EMA_12')):.2f}
- EMA 26: ${safe(latest.get('EMA_26')):.2f}

**Momentum Indicators:**
- RSI (14): {rsi_val:.2f} ({rsi_status})
- MACD: {safe(latest.get('MACD_12_26_9')):.4f}
- MACD Signal: {safe(latest.get('MACDs_12_26_9')):.4f}
- MACD Histogram: {safe(latest.get('MACDh_12_26_9')):.4f}

**Volatility:**
- ATR (14): ${safe(latest.get('ATR_14')):.2f}
- Bollinger Upper: ${safe(latest.get('BB_upper_20')):.2f}
- Bollinger Middle: ${safe(latest.get('BB_middle_20')):.2f}
- Bollinger Lower: ${safe(latest.get('BB_lower_20')):.2f}

**Trading Signals:**
- MA Signal: {signal_label(latest.get('MA_cross_signal'))}
- RSI Signal: {signal_label(latest.get('RSI_signal'))}
- MACD Signal: {signal_label(latest.get('MACD_signal'))}
- **Combined Signal: {combined_label}**
"""

    return [TextContent(type="text", text=output)]


async def backtest_multiple(args: dict) -> list[TextContent]:
    """Run backtest on multiple stocks."""
    symbols = args.get("symbols", settings.symbols_list)
    strategy_name = args.get("strategy", "ma_crossover")
    days = args.get("days", 365)

    # Create strategy
    if strategy_name == "ma_crossover":
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

    # Run backtest
    agent = TradingAgent(strategy=strategy, symbols=symbols)
    results = agent.run_backtest_all(days=days)
    agent.close()

    if not results:
        return [TextContent(type="text", text="Failed to backtest symbols")]

    # Format results
    output = f"""
📊 **BACKTEST SUMMARY - ALL SYMBOLS**
Strategy: {strategy_name}
Period: {days} days

| Symbol | Return | Trades | Win Rate | Sharpe | Max DD |
|--------|--------|--------|----------|--------|--------|
"""

    for symbol, r in results.items():
        output += f"| {symbol:<6} | {r['total_return']:>6.2f}% | {r['total_trades']:>6} | {r['win_rate']:>7.2f}% | {r['sharpe_ratio']:>6.2f} | {r['max_drawdown']:>6.2f}% |\n"

    return [TextContent(type="text", text=output)]


async def simulate_trading(args: dict) -> list[TextContent]:
    """Simulate live trading."""
    symbols = args.get("symbols", settings.symbols_list[:2])  # Default to first 2 symbols
    strategy_name = args.get("strategy", "ma_crossover")
    days = args.get("days", 30)

    # Create strategy
    if strategy_name == "ma_crossover":
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

    # Run simulation
    agent = TradingAgent(strategy=strategy, symbols=symbols)
    summary = agent.simulate_live_trading(days=days)
    agent.close()

    output = f"""
🤖 **TRADING SIMULATION RESULTS**
Strategy: {strategy_name}
Symbols: {', '.join(symbols)}
Period: {days} days

💰 **Portfolio Summary:**
- Portfolio Value: ${summary['portfolio_value']:,.2f}
- Cash: ${summary['cash']:,.2f}
- Positions Value: ${summary['positions_value']:,.2f}
- Number of Positions: {summary['num_positions']}

📊 **Performance:**
- Unrealized P&L: ${summary['unrealized_pnl']:,.2f}
- Daily P&L: ${summary['daily_pnl']:,.2f}
- Total P&L: ${summary['total_pnl']:,.2f} ({summary['total_pnl_pct']:.2f}%)

⚠️ **Status:**
- Trading Halted: {'Yes ⛔' if summary['trading_halted'] else 'No ✅'}
"""

    return [TextContent(type="text", text=output)]


async def get_portfolio_status(args: dict) -> list[TextContent]:
    """Get current portfolio status."""
    # This would connect to a persistent agent instance
    # For now, return a sample status
    output = """
📊 **PORTFOLIO STATUS**

💰 **Account:**
- Total Value: $100,000.00
- Cash: $100,000.00
- Positions Value: $0.00

📈 **Positions:**
No open positions

📊 **Performance:**
- Total P&L: $0.00 (0.00%)
- Day P&L: $0.00

Note: This is a demo status. In production, this would show live portfolio data.
"""

    return [TextContent(type="text", text=output)]


async def analyze_fundamentals_tool(args: dict) -> list[TextContent]:
    """Analyze fundamental indicators for a stock."""
    symbol = args["symbol"].upper()

    fi = FundamentalIndicators()
    analysis = fi.get_full_analysis(symbol)

    if not analysis:
        return [TextContent(type="text", text=f"Failed to get fundamentals for {symbol}")]

    fmt = fi.format_number
    val = analysis.get('valuation', {})
    prof = analysis.get('profitability', {})
    health = analysis.get('financial_health', {})
    eps_data = analysis.get('eps', {})
    div = analysis.get('dividends', {})
    risk = analysis.get('risk', {})
    growth = analysis.get('growth', {})
    analyst = analysis.get('analyst', {})
    own = analysis.get('ownership', {})
    val_i = analysis.get('valuation_interpretation', {})
    prof_i = analysis.get('profitability_interpretation', {})
    health_i = analysis.get('health_interpretation', {})

    output = f"""**FUNDAMENTAL ANALYSIS: {symbol} - {analysis.get('name', '')}**
Sector: {analysis.get('sector', 'N/A')} | Industry: {analysis.get('industry', 'N/A')}
Price: ${analysis.get('current_price', 0):.2f} | Market Cap: {fmt(analysis.get('market_cap'), prefix='$')}

**Valuation:**
| Metric | Value | Rating |
|--------|-------|--------|
| PER (trailing) | {val.get('trailing_pe', 0):.2f} | {val_i.get('pe_rating', 'N/A')} |
| PER (forward) | {val.get('forward_pe', 0):.2f} | - |
| PBR (P/B) | {val.get('price_to_book', 0):.2f} | {val_i.get('pb_rating', 'N/A')} |
| PSR (P/S) | {val.get('price_to_sales', 0):.2f} | - |
| PEG Ratio | {val.get('peg_ratio', 0):.2f} | {val_i.get('peg_rating', 'N/A')} |
| EV/EBITDA | {val.get('ev_to_ebitda', 0):.2f} | {val_i.get('ev_ebitda_rating', 'N/A')} |
| EV/Revenue | {val.get('ev_to_revenue', 0):.2f} | - |
| **Overall** | **{val_i.get('overall_score', 0):.1f}/5** | **{val_i.get('overall_rating', 'N/A')}** |

**Profitability:**
| Metric | Value | Rating |
|--------|-------|--------|
| ROE | {prof.get('return_on_equity', 0)*100:.2f}% | {prof_i.get('roe_rating', 'N/A')} |
| ROA | {prof.get('return_on_assets', 0)*100:.2f}% | {prof_i.get('roa_rating', 'N/A')} |
| Gross Margin | {prof.get('gross_margins', 0)*100:.2f}% | - |
| Operating Margin | {prof.get('operating_margins', 0)*100:.2f}% | - |
| Net Margin | {prof.get('profit_margins', 0)*100:.2f}% | {prof_i.get('margin_rating', 'N/A')} |
| EBITDA Margin | {prof.get('ebitda_margins', 0)*100:.2f}% | - |

**EPS:**
- TTM EPS: ${eps_data.get('trailing_eps', 0):.2f}
- Forward EPS: ${eps_data.get('forward_eps', 0):.2f}
- Revenue/Share: ${eps_data.get('revenue_per_share', 0):.2f}

**Growth:**
- Revenue Growth: {growth.get('revenue_growth', 0)*100:.2f}%
- Earnings Growth: {growth.get('earnings_growth', 0)*100:.2f}%
- Quarterly Earnings Growth: {growth.get('quarterly_earnings_growth', 0)*100:.2f}%

**Financial Health:**
| Metric | Value | Rating |
|--------|-------|--------|
| Current Ratio | {health.get('current_ratio', 0):.2f} | {health_i.get('current_ratio_rating', 'N/A')} |
| Quick Ratio | {health.get('quick_ratio', 0):.2f} | - |
| Debt/Equity | {health.get('debt_to_equity', 0):.2f} | {health_i.get('debt_rating', 'N/A')} |
| Total Cash | {fmt(health.get('total_cash'), prefix='$')} | - |
| Total Debt | {fmt(health.get('total_debt'), prefix='$')} | - |
| Free Cash Flow | {fmt(health.get('free_cashflow'), prefix='$')} | {health_i.get('fcf_rating', 'N/A')} |
| Operating CF | {fmt(health.get('operating_cashflow'), prefix='$')} | - |

**Dividends:**
- Yield: {div.get('dividend_yield', 0)*100:.2f}%
- Payout Ratio: {div.get('payout_ratio', 0)*100:.2f}%
- 5Y Avg Yield: {div.get('five_year_avg_yield', 0):.2f}%
- Annual Rate: ${div.get('dividend_rate', 0):.2f}

**Analyst Consensus:**
- Recommendation: **{analyst.get('recommendation', 'N/A').upper()}**
- Target Mean: ${analyst.get('target_mean', 0):.2f}
- Target Range: ${analyst.get('target_low', 0):.2f} - ${analyst.get('target_high', 0):.2f}
- # of Analysts: {analyst.get('num_analysts', 0)}

**Risk:**
- Beta: {risk.get('beta', 0):.3f}
- 52W High: ${risk.get('52_week_high', 0):.2f}
- 52W Low: ${risk.get('52_week_low', 0):.2f}

**Ownership:**
- Insider: {own.get('insider_pct', 0)*100:.2f}%
- Institutional: {own.get('institution_pct', 0)*100:.2f}%
- Short Ratio: {own.get('short_ratio', 0):.2f}
"""

    return [TextContent(type="text", text=output)]


async def compare_fundamentals_tool(args: dict) -> list[TextContent]:
    """Compare fundamentals across multiple stocks."""
    symbols = [s.upper() for s in args["symbols"]]

    fi = FundamentalIndicators()
    comparisons = fi.compare_symbols(symbols)

    if not comparisons:
        return [TextContent(type="text", text="Failed to compare symbols")]

    fmt = fi.format_number

    output = f"""**FUNDAMENTAL COMPARISON**

| Metric | {' | '.join(symbols)} |
|--------|{'|'.join(['--------|' for _ in symbols])}
"""

    # Collect rows of data
    rows = [
        ('Price', lambda d: f"${d.get('current_price', 0):.2f}"),
        ('Market Cap', lambda d: fmt(d.get('market_cap'), prefix='$')),
        ('PER (trailing)', lambda d: f"{d.get('valuation', {}).get('trailing_pe', 0):.1f}"),
        ('PER (forward)', lambda d: f"{d.get('valuation', {}).get('forward_pe', 0):.1f}"),
        ('PBR', lambda d: f"{d.get('valuation', {}).get('price_to_book', 0):.1f}"),
        ('PSR', lambda d: f"{d.get('valuation', {}).get('price_to_sales', 0):.1f}"),
        ('PEG', lambda d: f"{d.get('valuation', {}).get('peg_ratio', 0):.2f}"),
        ('EV/EBITDA', lambda d: f"{d.get('valuation', {}).get('ev_to_ebitda', 0):.1f}"),
        ('ROE', lambda d: f"{d.get('profitability', {}).get('return_on_equity', 0)*100:.1f}%"),
        ('ROA', lambda d: f"{d.get('profitability', {}).get('return_on_assets', 0)*100:.1f}%"),
        ('Gross Margin', lambda d: f"{d.get('profitability', {}).get('gross_margins', 0)*100:.1f}%"),
        ('Net Margin', lambda d: f"{d.get('profitability', {}).get('profit_margins', 0)*100:.1f}%"),
        ('EPS (TTM)', lambda d: f"${d.get('eps', {}).get('trailing_eps', 0):.2f}"),
        ('Revenue Growth', lambda d: f"{d.get('growth', {}).get('revenue_growth', 0)*100:.1f}%"),
        ('Earnings Growth', lambda d: f"{d.get('growth', {}).get('earnings_growth', 0)*100:.1f}%"),
        ('Debt/Equity', lambda d: f"{d.get('financial_health', {}).get('debt_to_equity', 0):.1f}"),
        ('Current Ratio', lambda d: f"{d.get('financial_health', {}).get('current_ratio', 0):.2f}"),
        ('Free Cash Flow', lambda d: fmt(d.get('financial_health', {}).get('free_cashflow'), prefix='$')),
        ('Div Yield', lambda d: f"{d.get('dividends', {}).get('dividend_yield', 0)*100:.2f}%"),
        ('Beta', lambda d: f"{d.get('risk', {}).get('beta', 0):.2f}"),
        ('Recommendation', lambda d: d.get('analyst', {}).get('recommendation', 'N/A').upper()),
        ('Target Price', lambda d: f"${d.get('analyst', {}).get('target_mean', 0):.2f}"),
        ('Valuation', lambda d: d.get('valuation_interpretation', {}).get('overall_rating', 'N/A')),
    ]

    for label, getter in rows:
        values = [getter(comparisons.get(s, {})) for s in symbols]
        output += f"| {label} | {' | '.join(values)} |\n"

    return [TextContent(type="text", text=output)]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
