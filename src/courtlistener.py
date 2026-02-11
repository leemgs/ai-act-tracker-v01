from __future__ import annotations

import os
import re
import requests
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta

from .pdf_text import extract_pdf_text
from .complaint_parse import detect_causes, extract_ai_training_snippet, extract_parties_from_caption

BASE = "https://www.courtlistener.com"
SEARCH_URL = BASE + "/api/rest/v4/search/"
DOCKET_URL = BASE + "/api/rest/v4/dockets/{id}/"
DOCKETS_LIST_URL = BASE + "/api/rest/v4/dockets/"
RECAP_DOCS_URL = BASE + "/api/rest/v4/recap-documents/"
PARTIES_URL = BASE + "/api/rest/v4/parties/"
DOCKET_ENTRIES_URL = BASE + "/api/rest/v4/docket-entries/"
COURT_URL = BASE + "/api/rest/v4/courts/{id}/"

COMPLAINT_KEYWORDS = [
    "complaint",
    "amended complaint",
    "petition",
    "class action complaint",
]


# =====================================================
# 🔥 데이터 클래스 (court_short_name, court_api_url 추가)
# =====================================================
@dataclass
class CLDocument:
    docket_id: Optional[int]
    docket_number: str
    case_name: str
    court: str
    date_filed: str
    doc_type: str
    doc_number: str
    description: str
    document_url: str
    pdf_url: str
    pdf_text_snippet: str
    extracted_plaintiff: str
    extracted_defendant: str
    extracted_causes: str
    extracted_ai_snippet: str


@dataclass
class CLCaseSummary:
    docket_id: int
    case_name: str
    docket_number: str
    court: str
    court_short_name: str
    court_api_url: str
    date_filed: str
    status: str
    judge: str
    magistrate: str
    nature_of_suit: str
    cause: str
    parties: str
    complaint_doc_no: str
    complaint_link: str
    recent_updates: str
    extracted_causes: str
    extracted_ai_snippet: str
    docket_candidates: str = ""


# =====================================================
# 🔥 Court short_name 수집
# =====================================================
def fetch_court_metadata(court_id: str) -> tuple[str, str]:
    if not court_id or court_id == "미확인":
        return "미확인", ""

    url = COURT_URL.format(id=court_id)
    try:
        r = requests.get(url, headers=_headers(), timeout=20)
        if r.status_code != 200:
            return court_id, url
        data = r.json()
        short_name = data.get("short_name") or court_id
        return short_name, url
    except Exception:
        return court_id, url


def _headers() -> Dict[str, str]:
    token = os.getenv("COURTLISTENER_TOKEN", "").strip()
    headers = {
        "Accept": "application/json",
        "User-Agent": "ai-lawsuit-monitor/1.1",
    }
    if token:
        headers["Authorization"] = f"Token {token}"
    return headers


def _get(url: str, params: Optional[dict] = None) -> Optional[dict]:
    try:
        r = requests.get(url, params=params, headers=_headers(), timeout=25)
        if r.status_code in (401, 403):
            return None
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def _abs_url(u: str) -> str:
    if not u:
        return ""
    if u.startswith("http"):
        return u
    if u.startswith("/"):
        return BASE + u
    return u


def _safe_str(x) -> str:
    return (str(x).strip() if x is not None else "")


def fetch_docket(docket_id: int) -> Optional[dict]:
    return _get(DOCKET_URL.format(id=docket_id))


def _status_from_docket(docket: dict) -> str:
    term = _safe_str(docket.get("date_terminated") or docket.get("dateTerminated") or "")
    if term:
        return f"종결({term[:10]})"
    return "진행중/미확인"


def _format_parties(parties: List[dict], max_n: int = 12) -> str:
    names = []
    for p in parties[:max_n]:
        nm = _safe_str(p.get("name") or p.get("party_name") or p.get("partyName"))
        typ = _safe_str(p.get("party_type") or p.get("partyType") or p.get("role"))
        if nm:
            names.append(f"{nm}({typ})" if typ else nm)
    if not names:
        return "미확인"
    if len(parties) > max_n:
        names.append("…")
    return "; ".join(names)


# =====================================================
# 🔥 build_case_summary_from_docket_id 수정 반영
# =====================================================
def build_case_summary_from_docket_id(docket_id: int) -> Optional[CLCaseSummary]:
    if not docket_id:
        return None

    docket = fetch_docket(int(docket_id)) or {}

    case_name = _safe_str(docket.get("case_name") or docket.get("caseName")) or "미확인"
    docket_number = _safe_str(docket.get("docket_number") or docket.get("docketNumber")) or "미확인"
    court_id = _safe_str(docket.get("court") or docket.get("court_id") or docket.get("courtId")) or "미확인"

    court_short_name, court_api_url = fetch_court_metadata(court_id)

    date_filed = _safe_str(docket.get("date_filed") or docket.get("dateFiled"))[:10] or "미확인"
    status = _status_from_docket(docket)

    judge = _safe_str(
        docket.get("assigned_to_str")
        or docket.get("assignedToStr")
        or docket.get("assigned_to")
        or docket.get("assignedTo")
    ) or "미확인"

    magistrate = _safe_str(
        docket.get("referred_to_str")
        or docket.get("referredToStr")
        or docket.get("referred_to")
        or docket.get("referredTo")
    ) or "미확인"

    nature_of_suit = _safe_str(docket.get("nature_of_suit") or docket.get("natureOfSuit")) or "미확인"
    cause = _safe_str(docket.get("cause")) or "미확인"

    parties = _format_parties(_get(PARTIES_URL, {"docket": docket_id}) or [])

    return CLCaseSummary(
        docket_id=int(docket_id),
        case_name=case_name,
        docket_number=docket_number,
        court=court_id,
        court_short_name=court_short_name,
        court_api_url=court_api_url,
        date_filed=date_filed,
        status=status,
        judge=judge,
        magistrate=magistrate,
        nature_of_suit=nature_of_suit,
        cause=cause,
        parties=parties,
        complaint_doc_no="미확인",
        complaint_link="",
        recent_updates="미확인",
        extracted_causes="미확인",
        extracted_ai_snippet="",
    )
