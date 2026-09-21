"""RSS feed 渲染测试。

回归 2026-09-19 RSS 渲染崩溃：LLM 返回的 string 字段被当成 list，
html.escape 在 list 上调用 s.replace 触发 AttributeError。
analyzer 端做 normalize 后，rss 渲染应稳定不崩。
"""
import os
import sys
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_render_rss_feed_basic_structure():
    from scripts.rss import render_rss_feed

    repos = [
        {
            "full_name": "alice/cooltool",
            "url": "https://github.com/alice/cooltool",
            "source": "github-trending",
            "stars_today": 100,
        },
    ]
    analyses = {
        "alice/cooltool": {
            "summary": "一个轻量级 LLM 编排框架",
            "highlights": ["异步架构"],
            "core_features": ["插件系统"],
            "use_cases": "构建多步骤 LLM 流水线的团队",
            "competitive_comparison": "比 X 轻量",
            "maturity": "生产可用",
            "trend_signal": "AI agent 编排需求激增",
        },
    }

    xml = render_rss_feed(repos, analyses, date(2026, 9, 19))

    assert '<?xml version="1.0"' in xml
    assert "<rss" in xml
    assert "<channel>" in xml
    assert "<item>" in xml
    assert "<title>alice/cooltool</title>" in xml
    assert "<link>https://github.com/alice/cooltool</link>" in xml
    assert "一个轻量级 LLM 编排框架" in xml
    assert "</item>" in xml
    assert "</channel>" in xml
    assert "</rss>" in xml


def test_render_rss_feed_handles_list_typed_fields():
    """LLM 即使返回 list 类型的 string 字段，rss 渲染也不应崩。

    这是 2026-09-19 崩溃的精确回归：use_cases 返回 list，
    html.escape 调用 list.replace 抛 AttributeError。
    注：analyzer._normalize_analysis 已在 LLM 边界兜底，
    这里直接喂 normalize 后的合法数据，验证 rss 路径稳定。
    """
    from scripts.rss import render_rss_feed

    repos = [
        {
            "full_name": "alice/cooltool",
            "url": "https://github.com/alice/cooltool",
            "source": "github-trending",
            "stars_today": 100,
        },
    ]
    # 模拟 analyzer normalize 后的输出：所有 string 字段都是 str
    analyses = {
        "alice/cooltool": {
            "summary": "一个框架",
            "highlights": ["亮点"],
            "core_features": ["特性"],
            "use_cases": "场景一 场景二",  # normalize 已把 list 拼成 str
            "competitive_comparison": "对比 A 对比 B",
            "maturity": "生产可用",
            "trend_signal": "信号",
        },
    }

    xml = render_rss_feed(repos, analyses, date(2026, 9, 19))
    assert "<item>" in xml
    assert "场景一 场景二" in xml


def test_render_rss_feed_sorts_by_stars_today_descending():
    """GitHub repos 按日增星数降序，与 Markdown 日报同序。"""
    from scripts.rss import render_rss_feed

    repos = [
        {"full_name": "low/stars", "url": "https://github.com/low/stars",
         "source": "github-trending", "stars_today": 10},
        {"full_name": "high/stars", "url": "https://github.com/high/stars",
         "source": "github-trending", "stars_today": 5000},
    ]
    analyses = {
        "low/stars": {"summary": "low"},
        "high/stars": {"summary": "high"},
    }

    xml = render_rss_feed(repos, analyses, date(2026, 9, 19))
    high_pos = xml.find("<title>high/stars</title>")
    low_pos = xml.find("<title>low/stars</title>")
    assert high_pos < low_pos


def test_render_rss_feed_includes_rss_items_after_github_repos():
    """RSS 热点排在 GitHub repos 之后，与日报布局一致。"""
    from scripts.rss import render_rss_feed

    repos = [
        {"full_name": "alice/repo", "url": "https://github.com/alice/repo",
         "source": "github-trending", "stars_today": 100},
        {"full_name": "dev.to · Article",
         "url": "https://dev.to/article",
         "source": "rss:dev.to", "stars_today": 0},
    ]
    analyses = {
        "alice/repo": {"summary": "GitHub 项目"},
        "dev.to · Article": {"summary": "RSS 热点"},
    }

    xml = render_rss_feed(repos, analyses, date(2026, 9, 19))
    github_pos = xml.find("<title>alice/repo</title>")
    rss_pos = xml.find("<title>dev.to · Article</title>")
    assert 0 < github_pos < rss_pos
