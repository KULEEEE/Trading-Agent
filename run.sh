#!/bin/bash

# Trading Agent Run Script

MODE=${1:-backtest}
STRATEGY=${2:-ma_cross}
SYMBOL=${3:-}
DAYS=${4:-365}

echo "========================================="
echo "  Trading Agent"
echo "========================================="
echo "Mode:     $MODE"
echo "Strategy: $STRATEGY"
if [ -n "$SYMBOL" ]; then
    echo "Symbol:   $SYMBOL"
fi
echo "Days:     $DAYS"
echo "========================================="
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate || . venv/Scripts/activate
fi

# Build command
CMD="python src/agent/main.py --mode $MODE --strategy $STRATEGY --days $DAYS"

if [ -n "$SYMBOL" ]; then
    CMD="$CMD --symbol $SYMBOL"
fi

# Run the command
$CMD
