from __future__ import annotations
import os
import re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from .fetch import fetch_news
from .extract import load_known_cases, build_regulations_from_news, RegulationInfo
from .render import render_markdown
from .github_issue import find_or_create_issue, create_comment, close_other_daily_issues
from .github_issue import list_comments
from .slack import post_to_slack
from .utils import debug_log
from .dedup import apply_deduplication

def main() -> None:
    # 0) 환경 변수 로드
    owner = os.environ.get("GITHUB_OWNER")
    repo = os.environ.get("GITHUB_REPO")
    gh_token = os.environ.get("GITHUB_TOKEN")
    slack_webhook = os.environ.get("SLACK_WEBHOOK_URL")

    if not all([owner, repo, gh_token, slack_webhook]):
        missing = [k for k, v in {"GITHUB_OWNER": owner, "GITHUB_REPO": repo, "GITHUB_TOKEN": gh_token, "SLACK_WEBHOOK_URL": slack_webhook}.items() if not v]
        raise ValueError(f"필수 환경 변수가 누락되었습니다: {', '.join(missing)}")

    base_title = os.environ.get("ISSUE_TITLE_BASE", "AI 규제/정책/법안 모니터링")
    lookback_days = int(os.environ.get("LOOKBACK_DAYS", "3"))
    # 필요 시 2로 변경: 환경변수 LOOKBACK_DAYS=2
    
    # KST 기준 날짜 생성
    now_kst = datetime.now(ZoneInfo("Asia/Seoul"))
    run_ts_kst = now_kst.strftime("%Y-%m-%d %H:%M")
    issue_day_kst = now_kst.strftime("%Y-%m-%d")
    issue_title = f"{base_title} ({issue_day_kst})"
    debug_log(f"KST 기준 실행시각: {run_ts_kst}")
    
    issue_label = os.environ.get("ISSUE_LABEL", "ai-regulation-monitor")

    # 2) 뉴스 수집
    news = fetch_news()
    known = load_known_cases()
    regulations = build_regulations_from_news(news, known, lookback_days=lookback_days)

    # 3) 렌더링
    md = render_markdown(
        regulations,
        lookback_days=lookback_days,
    )    
    
    debug_log(f"📊 수집 및 분석 완료 (최근 {lookback_days}일)")
    debug_log(f"  ├ News: {len(regulations)}건")

    debug_log("===== REPORT PREVIEW (First 1000 chars) =====")
    debug_log(md[:1000])
    debug_log(f"Report full length: {len(md)}")

    # 4) GitHub Issue 작업
    issue_no = find_or_create_issue(owner, repo, gh_token, issue_title, issue_label)
    issue_url = f"https://github.com/{owner}/{repo}/issues/{issue_no}"
   

    # =========================================================
    # Baseline 비교 로직 (Modularized)
    # =========================================================
    comments = list_comments(owner, repo, gh_token, issue_no)
    md, dedup_stats = apply_deduplication(md, comments)

    # 4.1) 실행 시각을 맨 위로 (중복 제거 요약보다 위로)
    md = f"### 실행 시각(KST): {run_ts_kst}\n\n" + md

    # 이전 날짜 이슈 Close
    closed_nums = close_other_daily_issues(owner, repo, gh_token, issue_label, base_title, issue_title, issue_no, issue_url)
    if closed_nums:
        debug_log(f"이전 날짜 이슈 자동 Close: {closed_nums}")
    
    # KST 기준 타임스탬프
    timestamp = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d %H:%M KST")

    comment_body = f"\n\n{md}"
    create_comment(owner, repo, gh_token, issue_no, comment_body)
    debug_log(f"Issue #{issue_no} 댓글 업로드 완료")

    # 5) Slack 요약 전송
    # ============================================
    # Slack 출력 개선 (최종 포맷)
    # ============================================

    slack_lines = []
    slack_lines.append(":막대_차트: AI 규제/정책 모니터링")
    slack_lines.append(f":시계_3시: {timestamp}")
    slack_lines.append("")

    # 중복 제거 요약 (있을 경우만)
    if dedup_stats:
        new_news = dedup_stats["new_news"]
        new_label = f"{new_news} (New)"
        if new_news > 0:
            new_label = f"🔴 *{new_label}*"
        
        slack_lines.append(":반복: Dedup Summary")
        slack_lines.append(f"└ News {dedup_stats['base_news']} (Baseline): {dedup_stats['dup_news']} (Dup), {new_label}")
        slack_lines.append("")

    # :상승세인_차트: Collection Status
    slack_lines.append(":상승세인_차트: Collection Status")
    slack_lines.append(f"└ News: {len(regulations)}")
    slack_lines.append("")

    # :링크: GitHub
    slack_lines.append(f":링크: GitHub: <{issue_url}|#{issue_no}>")
    try:
        post_to_slack(slack_webhook, "\n".join(slack_lines))
        debug_log(f"Slack 전송 완료")
    except Exception as e:
        debug_log(f"Slack 전송 실패: {e}")
        
if __name__ == "__main__":
    main()
