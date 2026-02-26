from __future__ import annotations
import re
import requests
import yaml
from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import List, Dict, Any
from datetime import datetime, timezone, timedelta
from .utils import debug_log

@dataclass
class RegulationInfo:
    update_or_filed_date: str
    country: str  # 추가: 규제 대상 국가
    # case_title: 법안/규제명 또는 관련 기관/국가
    case_title: str
    # article_title: RSS/기사 원문 제목
    article_title: str
    case_number: str
    reason: str
    article_urls: List[str]
    matched_keywords: str = ""


def fetch_page_text(url: str, timeout: int = 15) -> tuple[str, str]:
    """기사 페이지 텍스트를 가져오고 (텍스트, 최종URL)을 반환한다."""
    try:
        r = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"}, allow_redirects=True)
        r.raise_for_status()
        final_url = (r.url or url).strip()
        soup = BeautifulSoup(r.text, "lxml")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        text = soup.get_text("\n")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text[:20000], final_url
    except Exception as e:
        debug_log(f"fetch_page_text failed: {url}, error: {e}")
        return "", url

def load_known_cases(path: str = "data/known_cases.yml") -> List[Dict[str, Any]]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or []
    except FileNotFoundError:
        return []

def enrich_from_known(text: str, title: str, known: List[Dict[str, Any]]) -> Dict[str, str]:
    hay = (title + "\n" + text).lower()
    for entry in known:
        any_terms = [t.lower() for t in entry.get("match", {}).get("any", [])]
        if any_terms and any(term in hay for term in any_terms):
            return entry.get("enrich", {}) or {}
    return {}

def extract_country(text: str, title: str) -> str:
    """본문 또는 제목에서 국가 정보를 추정한다."""
    text_to_search = (title + " " + text).lower()
    
    mapping = {
        "대한민국": ["korea", "republic of korea", "south korea", "대한민국", "한국"],
        "미국": ["usa", "united states", "u.s.", "u.s.a", "미국", "미 연방"],
        "EU": ["eu ", "european union", "유럽연합", "브뤼셀", "유럽"],
        "영국": ["uk ", "united kingdom", "영국", "런던"],
        "중국": ["china", "중국", "베이징"],
        "일본": ["japan", "일본", "도쿄"],
        "캐나다": ["canada", "캐나다"],
        "인도": ["india", "인도"],
        "프랑스": ["france", "프랑스", "파리"],
        "독일": ["germany", "독일", "베를린"],
        "글로벌": ["global", "international", "글로벌", "국제"]
    }
    
    for country, keywords in mapping.items():
        if any(k in text_to_search for k in keywords):
            return country
            
    return "기타"

def extract_regulation_subject(text: str, title: str) -> str:
    """본문 또는 제목에서 규제 대상(국가, 법안명 등)을 추정한다."""
    text_to_search = (title + " " + text).lower()
    
    if "eu ai act" in text_to_search or "유럽연합" in text_to_search or "european union" in text_to_search:
        return "EU AI Act"
    if "기본법" in text_to_search or "대한민국" in text_to_search or "korea" in text_to_search:
        return "AI 기본법 (KR)"
    if "copyright" in text_to_search or "저작권" in text_to_search:
        return "AI 저작권 가이드라인"
    if "california" in text_to_search or "sb 1047" in text_to_search:
        return "California AI Safety Bill"
    
    return "국내외 규제 동향"

def reason_heuristic(hay: str) -> str:
    h = hay.lower()
    if "copyright" in h or "저작권" in h:
        return "AI 학습 데이터에 대한 저작권 가이드라인 또는 지식재산권 보호 조치 관련 정보."
    if "governance" in h or "policy" in h or "거버넌스" in h or "정책" in h:
        return "AI 윤리 준수 및 거버넌스 체계 구축을 위한 정책 가이드라인 또는 규제 프레임워크."
    if "ai act" in h or "eu" in h:
        return "EU AI Act 또는 이에 준하는 고강도 AI 규제 법안의 진척 및 대응 필요 사항."
    return "국내외 AI 규제 법제화, 가이드라인 배포 및 정책 동향 관련 최신 정보."

def build_regulations_from_news(news_items, known_cases, lookback_days: int = 3) -> List[RegulationInfo]:
    results: List[RegulationInfo] = []
    debug_log(f"build_regulations_from_news items={len(news_items)} lookback={lookback_days}")
    cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)
    for item in news_items:
        if item.published_at and item.published_at < cutoff:
            continue
        text, final_url = fetch_page_text(item.url)
        if not text:
            continue

        hay = (item.title + " " + text)
        lower = hay.lower()
        keywords = [
            "regulation", "governance", "act", "policy", "bill", "copyright", "dispute", "legal", 
            "intellectual property", "framework", "safety summit", "guideline", "ethics",
            "규제", "거버넌스", "기본법", "정책", "가이드라인", "저작권", "책임법", "윤리", "지식재산권"
        ]
        found = [k for k in keywords if k.lower() in lower]
        if not found:
            debug_log(f"Skipped non-relevant news: {item.title[:60]}...")
            continue
        matched_str = ", ".join(found)

        enrich = enrich_from_known(text, item.title, known_cases)

        # 규제명/대상 추출
        article_title = item.title
        country = enrich.get("country") or extract_country(text, article_title)
        case_title = enrich.get("case_title") or extract_regulation_subject(text, article_title)
        case_number = enrich.get("case_number") or "N/A"

        published = item.published_at or datetime.now(timezone.utc)
        update_date = published.date().isoformat()

        results.append(
            RegulationInfo(
                update_or_filed_date=update_date,
                country=country,
                case_title=case_title,
                article_title=article_title,
                case_number=case_number,
                reason=enrich.get("reason", reason_heuristic(hay)),
                article_urls=sorted(list({final_url, item.url})),
                matched_keywords=matched_str
            )
        )

    # 병합
    merged: Dict[tuple[str, str, str, str], RegulationInfo] = {}
    for r in results:
        key = (r.case_number, r.country, r.case_title, r.article_title)
        if key not in merged:
            merged[key] = r
        else:
            merged[key].article_urls = sorted(list(set(merged[key].article_urls + r.article_urls)))
            if r.update_or_filed_date > merged[key].update_or_filed_date:
                merged[key].update_or_filed_date = r.update_or_filed_date
            # 키워드 병합
            k1 = [x.strip() for x in merged[key].matched_keywords.split(",") if x.strip()]
            k2 = [x.strip() for x in r.matched_keywords.split(",") if x.strip()]
            merged[key].matched_keywords = ", ".join(sorted(list(set(k1 + k2))))

    return list(merged.values())