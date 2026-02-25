# Trading Agent MCP Server

Claude Code에서 사용 가능한 주식 트레이딩 에이전트 MCP 서버입니다.

## 🎯 기능

Claude와 대화하면서 다음 기능을 사용할 수 있습니다:

- **📊 백테스팅**: 과거 데이터로 트레이딩 전략 성능 검증
- **📈 기술적 분석**: 주식의 기술적 지표 분석 및 매매 신호 생성
- **🤖 트레이딩 시뮬레이션**: 실시간 트레이딩 시뮬레이션
- **📊 포트폴리오 관리**: 포트폴리오 현황 확인

## 🚀 설치 방법

### 1. 의존성 설치

```bash
cd C:\Project\Trading-Agent
pip install -r requirements-mcp.txt
```

### 2. Claude Desktop 설정

Claude Desktop의 설정 파일을 엽니다:

**Windows:**
```
%APPDATA%\Claude\claude_desktop_config.json
```

**macOS:**
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Linux:**
```
~/.config/Claude/claude_desktop_config.json
```

### 3. MCP 서버 추가

설정 파일에 다음을 추가합니다:

```json
{
  "mcpServers": {
    "trading-agent": {
      "command": "python3",
      "args": [
        "C:/Project/Trading-Agent/mcp_server.py"
      ],
      "env": {
        "PYTHONPATH": "C:/Project/Trading-Agent"
      }
    }
  }
}
```

**주의:** 경로를 실제 프로젝트 위치로 변경하세요!

### 4. .env 파일 설정

```bash
cp .env.example .env
# .env 파일을 편집하여 원하는 설정 입력
```

### 5. Claude Desktop 재시작

Claude Desktop을 완전히 종료하고 다시 실행합니다.

## 💬 사용 방법

Claude Desktop을 열고 다음과 같이 대화하세요:

### 예제 1: 주식 백테스팅

```
"AAPL 주식을 1년간 백테스팅해줘"
```

또는

```
"애플 주식에 MA Crossover 전략으로 백테스트 실행해줘"
```

### 예제 2: 기술적 분석

```
"GOOGL 주식을 분석해줘"
```

또는

```
"구글 주식의 현재 RSI, MACD 지표 알려줘"
```

### 예제 3: 여러 종목 비교

```
"AAPL, GOOGL, MSFT를 RSI 전략으로 백테스트하고 비교해줘"
```

### 예제 4: 트레이딩 시뮬레이션

```
"TSLA로 30일간 트레이딩 시뮬레이션 해줘"
```

## 🛠️ 사용 가능한 도구들

Claude가 자동으로 적절한 도구를 선택하지만, 직접 지정할 수도 있습니다:

### 1. `backtest_stock`
단일 종목 백테스팅
- **입력**: symbol (종목), strategy (전략), days (기간)
- **출력**: 수익률, 거래 통계, 리스크 지표

### 2. `analyze_stock`
기술적 분석
- **입력**: symbol (종목), days (분석 기간)
- **출력**: 이동평균, RSI, MACD, 볼린저밴드, 매매 신호

### 3. `backtest_multiple`
여러 종목 백테스팅 및 비교
- **입력**: symbols (종목 리스트), strategy (전략), days (기간)
- **출력**: 종목별 성과 비교 표

### 4. `simulate_trading`
실시간 트레이딩 시뮬레이션
- **입력**: symbols (종목 리스트), strategy (전략), days (기간)
- **출력**: 포트폴리오 현황, 손익

### 5. `get_portfolio_status`
현재 포트폴리오 상태 조회
- **입력**: 없음
- **출력**: 보유 포지션, 현금, 수익률

## 📋 지원 전략

1. **MA Crossover** (`ma_crossover`)
   - 이동평균선 교차 전략
   - 단기 MA(20일)가 장기 MA(50일)를 상향 돌파 시 매수

2. **RSI** (`rsi`)
   - RSI 지표 기반 전략
   - RSI < 30: 과매도 (매수)
   - RSI > 70: 과매수 (매도)

## 🎨 응답 예시

```
📊 BACKTEST RESULTS: AAPL
Strategy: MA_Crossover_20_50
Period: 365 days

💰 Performance:
- Initial Capital: $100,000.00
- Final Capital: $115,234.50
- Total Return: 15.23%

📈 Trading Stats:
- Total Trades: 12
- Win Rate: 66.67%
- Average Win: $2,345.67
- Average Loss: $-1,234.56
- Profit Factor: 1.89

📉 Risk Metrics:
- Sharpe Ratio: 1.45
- Max Drawdown: -8.34%
```

## 🔧 문제 해결

### "MCP 서버가 연결되지 않습니다"

1. 경로가 올바른지 확인
2. Python이 설치되어 있는지 확인
3. 의존성이 설치되어 있는지 확인
4. Claude Desktop 로그 확인

### "도구를 찾을 수 없습니다"

1. `requirements-mcp.txt`의 모든 패키지가 설치되었는지 확인
2. `.env` 파일이 올바르게 설정되었는지 확인

### 로그 확인

로그는 `logs/` 디렉토리에 저장됩니다:
- `trading_agent_YYYY-MM-DD.log`: 전체 로그
- `errors_YYYY-MM-DD.log`: 에러 로그만

## 🌟 고급 사용법

### 설정 커스터마이징

`.env` 파일에서 다음을 변경할 수 있습니다:

```env
# 기본 종목
DEFAULT_SYMBOLS=AAPL,GOOGL,MSFT,TSLA,NVDA

# 초기 자본금
INITIAL_CAPITAL=100000

# 포지션 크기 (자본금의 %)
POSITION_SIZE_PCT=0.1

# 손절 비율
STOP_LOSS_PCT=0.05

# 익절 비율
TAKE_PROFIT_PCT=0.15
```

### 새로운 전략 추가

`src/strategies/` 디렉토리에 새로운 전략을 추가할 수 있습니다.
`BaseStrategy`를 상속받아 구현하세요.

## 📚 추가 문서

- [메인 README](README.md): 전체 프로젝트 문서
- [Docker 배포](docker-compose.yml): Docker로 배포하기
- [예제 코드](example.py): Python 직접 사용 예제

## 🤝 기여

버그 리포트 및 기능 제안은 GitHub Issues에 올려주세요.

## 📄 라이선스

MIT License
