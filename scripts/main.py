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

from scripts.config import DAILY_REPO_LIMIT, load_feeds
from scripts.fetcher import fetch_trending_repos, fetch_all_readmes, fetch_rss_items
from scripts.analyzer import Analyzer, audit_analysis
from scripts.renderer import render_daily_report
from scripts.rss import render_rss_feed
from scripts.verify_report import verify_report

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"
DAILY_DIR = DOCS_DIR / "daily"

MAX_ANALYSIS_ATTEMPTS = 3
MAX_PIPELINE_ATTEMPTS = 3  # 生成失败后整体重跑次数（含首次）

# LLM 趋势总结失败时的兜底文本，必须 > 50 字符以通过 verify_report 校验
FALLBACK_TREND_SUMMARY = (
    "本期趋势总结未能自动生成，请直接查看下方项目详情与 RSS 热点，"
    "了解今日技术社区的核心亮点、技术方向和动态。"
    "每个条目都包含一句话摘要、核心功能、竞品对比和趋势信号。"
)


def get_report_date() -> date:
    if len(sys.argv) > 1:
        return date.fromisoformat(sys.argv[1])
    now = datetime.now(timezone.utc)
    return now.date()


def git_commit_and_push(report_date: date) -> None:
    report_path = DAILY_DIR / f"{report_date.isoformat()}.md"
    feed_path = DOCS_DIR / "feed.xml"

    subprocess.run(
        ["git", "config", "user.name", "int2t"],
        check=True, cwd=REPO_ROOT,
    )
    subprocess.run(
        ["git", "config", "user.email", "2103859514@qq.com"],
        check=True, cwd=REPO_ROOT,
    )
    subprocess.run(
        ["git", "add", str(report_path), str(feed_path)],
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

    feeds = load_feeds()
    if feeds:
        print(f"[auto-trend] Loaded {len(feeds)} RSS feeds from feeds.yml")

    print("[auto-trend] Fetching trending repos and RSS items...")
    repos, rss_items = await asyncio.gather(
        fetch_trending_repos(limit=DAILY_REPO_LIMIT),
        fetch_rss_items(feeds),
    )
    print(f"[auto-trend] Fetched {len(repos)} repos, {len(rss_items)} RSS items")

    if not repos and not rss_items:
        print("[auto-trend] No repos or RSS items found, aborting.")
        return

    print("[auto-trend] Fetching READMEs...")
    repos = await fetch_all_readmes(repos)
    # RSS items already carry content as readme，无需再抓
    items = repos + rss_items

    print(f"[auto-trend] Analyzing {len(items)} items with LLM...")
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

    for item in items:
        analysis = None
        for attempt in range(1, MAX_ANALYSIS_ATTEMPTS + 1):
            try:
                analysis = analyzer.analyze_repo(item)
                missing = audit_analysis(analysis)
                if not missing:
                    break
                print(
                    f"  [auto-trend] ⚠ {item['full_name']} "
                    f"attempt {attempt}: missing {missing}"
                )
            except Exception as e:
                print(
                    f"  [auto-trend] FAIL: {item['full_name']} "
                    f"attempt {attempt}: {e}"
                )

        if analysis is None:
            print(f"  [auto-trend] FAIL: {item['full_name']}: all attempts failed")
            analysis = {**FALLBACK, "summary": item.get("description", "")}
            analyses[item["full_name"]] = analysis
        else:
            analyses[item["full_name"]] = analysis
            print(f"  [auto-trend] OK: {item['full_name']}")

    print("[auto-trend] Generating trend summary...")
    try:
        trend_summary = analyzer.analyze_trends(list(analyses.values()))
        if not trend_summary or not trend_summary.strip():
            print("[auto-trend] Trend summary empty, using fallback")
            trend_summary = FALLBACK_TREND_SUMMARY
    except Exception as e:
        print(f"[auto-trend] Trend summary failed: {e}")
        trend_summary = FALLBACK_TREND_SUMMARY

    print("[auto-trend] Rendering report...")
    report_md = render_daily_report(report_date, items, analyses, trend_summary)
    report_path = DAILY_DIR / f"{report_date.isoformat()}.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report_md, encoding="utf-8")
    print(f"[auto-trend] Report written to {report_path}")

    print("[auto-trend] Rendering RSS feed...")
    feed_xml = render_rss_feed(items, analyses, report_date)
    feed_path = DOCS_DIR / "feed.xml"
    feed_path.write_text(feed_xml, encoding="utf-8")
    print(f"[auto-trend] RSS feed written to {feed_path}")


def main():
    report_date = get_report_date()
    report_path = DAILY_DIR / f"{report_date.isoformat()}.md"

    for attempt in range(1, MAX_PIPELINE_ATTEMPTS + 1):
        print(f"\n[auto-trend] === Pipeline attempt {attempt}/{MAX_PIPELINE_ATTEMPTS} ===")
        try:
            asyncio.run(run_pipeline(report_date))
        except Exception as e:
            print(f"[auto-trend] FAIL: pipeline 运行时异常 (attempt {attempt}): {e}")
            if attempt < MAX_PIPELINE_ATTEMPTS:
                print("[auto-trend] 重跑生成流程...")
                continue
            print("[auto-trend] 已达最大重试次数，pipeline 持续崩溃")
            if os.environ.get("CI"):
                print("[auto-trend] pipeline 崩溃，跳过 commit/push")
            sys.exit(1)

        # 生成后验证：结构完整性校验，拦截 LLM 截断
        failures = verify_report(report_path)
        if not failures:
            print("[auto-trend] OK: 报告校验通过")
            if os.environ.get("CI"):
                print("[auto-trend] Committing and pushing...")
                git_commit_and_push(report_date)
            else:
                print("[auto-trend] Not in CI, skipping git commit/push.")
            return

        print(f"[auto-trend] FAIL: 报告校验失败 (attempt {attempt}):")
        for f in failures:
            print(f"  - {f}")

        if attempt < MAX_PIPELINE_ATTEMPTS:
            print("[auto-trend] 重跑生成流程...")
        else:
            print("[auto-trend] 已达最大重试次数，保留残缺报告（不 commit）")
            if os.environ.get("CI"):
                print("[auto-trend] 残缺报告未通过校验，跳过 commit/push")
            sys.exit(1)


if __name__ == "__main__":
    main()
