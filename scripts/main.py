"""Daily GitHub Trending analysis pipeline.

Usage:
    python scripts/main.py              # Run for today
    python scripts/main.py 2026-05-20   # Run for a specific date
"""

import asyncio
import os
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path

from scripts.config import DAILY_REPO_LIMIT
from scripts.fetcher import fetch_trending_repos, fetch_all_readmes
from scripts.analyzer import Analyzer, audit_analysis
from scripts.renderer import render_daily_report
from scripts.indexer import update_index


REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"
DAILY_DIR = DOCS_DIR / "daily"

MAX_ANALYSIS_ATTEMPTS = 3


def get_report_date() -> date:
    if len(sys.argv) > 1:
        return date.fromisoformat(sys.argv[1])
    now = datetime.now(timezone.utc)
    return now.date()


def git_commit_and_push(report_date: date) -> None:
    report_path = DAILY_DIR / f"{report_date.isoformat()}.md"
    index_path = DOCS_DIR / "index.md"

    subprocess.run(
        ["git", "config", "user.name", "github-actions[bot]"],
        check=True, cwd=REPO_ROOT,
    )
    subprocess.run(
        ["git", "config", "user.email",
         "github-actions[bot]@users.noreply.github.com"],
        check=True, cwd=REPO_ROOT,
    )
    subprocess.run(
        ["git", "add", str(report_path), str(index_path)],
        check=True, cwd=REPO_ROOT,
    )
    result = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        cwd=REPO_ROOT,
    )
    if result.returncode == 0:
        print("[auto-trend] No changes to commit, skipping.")
        return
    subprocess.run(
        ["git", "commit", "-m",
         f"report: daily trending analysis for {report_date.isoformat()}"],
        check=True, cwd=REPO_ROOT,
    )
    subprocess.run(
        ["git", "pull", "--rebase"],
        check=True, cwd=REPO_ROOT,
    )
    subprocess.run(["git", "push"], check=True, cwd=REPO_ROOT)


async def run_pipeline(report_date: date) -> None:
    print(f"[auto-trend] Starting pipeline for {report_date.isoformat()}")

    print("[auto-trend] Fetching trending repos...")
    repos = await fetch_trending_repos(limit=DAILY_REPO_LIMIT)
    print(f"[auto-trend] Fetched {len(repos)} repos")

    if not repos:
        print("[auto-trend] No repos found, aborting.")
        return

    print("[auto-trend] Fetching READMEs...")
    repos = await fetch_all_readmes(repos)

    print("[auto-trend] Analyzing repos with LLM...")
    analyzer = Analyzer()
    analyses: dict[str, dict] = {}

    FALLBACK = {
        "summary": "",
        "highlights": [],
        "core_features": [],
        "use_cases": "",
        "competitive_comparison": "",
        "maturity": "",
        "trend_signal": "",
    }

    for repo in repos:
        analysis = None
        for attempt in range(1, MAX_ANALYSIS_ATTEMPTS + 1):
            try:
                analysis = analyzer.analyze_repo(repo)
                missing = audit_analysis(analysis)
                if not missing:
                    break
                print(
                    f"  [auto-trend] ⚠ {repo['full_name']} "
                    f"attempt {attempt}: missing {missing}"
                )
            except Exception as e:
                print(
                    f"  [auto-trend] ✗ {repo['full_name']} "
                    f"attempt {attempt}: {e}"
                )

        if analysis is None:
            print(f"  [auto-trend] ✗ {repo['full_name']}: all attempts failed")
            analysis = {**FALLBACK, "summary": repo.get("description", "")}
            analyses[repo["full_name"]] = analysis
        else:
            analyses[repo["full_name"]] = analysis
            print(f"  [auto-trend] ✓ {repo['full_name']}")

    print("[auto-trend] Generating trend summary...")
    try:
        trend_summary = analyzer.analyze_trends(list(analyses.values()))
    except Exception as e:
        print(f"[auto-trend] Trend summary failed: {e}")
        trend_summary = "今日无法生成趋势总结。"

    print("[auto-trend] Rendering report...")
    report_md = render_daily_report(report_date, repos, analyses, trend_summary)
    report_path = DAILY_DIR / f"{report_date.isoformat()}.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report_md, encoding="utf-8")
    print(f"[auto-trend] Report written to {report_path}")

    print("[auto-trend] Updating index...")
    index_path = DOCS_DIR / "index.md"
    update_index(index_path, report_date)
    print(f"[auto-trend] Index updated at {index_path}")

    if os.environ.get("CI"):
        print("[auto-trend] Committing and pushing...")
        git_commit_and_push(report_date)
    else:
        print("[auto-trend] Not in CI, skipping git commit/push.")


def main():
    report_date = get_report_date()
    asyncio.run(run_pipeline(report_date))


if __name__ == "__main__":
    main()
