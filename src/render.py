from __future__ import annotations
from typing import List
from .extract import Lawsuit
from .courtlistener import CLDocument, CLCaseSummary

def _esc(s: str) -> str:
    """Escape for GitHub Markdown *table cells*."""
    s = str(s or "").strip()

    # 1) CRLF/CR 정규화
    s = s.replace("\r\n", "\n").replace("\r", "\n")

    # 2) 코드 펜스 무력화
    s = s.replace("```", "&#96;&#96;&#96;")
    s = s.replace("~~~", "&#126;&#126;&#126;")

    # 3) 테이블 셀 안전화 (파이프 기호 및 줄바꿈 처리)
    s = s.replace("|", "\\|")
    s = s.replace("\n", "<br>")
    
    return s

def _md_sep(col_count: int) -> str:
    """Return a valid Markdown table separator row."""
    return "|" + "---| " * col_count

def _mdlink(label: str, url: str) -> str:
    label = _esc(label)
    url = (url or "").strip()
    if not url:
        return label
    return f"[{label}]({url})"

def _details(summary: str, body: str) -> str:
    """Return a GitHub-compatible <details>/<summary> HTML block."""
    summary = _esc(summary)
    # body 내부의 줄바꿈은 이미 _esc에서 <br>로 치환됨
    body = _esc(body)
    if not body or body == "미확인":
        return "미확인"
    # 테이블 파괴를 막기 위해 전체를 한 줄로 결합
    return f"<details><summary>{summary}</summary>{body}</details>"

def render_markdown(lawsuits: List[Lawsuit], cl_docs: List[CLDocument], cl_cases: List[CLCaseSummary], lookback_days: int = 3) -> str:
    lines: List[str] = []

    os = __import__("os")
    show_candidates = os.getenv("SHOW_DOCKET_CANDIDATES", "").strip().lower() in ("1", "true", "yes", "y")
    collapse_cells = os.getenv("COLLAPSE_LONG_CELLS", "").strip().lower() in ("1", "true", "yes", "y")
    collapse_article_urls = os.getenv("COLLAPSE_ARTICLE_URLS", "").strip().lower() in ("1", "true", "yes", "y")

    lines.append(f"## 최근 {lookback_days}일: AI 학습용 무단/불법 데이터 사용 관련 소송/업데이트\n")
    lines.append(f"- 언론보도 기반 수집: {len(lawsuits)}건")
    lines.append(f"- 법원 사건(RECAP 도켓) 확인: {len(cl_cases)}건")
    lines.append(f"- 법원 문서(RECAP Complaint 등) 확보: {len(cl_docs)}건")
    lines.append("")

    if lawsuits:
        lines.append("### 요약 테이블 (뉴스/RSS 기반 정규화)")
        lines.append("| 소송/업데이트 일자 | 소송제목/기사제목 | 소송번호 | 소송이유 | 원고 | 피고 | 국가 | 법원명 | 히스토리 |")
        lines.append(_md_sep(9))
        for s in lawsuits:
            if (s.case_title and s.case_title != "미확인") and (s.article_title and s.article_title != s.case_title):
                display_title = f"{s.case_title} / {s.article_title}"
            elif s.case_title and s.case_title != "미확인":
                display_title = s.case_title
            else:
                display_title = s.article_title or s.case_title
            lines.append(
                f"| {_esc(s.update_or_filed_date)} | {_esc(display_title)} | {_esc(s.case_number)} | {_esc(s.reason)} | {_esc(s.plaintiff)} | {_esc(s.defendant)} | {_esc(s.country)} | {_esc(s.court)} | {_esc(s.history)} |"
            )
    else:
        lines.append("정규화된 소송 테이블을 생성하지 못했습니다.")

    lines.append("\n---\n")

    if cl_cases:
        lines.append("### RECAP 도켓 기반 케이스 요약 (소송번호 확장 필드)")
        
        # 헤더 정의
        base_headers = ["접수일", "상태", "케이스명", "도켓번호"]
        if show_candidates:
            base_headers.append("도켓 후보(Top3)")
        
        base_headers += ["법원", "담당판사", "치안판사", "Nature of Suit", "Cause", "Parties", "Complaint 문서#", "Complaint 링크", "최근 도켓 업데이트(3)", "청구원인(Complaint 추출)", "AI학습 핵심문장(Complaint 추출)"]
        
        lines.append("| " + " | ".join(base_headers) + " |")
        lines.append(_md_sep(len(base_headers)))

        for c in sorted(cl_cases, key=lambda x: x.date_filed, reverse=True)[:25]:
            # 공통 데이터 추출
            row_data = [
                _esc(c.date_filed),
                _esc(c.status),
                _mdlink(c.case_name, f"[https://www.courtlistener.com/docket/](https://www.courtlistener.com/docket/){c.docket_id}/"),
                _esc(c.docket_number)
            ]
            
            if show_candidates:
                cands_val = getattr(c, "docket_candidates", "")
                row_data.append(_details("후보 Top3", cands_val) if (collapse_cells and cands_val) else _esc(cands_val))
            
            # 나머지 데이터 추가 (여기서 순서와 개수가 정확히 맞아야 함)
            row_data += [
                _esc(c.court),
                _esc(c.judge),
                _esc(c.magistrate),
                _esc(c.nature_of_suit),
                _esc(c.cause),
                _esc(c.parties),
                _esc(c.complaint_doc_no),
                _mdlink("Complaint", c.complaint_link),
                (_details("최근 업데이트 3건", getattr(c, "recent_updates", "")) if (collapse_cells and getattr(c, "recent_updates", "")) else _esc(getattr(c, "recent_updates", ""))),
                _esc(c.extracted_causes),
                _esc(c.extracted_ai_snippet)
            ]
            
            lines.append("| " + " | ".join(row_data) + " |")

        lines.append("\n")
    else:
        lines.append("### RECAP 도켓 기반 케이스 요약")
        lines.append("최근 범위 내에서 확인된 RECAP 도켓(사건)이 없습니다.\n")

    if cl_docs:
        lines.append("### RECAP 문서 기반 (Complaint/Petition 우선)")
        lines.append("| 문서 제출일 | 케이스명 | 도켓번호 | 법원 | 문서유형 | 원고(추출) | 피고(추출) | 청구원인(추출) | AI학습 핵심문장(추출) | 문서 링크 |")
        lines.append(_md_sep(10))
        for d in sorted(cl_docs, key=lambda x: x.date_filed, reverse=True)[:20]:
            link = d.document_url or d.pdf_url
            lines.append(
                f"| {_esc(d.date_filed)} | {_esc(d.case_name)} | {_esc(d.docket_number)} | {_esc(d.court)} | {_esc(d.doc_type)} | {_esc(d.extracted_plaintiff)} | {_esc(d.extracted_defendant)} | {_esc(d.extracted_causes)} | {_esc(d.extracted_ai_snippet)} | {_mdlink('Document', link)} |"
            )
        lines.append("\n")

    lines.append("## 기사 주소\n")
    if lawsuits:
        for s in lawsuits:
            if (s.case_title and s.case_title != "미확인") and (s.article_title and s.article_title != s.case_title):
                header_title = f"{s.case_title} / {s.article_title}"
            elif s.case_title and s.case_title != "미확인":
                header_title = s.case_title
            else:
                header_title = s.article_title or s.case_title
            lines.append(f"### {_esc(header_title)} ({_esc(s.case_number)})")
            if collapse_article_urls and s.article_urls:
                lines.append("<details><summary>기사 주소 펼치기</summary>")
                for u in s.article_urls:
                    lines.append(f"- {u}")
                lines.append("</details>")
            else:
                for u in s.article_urls:
                    lines.append(f"- {u}")
            lines.append("")
    
    return "\n".join(lines)
