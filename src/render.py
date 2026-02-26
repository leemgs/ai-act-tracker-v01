from typing import List, Any

import re
import copy
from .extract import RegulationInfo
from .utils import debug_log

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
# 규제 강도 평가 (Intensity Score)
# =====================================================
def calculate_regulation_intensity_score(title: str, reason: str) -> int:
    score = 0
    text = f"{title or ''} {reason or ''}".lower()

    # 1. 법안/규제 직접 명시 (Act, Law, Regulation, 기본법) (+30)
    if any(k in text for k in ["act", "law", "regulation", "bill", "legislation", "규제", "기본법", "법안"]):
        score += 30
    
    # 2. 강력한 규제 조치 (Penalty, Fines, Prohibit, Restriction) (+30)
    if any(k in text for k in ["penalty", "fine", "prohibit", "restriction", "ban", "enforcement", "처벌", "과징금", "금지"]):
        score += 30
    
    # 3. 글로벌 규제 프레임워크 (EU AI Act, Governance, Policy) (+15)
    if any(k in text for k in ["eu ai act", "governance", "policy", "framework", "guideline", "거버넌스", "정책", "가이드라인"]):
        score += 15
    
    # 4. 저작권 및 지식재산권 관련 규제 (+15)
    if any(k in text for k in ["copyright", "intellectual property", "ip", "infringement", "저작권", "지식재산권"]):
        score += 15
        
    # 5. 법적 분쟁 및 규제 조치 (+10)
    if any(k in text for k in ["regulation", "litigation", "legal", "dispute", "소송", "분쟁", "규제"]):
        score += 10

    return min(score, 100)


def format_intensity(score: int) -> str:
    if score >= 80:
        return f"🔥 {score}"
    if score >= 60:
        return f"⚠️ {score}"
    if score >= 40:
        return f"🟡 {score}"
    return f"🟢 {score}"



# =====================================================
# 메인 렌더
# =====================================================
def render_markdown(
    regulations: List[RegulationInfo],
    lookback_days: int = 3,
) -> str:

    lines: List[str] = []

    # KPI (간결 텍스트 요약)
    lines.append(f"## 📊 최근 {lookback_days}일 규제 동향 요약")
    lines.append(f"└ 📰 News: {len(regulations)}")

    # 뉴스 테이블
    lines.append("## 📰 AI Regulation News")
    if regulations:
        debug_log("'News' is printed.")            
        lines.append("| No. | 기사일자⬇️ | 국가 | 제목 | 조건 (주요 키워드) | 주요 내용 | 규제 강도 점수 |")
        lines.append(_md_sep(7))

        # 기사일자 기준으로 정렬 (날짜 내림차순, 동일 날짜 시 강도 내림차순)
        scored_regulations = []
        for s in regulations:
            intensity_score = calculate_regulation_intensity_score(s.article_title or s.case_title, s.reason)
            scored_regulations.append((intensity_score, s))
        
        scored_regulations.sort(key=lambda x: (x[1].update_or_filed_date or "", x[0]), reverse=True)

        for idx, item_tuple in enumerate(scored_regulations, start=1):
            intensity_score, s = item_tuple
            article_url = s.article_urls[0] if getattr(s, "article_urls", None) else ""
            title_cell = _mdlink(s.article_title or s.case_title, article_url)

            lines.append(
                f"| {idx} | "
                f"{_esc(s.update_or_filed_date)} | "
                f"{_esc(s.country)} | "
                f"{title_cell} | "
                f"{_esc(s.matched_keywords)} | "
                f"{_short(s.reason)} | "
                f"{format_intensity(intensity_score)} |"
            )
        lines.append("")
    else:
        lines.append("새로운 규제 소식이 0건입니다.\n")

    # 기사 주소
    if regulations:
        lines.append("<details>")
        lines.append("<summary><strong><span style=\"font-size:2.5em; font-weight:bold;\">📰 Source Articles</span></strong></summary>\n")
        for s in regulations:
            lines.append(f"### {_esc(s.article_title or s.case_title)}")
            for u in s.article_urls:
                lines.append(f"- {u}")
        lines.append("</details>\n")

    # 규제 강도 척도
    lines.append("<details>")
    lines.append("<summary><strong><span style=\"font-size:2.5em; font-weight:bold;\">📘 AI 규제 강도 점수(0~100) 평가 척도</span></strong></summary>\n")
    lines.append("- AI 제품 출시 및 운영에 미치는 규제적 영향력과 법적 구속력을 수치화한 지표입니다.")
    lines.append("- 0에 가까울수록 → 권고/가이드라인 위주")
    lines.append("- 100에 가까울수록 → 법적 처벌 및 운영 금지 등 고강도 규제\n")
    lines.append("")
    
    lines.append("### 📊 등급 기준")
    lines.append("-  0~ 39 🟢 : 자율 규제/가이드라인")
    lines.append("- 40~ 59 🟡 : 정책 도입 논의 중")
    lines.append("- 60~ 79 ⚠️ : 법안 발의 및 강력 권고")
    lines.append("- 80~100 🔥 : 법적 구속력 발생 및 고강도 제재")
    lines.append("")

    lines.append("### 🧮 점수 산정 기준")
    lines.append("| 항목 | 조건 (주요 키워드) | 점수 |")
    lines.append("|---|---|---|")
    lines.append("| 법안/규제 직접 명시 | Act, Law, Regulation, 기본법 등 | +30 |")
    lines.append("| 강력한 규제 조치 | Penalty, Fines, Prohibit, 금지 등 | +30 |")
    lines.append("| 글로벌 규제 프레임워크 | EU AI Act, Governance, 가이드라인 등 | +15 |")
    lines.append("| 저작권/IP 관련 규제 | Copyright, Intellectual Property, 저작권 등 | +15 |")
    lines.append("| 법적 분쟁 및 규제 조치 | Regulation, Litigation, 소송 등 | +10 |")
    lines.append("")

    lines.append("</details>\n")

    return "\n".join(lines) or ""
