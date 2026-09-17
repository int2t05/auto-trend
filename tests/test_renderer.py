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
            "stars_today": 1500,
            "total_stars": 15000,
            "url": "https://github.com/alice/cooltool",
        },
        {
            "full_name": "bob/othertool",
            "owner": "bob",
            "name": "othertool",
            "description": "Another tool",
            "language": "Rust",
            "stars_today": 800,
            "total_stars": 8000,
            "url": "https://github.com/bob/othertool",
        },
    ]

    analyses = {
        "alice/cooltool": {
            "summary": "一个轻量级 LLM 编排框架",
            "core_features": ["异步架构", "插件系统"],
            "use_cases": "构建多步骤 LLM 流水线的团队",
            "trend_signal": "AI agent 编排需求激增",
        },
        "bob/othertool": {
            "summary": "高性能序列化库",
            "core_features": ["零拷贝设计"],
            "use_cases": "需要高性能数据交换的系统",
            "trend_signal": "性能优化工具持续受关注",
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
    assert "趋势信号" in report
    assert "⭐ +1,500 今日新增 · 15,000 总星数" in report
    assert "⭐ +800 今日新增 · 8,000 总星数" in report


def test_render_sorts_by_daily_stars_descending():
    from scripts.renderer import render_daily_report

    repos = [
        {
            "full_name": "alice/lowstars",
            "owner": "alice",
            "name": "lowstars",
            "description": "",
            "language": "Go",
            "stars_today": 100,
            "total_stars": 1000,
            "url": "https://github.com/alice/lowstars",
        },
        {
            "full_name": "bob/highstars",
            "owner": "bob",
            "name": "highstars",
            "description": "",
            "language": "Rust",
            "stars_today": 5000,
            "total_stars": 50000,
            "url": "https://github.com/bob/highstars",
        },
    ]

    analyses = {
        "alice/lowstars": {"summary": "low", "core_features": [], "use_cases": "", "trend_signal": ""},
        "bob/highstars": {"summary": "high", "core_features": [], "use_cases": "", "trend_signal": ""},
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


def test_render_rss_section():
    """RSS 热点章节存在、source 标签正确、7 字段渲染。"""
    from scripts.renderer import render_daily_report

    rss_items = [
        {
            "full_name": "Hacker News · Rust 1.78 released",
            "description": "Rust 1.78 ships with proc-macro improvements.",
            "readme": "Rust 1.78 content...",
            "url": "https://news.ycombinator.com/item?id=1",
            "source": "rss:Hacker News",
            "language": "",
            "stars_today": 0,
            "total_stars": 0,
        },
    ]

    analyses = {
        "Hacker News · Rust 1.78 released": {
            "summary": "Rust 1.78 发布，改进 proc-macro",
            "core_features": ["proc-macro 诊断增强"],
            "use_cases": "Rust 开发者关注新版特性",
            "highlights": ["编译器诊断信息更友好"],
            "competitive_comparison": "相比 Go，宏能力更强",
            "maturity": "已发布稳定版",
            "trend_signal": "Rust 生态持续扩张",
        },
    }

    report = render_daily_report(
        report_date=date(2026, 9, 17),
        repos=rss_items,
        analyses=analyses,
        trend_summary="今日 RSS 热点集中在语言生态更新。",
    )

    assert "## RSS 热点" in report
    assert "## 项目详情" not in report  # 无 GitHub repo 时不渲染空章节
    assert "## 趋势观察" in report
    assert "[Hacker News · Rust 1.78 released]" in report
    assert "`RSS: Hacker News`" in report
    assert "Rust 1.78 发布，改进 proc-macro" in report
    assert "核心功能" in report
    assert "适用场景" in report
    assert "趋势信号" in report
    # RSS item 不应出现 GitHub 星数标签
    assert "⭐" not in report
    assert "总星数" not in report


def test_render_separates_by_source():
    """GitHub repos 进项目详情，RSS items 进 RSS 热点，分区正确。"""
    from scripts.renderer import render_daily_report

    items = [
        {
            "full_name": "alice/cooltool",
            "owner": "alice",
            "name": "cooltool",
            "description": "A cool tool",
            "language": "Python",
            "stars_today": 1500,
            "total_stars": 15000,
            "url": "https://github.com/alice/cooltool",
            "source": "github-trending",
        },
        {
            "full_name": "dev.to · Post about LLMs",
            "description": "A blog post about LLMs",
            "readme": "content...",
            "url": "https://dev.to/post",
            "source": "rss:dev.to",
            "language": "",
            "stars_today": 0,
            "total_stars": 0,
        },
    ]

    analyses = {
        "alice/cooltool": {
            "summary": "轻量 LLM 编排框架",
            "core_features": ["异步架构"],
            "use_cases": "构建 LLM 流水线",
            "highlights": ["插件系统"],
            "competitive_comparison": "比 X 轻量",
            "maturity": "生产可用",
            "trend_signal": "AI 编排需求增长",
        },
        "dev.to · Post about LLMs": {
            "summary": "LLM 应用实践文章",
            "core_features": ["prompt 工程实战"],
            "use_cases": "LLM 应用开发者",
            "highlights": ["真实案例复盘"],
            "competitive_comparison": "暂无直接竞品",
            "maturity": "信息成熟",
            "trend_signal": "prompt 工程讨论升温",
        },
    }

    report = render_daily_report(
        report_date=date(2026, 9, 17),
        repos=items,
        analyses=analyses,
        trend_summary="今日 GitHub 与 RSS 双源都聚焦 LLM 方向。",
    )

    # 两章节都应存在
    assert "## 项目详情" in report
    assert "## RSS 热点" in report

    # 顺序：项目详情 在 RSS 热点 之前，RSS 热点 在 趋势观察 之前
    detail_pos = report.find("## 项目详情")
    rss_pos = report.find("## RSS 热点")
    trend_pos = report.find("## 趋势观察")
    assert detail_pos < rss_pos < trend_pos

    # GitHub repo 在项目详情中，带星数标签
    assert "[alice/cooltool]" in report
    assert "⭐ +1,500 今日新增 · 15,000 总星数" in report

    # RSS item 在 RSS 热点中，带 RSS 标签
    assert "[dev.to · Post about LLMs]" in report
    assert "`RSS: dev.to`" in report
