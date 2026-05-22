import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import date


def test_render_daily_report_contains_sections():
    from scripts.renderer import render_daily_report

    repos = [
        {
            "full_name": "alice/cooltool",
            "owner": "alice",
            "name": "cooltool",
            "description": "A cool tool",
            "language": "Python",
            "stars_today": "1,500",
            "forks_today": "200",
            "total_stars": 15000,
            "url": "https://github.com/alice/cooltool",
        },
        {
            "full_name": "bob/othertool",
            "owner": "bob",
            "name": "othertool",
            "description": "Another tool",
            "language": "Rust",
            "stars_today": "800",
            "forks_today": "50",
            "total_stars": 8000,
            "url": "https://github.com/bob/othertool",
        },
    ]

    analyses = {
        "alice/cooltool": {
            "summary": "一个轻量级 LLM 编排框架",
            "core_features": ["异步架构", "插件系统"],
            "use_cases": "构建多步骤 LLM 流水线的团队",
        },
        "bob/othertool": {
            "summary": "高性能序列化库",
            "core_features": ["零拷贝设计"],
            "use_cases": "需要高性能数据交换的系统",
        },
    }

    trend_summary = "今日趋势集中在 AI 基础设施和开发者工具两个方向。"

    report = render_daily_report(
        report_date=date(2026, 5, 21),
        repos=repos,
        analyses=analyses,
        trend_summary=trend_summary,
    )

    assert "# GitHub Trending 日报 · 2026-05-21" in report
    assert "## 概览" in report
    assert "## 项目详情" in report
    assert "## 趋势观察" in report
    assert "[alice/cooltool](https://github.com/alice/cooltool)" in report
    assert "[bob/othertool](https://github.com/bob/othertool)" in report
    assert "一个轻量级 LLM 编排框架" in report
    assert "高性能序列化库" in report
    assert "核心功能" in report
    assert "适用场景" in report
    assert "⭐ 15,000 · 今日 +1,500" in report
    assert "⭐ 8,000 · 今日 +800" in report


def test_render_sorts_by_daily_stars_descending():
    from scripts.renderer import render_daily_report

    repos = [
        {
            "full_name": "alice/lowstars",
            "owner": "alice",
            "name": "lowstars",
            "description": "",
            "language": "Go",
            "stars_today": "100",
            "forks_today": "10",
            "total_stars": 1000,
            "url": "https://github.com/alice/lowstars",
        },
        {
            "full_name": "bob/highstars",
            "owner": "bob",
            "name": "highstars",
            "description": "",
            "language": "Rust",
            "stars_today": "5,000",
            "forks_today": "200",
            "total_stars": 50000,
            "url": "https://github.com/bob/highstars",
        },
    ]

    analyses = {
        "alice/lowstars": {"summary": "low", "core_features": [], "use_cases": ""},
        "bob/highstars": {"summary": "high", "core_features": [], "use_cases": ""},
    }

    report = render_daily_report(
        report_date=date(2026, 5, 21),
        repos=repos,
        analyses=analyses,
        trend_summary="test",
    )

    high_pos = report.find("bob/highstars")
    low_pos = report.find("alice/lowstars")
    assert high_pos < low_pos
