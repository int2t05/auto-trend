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
            "url": "https://github.com/bob/othertool",
        },
    ]

    analyses = {
        "alice/cooltool": {
            "summary": "一个轻量级 LLM 编排框架",
            "highlights": ["异步架构", "插件系统"],
            "use_cases": "构建多步骤 LLM 流水线的团队",
            "comparison": "比 LangChain 更轻量",
            "maturity": "成长期",
            "trend_signal": "AI agent 需求激增",
        },
        "bob/othertool": {
            "summary": "高性能序列化库",
            "highlights": ["零拷贝设计"],
            "use_cases": "需要高性能数据交换的系统",
            "comparison": "比 serde 更快",
            "maturity": "成熟",
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
    assert "## 今日精选" in report
    assert "## 完整列表" in report
    assert "## 趋势观察" in report
    assert "alice/cooltool" in report
    assert "bob/othertool" in report
    assert "一个轻量级 LLM 编排框架" in report
    assert "高性能序列化库" in report
    assert "| 排名 | 项目 | 语言 | Stars | 一句话概括 |" in report
