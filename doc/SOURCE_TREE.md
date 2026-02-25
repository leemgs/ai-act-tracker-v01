좋아요, 전체 구조를 **트리 형태 + 각 파일 역할 설명**으로 정리해드릴게요.
(현재 레포지토리 `ai-regulation-tracker-v01` 기준)

---

# 📁 프로젝트 구조 설명

```text
ai-regulation-tracker-v01
├── .github/
│   └── workflows/
│       └── hourly.yml
├── .env.example
├── .gitignore
├── README.md
├── create_pr.py
├── requirements.txt
├── data/
│   └── known_cases.yml
├── doc/
│   └── SOURCE_TREE.md
├── src/
│   ├── __init__.py
│   ├── dedup.py
│   ├── extract.py
│   ├── fetch.py
│   ├── github_issue.py
│   ├── queries.py
│   ├── render.py
│   ├── run.py
│   ├── slack.py
│   └── utils.py
└── test/
```

---

## 🔧 루트 레벨

### `.github/workflows/hourly.yml`

* GitHub Actions 워크플로 파일
* 이 프로젝트를 **1시간마다 자동 실행**
* 실행 내용:
  1. Python 환경 세팅
  2. 의존성 설치
  3. `python -m src.run` 실행
  4. 결과를 GitHub Issue + Slack으로 전송

---

### `.env.example`

* 환경 변수 설정을 위한 예시 파일
* `GITHUB_TOKEN`, `SLACK_WEBHOOK_URL` 등 필수 API 토큰과 `LOOKBACK_DAYS`, `DEBUG` 등 부가 설정 포함

---

### `README.md`

* 프로젝트 개요 및 사용 방법 설명 문서
* 수집 데이터, 주요 기능(규제 강도 점수 등), 실행 방법 정리

---

### `create_pr.py`

* 변경 사항을 바탕으로 브랜치 생성 및 Pull Request를 자동화하는 스크립트

---

### `requirements.txt`

* Python 의존 라이브러리 목록 (`feedparser`, `requests`, `python-dateutil` 등)

---

### `data/known_cases.yml`

* 이미 알려진 규제 케이스 또는 예외 처리를 위한 데이터 파일

---

### `doc/SOURCE_TREE.md`

* 현재 보고 계신 프로젝트 구조 및 파일 역할 정의 문서

### `test/`

* API 연동 테스트 및 기능 검증을 위한 테스트 스크립트들이 포함된 폴더

---

## 🧠 핵심 로직: `src/` 폴더

시스템의 주요 기능을 담당하는 소스 코드 폴더입니다.

---

### `run.py` ⭐ **엔트리포인트 (가장 중요)**

* 전체 파이프라인을 오케스트레이션하는 메인 모듈
* 하는 일:
  1. 뉴스 수집 (`fetch_news`)
  2. 규제 정보 추출 및 정제 (`build_regulations_from_news`)
  3. Markdown 리포트 생성 (`render_markdown`)
  4. 중복 제거 (`apply_deduplication`)
  5. GitHub Issue 생성/업데이트 및 Slack 알림 전송

---

### `queries.py`

* 뉴스 검색에 사용할 **검색 쿼리(키워드)** 정의
* 예: AI regulation, AI governance, AI copyright, AI 기본법 등

---

### `fetch.py`

* Google News RSS 등을 통해 최신 규제 관련 뉴스를 가져오는 모듈

---

### `extract.py`

* 수집된 뉴스 데이터에서 규제 강도 점수를 계산하고 필요한 정보를 추출하는 로직

---

### `render.py`

* 분석 결과를 GitHub Issue에 게시할 **Markdown 테이블 형태로 렌더링**

---

### `dedup.py`

* GitHub Issue의 기존 댓글과 비교하여 중복된 정보를 필터링하는 로직

---

### `github_issue.py`

* GitHub API와 연동하여 이슈 생성, 조회, 댓글 작성 및 이전 이슈 Close 담당

---

### `slack.py`

* 분석 결과 요약을 Slack Webhook으로 전송

---

### `utils.py`

* 프로젝트 공통 유틸리티 (예: `DEBUG` 환경 변수에 따른 `debug_log` 등)

---

### `__init__.py`

* Python 패키지 인식용 파일

---

# 🧭 전체 흐름 요약

```text
GitHub Actions (hourly.yml)
        ↓
python -m src.run
        ↓
[queries] 검색 키워드 정의
        ↓
[fetch] 최신 규제 뉴스 수집
        ↓
[extract] 규제 강도 분석 및 정보 추출
        ↓
[render] Markdown 리포트 생성
        ↓
[dedup] 기존 리포트와 대조하여 중복 제거
        ↓
[github_issue] GitHub 이슈/댓글 업데이트
        ↓
[slack] 주요 요약 Slack 전송
```

