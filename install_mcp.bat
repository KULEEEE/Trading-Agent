@echo off
REM MCP Server Installation Script for Trading Agent (Windows)

echo =========================================
echo   Trading Agent MCP Server Installation
echo =========================================
echo.

REM Get current directory
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

echo Installation directory: %SCRIPT_DIR%
echo.

REM Step 1: Install Python dependencies
echo Step 1: Installing Python dependencies...
pip install -r requirements-mcp.txt

if %errorlevel% neq 0 (
    echo Failed to install dependencies
    pause
    exit /b 1
)

echo Dependencies installed
echo.

REM Step 2: Create .env file if it doesn't exist
if not exist .env (
    echo Step 2: Creating .env file...
    copy .env.example .env
    echo .env file created. Please edit it with your settings.
) else (
    echo .env file already exists
)
echo.

REM Step 3: Detect Claude Desktop config location
echo Step 3: Detecting Claude Desktop config location...
set "CONFIG_DIR=%APPDATA%\Claude"
set "CONFIG_FILE=%CONFIG_DIR%\claude_desktop_config.json"

echo Config location: %CONFIG_FILE%
echo.

REM Step 4: Create config directory if it doesn't exist
if not exist "%CONFIG_DIR%" (
    echo Creating config directory...
    mkdir "%CONFIG_DIR%"
)

REM Step 5: Detect Python command
where python3 >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_CMD=python3"
) else (
    where python >nul 2>&1
    if %errorlevel% equ 0 (
        set "PYTHON_CMD=python"
    ) else (
        echo Python not found. Please install Python 3.11+
        pause
        exit /b 1
    )
)

REM Convert backslashes to forward slashes for JSON
set "SCRIPT_DIR_JSON=%SCRIPT_DIR:\=/%"

REM Step 6: Create or update config
echo Step 4: Updating Claude Desktop configuration...

if exist "%CONFIG_FILE%" (
    echo Config file exists. Please manually add the following to:
    echo %CONFIG_FILE%
    echo.
    echo {
    echo   "trading-agent": {
    echo     "command": "%PYTHON_CMD%",
    echo     "args": [
    echo       "%SCRIPT_DIR_JSON%/mcp_server.py"
    echo     ],
    echo     "env": {
    echo       "PYTHONPATH": "%SCRIPT_DIR_JSON%"
    echo     }
    echo   }
    echo }
) else (
    echo Creating new config file...
    (
        echo {
        echo   "mcpServers": {
        echo     "trading-agent": {
        echo       "command": "%PYTHON_CMD%",
        echo       "args": [
        echo         "%SCRIPT_DIR_JSON%/mcp_server.py"
        echo       ],
        echo       "env": {
        echo         "PYTHONPATH": "%SCRIPT_DIR_JSON%"
        echo       }
        echo     }
        echo   }
        echo }
    ) > "%CONFIG_FILE%"
    echo Config file created
)

echo.
echo =========================================
echo   Installation Complete!
echo =========================================
echo.
echo Next steps:
echo 1. Edit .env file if needed
echo 2. Restart Claude Desktop
echo 3. Try asking Claude:
echo    "AAPL 주식을 백테스팅해줘"
echo.
echo Config file location: %CONFIG_FILE%
echo.

pause
