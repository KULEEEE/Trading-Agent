# Trading Agent MCP Server

Claude Code/Desktop에서 자연어로 주식 분석, 백테스팅, 트레이딩 시뮬레이션을 할 수 있는 MCP 서버입니다.

## 작동 원리

```
사용자 <-> Claude Code/Desktop <-> MCP 프로토콜 <-> Trading Agent 서버 <-> Yahoo Finance API
```

**MCP(Model Context Protocol)** 는 Claude가 외부 도구를 사용할 수 있게 해주는 프로토콜입니다.
이 프로젝트는 MCP 서버로 동작하며, Claude가 주식 데이터를 가져오고 분석하는 도구들을 호출할 수 있게 합니다.

### 프로젝트 구조

```
Trading-Agent/
├── mcp_server.py              # MCP 서버 진입점 (Claude와 통신)
├── src/
│   ├── agent/                 # 트레이딩 에이전트 코어
│   ├── api/                   # Yahoo Finance API 클라이언트
│   ├── backtest/              # 백테스팅 엔진
│   ├── indicators/            # 기술적/펀더멘털 지표 계산
│   ├── strategies/            # 트레이딩 전략 (MA Crossover, RSI)
│   ├── risk/                  # 리스크 관리
│   ├── data/                  # 데이터 관리 및 DB
│   ├── monitoring/            # 모니터링
│   └── utils/                 # 설정, 로거
├── requirements.txt           # Python 핵심 의존성
├── requirements-mcp.txt       # MCP 서버 의존성
├── .env.example               # 환경변수 템플릿
├── Dockerfile                 # Docker 배포용
└── docker-compose.yml         # Docker Compose 설정
```

### 제공 기능

| 도구 | 설명 |
|------|------|
| `analyze_stock` | 기술적 분석 (RSI, MACD, 볼린저밴드, 매매신호) |
| `analyze_fundamentals` | 펀더멘털 분석 (PER, PBR, ROE, 배당 등) |
| `compare_fundamentals` | 여러 종목 펀더멘털 비교 |
| `backtest_stock` | 단일 종목 백테스팅 |
| `backtest_multiple` | 다중 종목 백테스팅 비교 |
| `simulate_trading` | 트레이딩 시뮬레이션 |
| `get_portfolio_status` | 포트폴리오 현황 조회 |

## 설치 방법

### 사전 요구사항

- **Python 3.11+**
- **Claude Code** 또는 **Claude Desktop**

### 1단계: 프로젝트 다운로드

```bash
git clone https://github.com/KULEEEE/Trading-Agent.git
cd Trading-Agent
```

### 2단계: 가상환경 생성 및 의존성 설치

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-mcp.txt
```

**Mac/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-mcp.txt
```

### 3단계: 환경변수 설정

```bash
cp .env.example .env
```

`.env` 파일을 열어 원하는 설정을 수정합니다 (기본값으로도 동작합니다):

```env
DEFAULT_SYMBOLS=AAPL,GOOGL,MSFT,TSLA    # 기본 종목
INITIAL_CAPITAL=100000                    # 초기 자본금
STOP_LOSS_PCT=0.05                        # 손절 비율 (5%)
TAKE_PROFIT_PCT=0.15                      # 익절 비율 (15%)
```

### 4단계: MCP 서버 연결

Claude Code 또는 Claude Desktop에 MCP 서버를 등록합니다.

#### Claude Code 사용 시

프로젝트 루트에 `.mcp.json` 파일을 생성합니다:

```json
{
  "mcpServers": {
    "trading-agent": {
      "type": "stdio",
      "command": "<프로젝트 경로>/.venv/Scripts/python.exe",
      "args": ["<프로젝트 경로>/mcp_server.py"],
      "env": {
        "PYTHONPATH": "<프로젝트 경로>",
        "PYTHONUTF8": "1"
      }
    }
  }
}
```

> `<프로젝트 경로>`를 실제 절대 경로로 바꿔주세요.
> Mac/Linux는 `python.exe` 대신 `.venv/bin/python`을 사용합니다.

#### Claude Desktop 사용 시

설정 파일을 열어 수정합니다:

- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **Mac:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux:** `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "trading-agent": {
      "command": "python",
      "args": ["<프로젝트 경로>/mcp_server.py"],
      "env": {
        "PYTHONPATH": "<프로젝트 경로>"
      }
    }
  }
}
```

### 5단계: 재시작

Claude Code 또는 Claude Desktop을 재시작하면 Trading Agent 도구를 사용할 수 있습니다.

## 사용 예시

Claude에게 자연어로 말하면 됩니다:

```
"애플 주식 기술적 분석해줘"
"삼성전자 하이닉스 펀더멘털 비교해줘"
"NVDA를 MA Crossover 전략으로 1년간 백테스트해줘"
"TSLA로 30일 트레이딩 시뮬레이션 해봐"
"AAPL, GOOGL, MSFT 비교 백테스팅 해줘"
```

## 지원 전략

| 전략 | 키워드 | 설명 |
|------|--------|------|
| MA Crossover | `ma_crossover` | 단기(20일)/장기(50일) 이동평균선 교차 시 매매 |
| RSI | `rsi` | RSI 30 이하 매수, 70 이상 매도 |

## Docker로 실행 (선택)

```bash
cp .env.example .env
docker-compose up --build
```

## 문제 해결

| 증상 | 해결 방법 |
|------|----------|
| MCP 서버 연결 안 됨 | `.mcp.json`의 경로가 정확한지, python 경로가 가상환경 내 경로인지 확인 |
| 도구를 찾을 수 없음 | `pip install -r requirements-mcp.txt` 재실행 |
| 한글 깨짐 | `env`에 `"PYTHONUTF8": "1"` 추가 |
| 데이터 없음 | 인터넷 연결 확인, Yahoo Finance 접근 가능한지 확인 |

로그는 `logs/` 디렉토리에서 확인할 수 있습니다.

## 라이선스

MIT License
