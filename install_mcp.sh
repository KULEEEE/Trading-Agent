#!/bin/bash

# MCP Server Installation Script for Trading Agent

echo "========================================="
echo "  Trading Agent MCP Server Installation"
echo "========================================="
echo ""

# Get absolute path of current directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Installation directory: $SCRIPT_DIR"
echo ""

# Step 1: Install Python dependencies
echo "📦 Step 1: Installing Python dependencies..."
pip install -r requirements-mcp.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✅ Dependencies installed"
echo ""

# Step 2: Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Step 2: Creating .env file..."
    cp .env.example .env
    echo "✅ .env file created. Please edit it with your settings."
else
    echo "✅ .env file already exists"
fi
echo ""

# Step 3: Detect Claude Desktop config location
echo "🔍 Step 3: Detecting Claude Desktop config location..."

if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    CONFIG_DIR="$HOME/Library/Application Support/Claude"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    CONFIG_DIR="$HOME/.config/Claude"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    # Windows
    CONFIG_DIR="$APPDATA/Claude"
else
    echo "❌ Unsupported OS: $OSTYPE"
    exit 1
fi

CONFIG_FILE="$CONFIG_DIR/claude_desktop_config.json"
echo "Config location: $CONFIG_FILE"
echo ""

# Step 4: Create config directory if it doesn't exist
if [ ! -d "$CONFIG_DIR" ]; then
    echo "📁 Creating config directory..."
    mkdir -p "$CONFIG_DIR"
fi

# Step 5: Update Claude Desktop config
echo "⚙️  Step 4: Updating Claude Desktop configuration..."

# Determine Python command
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ Python not found. Please install Python 3.11+"
    exit 1
fi

# Create or update config
if [ -f "$CONFIG_FILE" ]; then
    echo "📝 Config file exists. Please manually add the following to $CONFIG_FILE:"
else
    echo "📝 Creating new config file..."
    cat > "$CONFIG_FILE" << EOF
{
  "mcpServers": {
    "trading-agent": {
      "command": "$PYTHON_CMD",
      "args": [
        "$SCRIPT_DIR/mcp_server.py"
      ],
      "env": {
        "PYTHONPATH": "$SCRIPT_DIR"
      }
    }
  }
}
EOF
    echo "✅ Config file created"
fi

echo ""
echo "========================================="
echo "  Installation Complete! 🎉"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file if needed: nano .env"
echo "2. Restart Claude Desktop"
echo "3. Try asking Claude:"
echo "   'AAPL 주식을 백테스팅해줘'"
echo ""
echo "If you already had a config file, add this to your mcpServers:"
echo ""
echo "{
  \"trading-agent\": {
    \"command\": \"$PYTHON_CMD\",
    \"args\": [
      \"$SCRIPT_DIR/mcp_server.py\"
    ],
    \"env\": {
      \"PYTHONPATH\": \"$SCRIPT_DIR\"
    }
  }
}"
echo ""
echo "Config file location: $CONFIG_FILE"
echo ""
