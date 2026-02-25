from __future__ import annotations
import requests
from typing import Dict

def _headers(token: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

def find_or_create_issue(owner: str, repo: str, token: str, title: str, label: str) -> int:
    url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    r = requests.get(url, headers=_headers(token), params={"state": "open", "labels": label, "per_page": 50}, timeout=20)
    r.raise_for_status()
    issues = r.json()
    for it in issues:
        if it.get("title") == title:
            return int(it["number"])
    payload = {
        "title": title,
        "body": (
            "## 📋 AI 규제/정책/법안 자동 수집 리포트\n\n"
            "이 이슈에는 AI 관련 각국의 법안, 정책, 가이드라인 등 규제 동향 리포트가 댓글로 누적됩니다.\n\n"
            "---\n\n"
            "## 📡 데이터 수집 출처\n\n"
            "| 출처 | 설명 |\n"
            "|------|------|\n"
            "| **Google News RSS** | Google News에서 제공하는 RSS 피드를 통해 AI 규제, 거버넌스, 저작권, 법안 관련 최신 소식을 자동으로 수집합니다. |\n\n"
            "---\n\n"
            "> 💡 **참고:** 각 댓글은 수집 시각과 함께 자동으로 기록됩니다.\n"
        ),
        "labels": [label]
    }    
    r2 = requests.post(url, headers=_headers(token), json=payload, timeout=20)
    r2.raise_for_status()
    return int(r2.json()["number"])

def create_comment(owner: str, repo: str, token: str, issue_number: int, body: str) -> None:
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments"
    r = requests.post(url, headers=_headers(token), json={"body": body}, timeout=20)
    r.raise_for_status()

def list_open_issues_by_label(owner: str, repo: str, token: str, label: str, per_page: int = 100) -> list[dict]:
    url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    r = requests.get(url, headers=_headers(token), params={"state": "open", "labels": label, "per_page": per_page}, timeout=20)
    r.raise_for_status()
    return r.json() or []

def close_issue(owner: str, repo: str, token: str, issue_number: int) -> None:
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}"
    r = requests.patch(url, headers=_headers(token), json={"state": "closed"}, timeout=20)
    r.raise_for_status()

def close_other_daily_issues(owner: str, repo: str, token: str, label: str, base_title: str, today_title: str, new_issue_number: int, new_issue_url: str) -> list[int]:
    """같은 라벨을 가진 모니터링 이슈 중 '오늘/현재' 이슈를 제외한 나머지 OPEN 이슈를 닫습니다."""
    closed: list[int] = []
    issues = list_open_issues_by_label(owner, repo, token, label)
    prefix = f"{base_title} ("
    
    # [수정] footer 문자열을 올바르게 합치고 따옴표를 닫았습니다.
    footer = (
        f"다음 리포트: #{new_issue_number} ({new_issue_url})\n\n"
        "이 이슈는 다음 리포트 생성으로 자동 종료되었습니다."
    )

    for it in issues:
        t = it.get("title") or ""
        if t == today_title:
            continue
        # base_title (YYYY-MM-DD) 형태만 닫기
        if t.startswith(prefix) and t.endswith(")"):
            num = int(it["number"])
            comment_and_close_issue(owner, repo, token, num, footer)
            closed.append(num)
    return closed

def comment_and_close_issue(owner: str, repo: str, token: str, issue_number: int, body: str) -> None:
    # 먼저 마무리 코멘트 작성
    url_c = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments"
    rc = requests.post(url_c, headers=_headers(token), json={"body": body}, timeout=20)
    rc.raise_for_status()
    # 그 다음 이슈 Close
    close_issue(owner, repo, token, issue_number)



 
# =========================================================
# NEW: Issue 댓글 조회 (baseline 확보용)
# =========================================================
def list_comments(owner: str, repo: str, token: str, issue_number: int) -> list[dict]:
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments"
    r = requests.get(url, headers=_headers(token), timeout=20)
    r.raise_for_status()
    return r.json() or []




