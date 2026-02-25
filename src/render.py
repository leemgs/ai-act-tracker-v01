from __future__ import annotations
from typing import List

import re
import copy
from .extract import Lawsuit
from .courtlistener import CLDocument, CLCaseSummary
from .utils import debug_log, slugify_case_name

def _esc(s: str) -> str:
    s = str(s or "").strip()
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = s.replace("```", "&#96;&#96;&#96;")
    s = s.replace("~~~", "&#126;&#126;&#126;")
    s = s.replace("|", "\\|")
    s = s.replace("\n", "<br>")
    return s


def _md_sep(col_count: int) -> str:
    return "|" + "---|" * col_count


def _mdlink(label: str, url: str) -> str:
    label = _esc(label)
    url = (url or "").strip()
    if not url:
        return label

    # 이미 Markdown 링크 형식이면 그대로 반환 (이중 방지)
    if url.startswith("[") and "](" in url:
        return url
        
    return f"[{label}]({url})"


def _short(val: str, limit: int = 140) -> str:
    val = val or ""
    if len(val) <= limit:
        return _esc(val)
    return f"<details><summary>내용 펼치기</summary>{_esc(val)}</details>"


# =====================================================
# slug 변환
# =====================================================
def _slugify_case_name(name: str) -> str:
    return slugify_case_name(name)


# =====================================================
# 뉴스 위험도
# =====================================================
def calculate_news_risk_score(title: str, reason: str) -> int:
    score = 0
    text = f"{title or ''} {reason or ''}".lower()

    # 1. 무단 데이터 수집 명시 (+30)
    if any(k in text for k in ["scrape", "crawl", "ingest", "harvest", "mining", "extraction", "bulk", "collection", "robots.txt", "common crawl", "laion", "the pile", "bookcorpus", "unauthorized"]):
        score += 30
    
    # 2. 모델 학습 직접 언급 (+30)
    if any(k in text for k in ["train", "training", "model", "llm", "generative ai", "genai", "gpt", "transformer", "weight", "fine-tune", "diffusion", "inference"]):
        score += 30
    
    # 3. 상업적 사용 (+15)
    if any(k in text for k in ["commercial", "profit", "monetiz", "revenue", "subscription", "enterprise", "paid", "for-profit"]):
        score += 15
    
    # 4. 저작권 관련 (뉴스에서는 Nature of Suit 820 대용으로 키워드 체크) (+15)
    if any(k in text for k in ["copyright", "infringement", "dmca", "fair use", "derivative", "exclusive", "820"]):
        score += 15
        
    # 5. 집단소송 (+10)
    if any(k in text for k in ["class action", "putative class", "representative"]):
        score += 10

    return min(score, 100)


def format_risk(score: int) -> str:
    if score >= 80:
        return f"🔥 {score}"
    if score >= 60:
        return f"⚠️ {score}"
    if score >= 40:
        return f"🟡 {score}"
    return f"🟢 {score}"


# =====================================================
# RECAP 위험도
# =====================================================
def calculate_case_risk_score(case: CLCaseSummary) -> int:
    score = 0
    text = f"{case.extracted_ai_snippet or ''} {case.extracted_causes or ''}".lower()

    # 1. 무단 데이터 수집 명시 (+30)
    if any(k in text for k in ["scrape", "crawl", "ingest", "harvest", "mining", "extraction", "bulk", "collection", "robots.txt", "common crawl", "laion", "the pile", "bookcorpus", "unauthorized"]):
        score += 30
    
    # 2. 모델 학습 직접 언급 (+30)
    if any(k in text for k in ["train", "training", "model", "llm", "generative ai", "genai", "gpt", "transformer", "weight", "fine-tune", "diffusion", "inference"]):
        score += 30
    
    # 3. 상업적 사용 (+15)
    if any(k in text for k in ["commercial", "profit", "monetiz", "revenue", "subscription", "enterprise", "paid", "for-profit"]):
        score += 15
    
    # 4. 저작권 소송 (Nature = 820) (+15)
    # RECAP의 경우 Nature of Suit 코드를 우선하며, 텍스트에서도 저작권 침해 쟁점을 확인합니다.
    if (case.nature_of_suit and "820" in case.nature_of_suit) or any(k in text for k in ["copyright", "infringement", "dmca", "fair use", "derivative", "exclusive"]):
        score += 15
        
    # 5. 집단소송 (+10)
    if any(k in text for k in ["class action", "putative class", "representative"]):
        score += 10

    return min(score, 100)


# =====================================================
# 메인 렌더
# =====================================================
def render_markdown(
    lawsuits: List[Lawsuit],
    cl_docs: List[CLDocument],
    cl_cases: List[CLCaseSummary],
    recap_doc_count: int,
    lookback_days: int = 3,
) -> str:

    lines: List[str] = []

    # KPI (간결 텍스트 요약)
    lines.append(f"## 📊 최근 {lookback_days}일 요약")
    lines.append(f"└ 📰 News: {len(lawsuits)}")

    # 뉴스 테이블
    lines.append("## 📰 News")
    if lawsuits:
        debug_log("'News' is printed.")            
        lines.append("| No. | 기사일자⬇️ | 제목 | 소송번호 | 소송사유 | 위험도 예측 점수 |")
        lines.append(_md_sep(6))

        # 기사일자 기준으로 정렬 (날짜 내림차순, 동일 날짜 시 위험도 내림차순)
        scored_lawsuits = []
        for s in lawsuits:
            risk_score = calculate_news_risk_score(s.article_title or s.case_title, s.reason)
            scored_lawsuits.append((risk_score, s))
        
        scored_lawsuits.sort(key=lambda x: (x[1].update_or_filed_date or "", x[0]), reverse=True)

        for idx, (risk_score, s) in enumerate(scored_lawsuits, start=1):
            article_url = s.article_urls[0] if getattr(s, "article_urls", None) else ""
            title_cell = _mdlink(s.article_title or s.case_title, article_url)

            lines.append(
                f"| {idx} | "
                f"{_esc(s.update_or_filed_date)} | "
                f"{title_cell} | "
                f"{_esc(s.case_number)} | "
                f"{_short(s.reason)} | "
                f"{format_risk(risk_score)} |"
            )
        lines.append("")
    else:
        lines.append("새로운 소식이 0건입니다.\n")

    # 기사 주소
    if lawsuits:
        lines.append("<details>")
        lines.append("<summary><strong><span style=\"font-size:2.5em; font-weight:bold;\">📰 News Website</span></strong></summary>\n")
        for s in lawsuits:
            lines.append(f"### {_esc(s.article_title or s.case_title)}")
            for u in s.article_urls:
                lines.append(f"- {u}")
        lines.append("</details>\n")

    # 위험도 척도
    lines.append("<details>")
    lines.append("<summary><strong><span style=\"font-size:2.5em; font-weight:bold;\">📘 AI 학습 위험도 점수(0~100) 평가 척도</span></strong></summary>\n")
    lines.append("- AI 모델 학습과의 직접성 + 법적 리스크 강도를 수치화한 지표입니다.")
    lines.append("- 0에 가까울수록 → 간접/주변 이슈")
    lines.append("- 100에 가까울수록 → AI 학습 핵심 리스크 사건\n")
    lines.append("")
    
    lines.append("### 📊 등급 기준")
    lines.append("-  0~ 39 🟢 : 간접 연관")
    lines.append("- 40~ 59 🟡 : 학습 쟁점 존재")
    lines.append("- 60~ 79 ⚠️ : 모델 학습 직접 언급")
    lines.append("- 80~100 🔥 : 무단 수집 + 학습 + 상업적 사용 고위험")
    lines.append("")

    lines.append("### 🧮 점수 산정 기준")
    lines.append("| 항목 | 조건 (주요 키워드) | 점수 |")
    lines.append("|---|---|---|")
    lines.append("| 무단 데이터 수집 명시 | scrape, crawl, ingest, unauthorized 등 | +30 |")
    lines.append("| 모델 학습 직접 언급 | train, model, llm, generative ai, gpt 등 | +30 |")
    lines.append("| 상업적 사용 | commercial, profit, monetiz, revenue 등 | +15 |")
    lines.append("| 저작권 소송/쟁점 | Nature=820, copyright, infringement, dmca 등 | +15 |")
    lines.append("| 집단소송 | class action, putative class 등 | +10 |")
    lines.append("")

    lines.append("</details>\n")

    return "\n".join(lines) or ""
