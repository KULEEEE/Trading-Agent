#!/usr/bin/env python3
"""Test script for MCP server functionality."""

import asyncio
import json
from mcp_server import (
    backtest_stock,
    analyze_stock,
    backtest_multiple,
    simulate_trading
)


async def test_backtest():
    """Test backtest_stock tool."""
    print("\n" + "="*60)
    print("Testing: backtest_stock")
    print("="*60)

    args = {
        "symbol": "AAPL",
        "strategy": "ma_crossover",
        "days": 365
    }

    result = await backtest_stock(args)
    print(result[0].text)


async def test_analyze():
    """Test analyze_stock tool."""
    print("\n" + "="*60)
    print("Testing: analyze_stock")
    print("="*60)

    args = {
        "symbol": "GOOGL",
        "days": 90
    }

    result = await analyze_stock(args)
    print(result[0].text)


async def test_backtest_multiple():
    """Test backtest_multiple tool."""
    print("\n" + "="*60)
    print("Testing: backtest_multiple")
    print("="*60)

    args = {
        "symbols": ["AAPL", "GOOGL", "MSFT"],
        "strategy": "rsi",
        "days": 365
    }

    result = await backtest_multiple(args)
    print(result[0].text)


async def test_simulate():
    """Test simulate_trading tool."""
    print("\n" + "="*60)
    print("Testing: simulate_trading")
    print("="*60)

    args = {
        "symbols": ["AAPL", "GOOGL"],
        "strategy": "ma_crossover",
        "days": 30
    }

    result = await simulate_trading(args)
    print(result[0].text)


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("MCP Server Functionality Test")
    print("="*60)

    tests = [
        ("Backtest Single Stock", test_backtest),
        ("Analyze Stock", test_analyze),
        ("Backtest Multiple Stocks", test_backtest_multiple),
        ("Simulate Trading", test_simulate),
    ]

    for name, test_func in tests:
        try:
            print(f"\n🧪 Running: {name}")
            await test_func()
            print(f"✅ {name} passed")
        except Exception as e:
            print(f"❌ {name} failed: {e}")

    print("\n" + "="*60)
    print("Test Complete!")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
