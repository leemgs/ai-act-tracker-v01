# AI Regulation Sensing (Global AI Policy & Legislation Tracker)

AI 모델 및 제품 출시와 관련하여 각국의 법안, 정책, 가이드라인 등 규제 동향을 추적하고 분석하는 자동화 도구입니다. 최근 3일 내의 규제 관련 소식을 **뉴스(RSS)**에서 수집하여 GitHub Issue와 Slack으로 통합 리포트를 제공합니다. 이를 통해 회사의 AI 제품이 출시 전후에 발생 가능한 법적/정책적 위험을 조기에 파악하고 대응할 수 있도록 돕습니다.

## ✨ 핵심 기능

### 1. 🔍 글로벌 규제 센싱
- **규제 중심 탐색**: AI 기본법, EU AI Act, 저작권 가이드라인, 거버넌스 정책 등 규제 관련 키워드를 중심으로 정보를 수집합니다.
- **다국어 키워드 지원**: 영어 및 한국어 키워드(AI regulation, AI governance, AI 기본법, AI 규제 등)를 활용하여 글로벌 동향을 동시에 파악합니다.
- **지능형 필터링**: `queries.py`에 정의된 정밀한 규제 관련 키워드 조합을 사용하여 관련성 높은 정책/법안 소식만 추출합니다.

### 2. 📊 지능형 강도 분석
- **AI 규제 강도 점수(0~100)**: 규제 조치의 구속력, 처벌 수위, 운영 영향력을 분석하여 점수화하고 시각화(🟢, 🟡, ⚠️, 🔥)합니다.
- **주요 내용 요약**: 기사 본문에서 규제 목적, 적용 대상, 주요 규격 사항을 자동으로 분석하여 제공합니다.
- **출시 리스크 평가**: 법안의 법적 구속력 발생 여부와 제재 수위를 기준으로 제품 출시 전 준비 사항을 식별하도록 돕습니다.

### 3. 🤖 스마트 리포팅 & 중복 제거
- **일자별 통합 이슈**: 매일 하나의 GitHub Issue를 생성하고, 주기적 실행 결과를 댓글로 누적합니다.
- **중복 제거 시스템 (Dedup Summary)**: 당일 첫 실행 결과를 기준으로 새로운 규제 정보(New)와 중복 정보(Dup)를 구분하여 리포트 가독성을 높입니다.
- **Slack 알람**: 중복 제거 요약, 수집 현황, 주요 규제 소식 링크를 포함한 요약을 실시간으로 발송합니다.
- **자동 관리**: 이전 날짜의 열린 이슈를 자동으로 Close 처리하고 최신 이슈로 연결합니다.

## 🛠️ 설정 가이드

### 1. GitHub Secrets (필수)
Repository → Settings → Secrets and variables → Actions → New repository secret

| Name | Description |
|---|---|
| `SLACK_WEBHOOK_URL` | Slack Incoming Webhook URL |
| `GITHUB_OWNER` | Repository 소유자 (예: `leemgs`) |
| `GITHUB_REPO` | Repository 이름 (예: `ai-regulation-tracker-v01`) |
| `GITHUB_TOKEN` | GitHub API 토큰 (`secrets.GITHUB_TOKEN` 사용 가능) |

### 2. GitHub Variables (선택)
| Name | Value (Default) | Description |
|---|---|---|
| `LOOKBACK_DAYS` | `3` | 며칠 전까지의 정보를 수집할지 설정 |
| `ISSUE_TITLE_BASE` | `AI 규제/정책/법안 모니터링` | 생성될 이슈의 기본 제목 |
| `ISSUE_LABEL` | `ai-regulation-monitor` | 이슈에 부여할 라벨 이름 |
| `DEBUG` | `0` | 1 설정 시 상세 실행 로그 출력 |

## 🚀 실행 및 로컬 환경

### GitHub Actions
- **매 시간 정각(UTC)** 자동 실행됩니다.
- `Actions` -> `regulation-monitor` -> `Run workflow`를 통해 수동 실행도 가능합니다.

### 로컬 실행
1. 저장소 클론 및 패키지 설치: `pip install -r requirements.txt`
2. `.env` 파일 생성:
   ```env
   GITHUB_OWNER=your_id
   GITHUB_REPO=your_repo
   GITHUB_TOKEN=your_pat
   SLACK_WEBHOOK_URL=your_url
   DEBUG=1
   ```
3. 실행: `python -m src.run`

## 📊 AI 규제 강도 점수(0~100) 평가 척도

| 항목 | 조건 (주요 키워드) | 점수 |
|---|---|---|
| 법안/규제 직접 명시 | Act, Law, Regulation, 기본법, 법안 등 | +30 |
| 강력한 규제 조치 | Penalty, Fines, Prohibit, 처벌, 금지 등 | +30 |
| 글로벌 규제 프레임워크 | EU AI Act, Governance, 가이드라인 등 | +15 |
| 저작권/IP 관련 규제 | Copyright, Intellectual Property, 저작권 등 | +15 |
| 법적 분쟁 및 규제 조치 | Regulation, Litigation, 소송, 분쟁 등 | +10 |

- **80~100 🔥**: 법적 구속력 발생 및 고강도 제재 (운영 중단 위험)
- **60~79 ⚠️**: 법안 발의 및 정부 차원의 강력 권고/가이드라인
- **40~59 🟡**: 정책 도입 논의 중 및 규제 도입 예고
- **0~39 🟢**: 자율 규제 준수 요청 또는 일반적인 가이드라인

## 📝 참고 사항
- **KST 기준**: 이슈 생성 및 타임스탬프는 한국 표준시(Asia/Seoul)를 기준으로 작동합니다.
- **목적**: 본 도구는 정보를 센싱하여 사전 대응 준비를 돕는 도구이며, 최종 법적 판단은 전문가의 검토가 필요합니다.
- **GitHub Permissions**: Workflow 실행 시 `issues: write` 권한이 필요합니다.

