"""RSS feed 生成测试。

验证 RSS 2.0 XML 结构：每份日报一条 item，按日期降序排列。
"""
import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _write_report(daily_dir: Path, report_date: date, trend_text: str) -> Path:
    """生成一份测试用日报 Markdown。"""
    md = (
        f"# GitHub Trending 日报 · {report_date.isoformat()}\n\n"
        f"## 概览\n\n{trend_text}\n\n"
        f"## 项目详情\n\n### [test/repo](https://github.com/test/repo)\n\n> 摘要\n\n---\n\n"
        f"## 趋势观察\n\n{trend_text}\n"
    )
    path = daily_dir / f"{report_date.isoformat()}.md"
    path.write_text(md, encoding="utf-8")
    return path


def test_render_rss_feed_basic_structure(tmp_path):
    """验证 RSS XML 基本结构：xml 声明、channel、item、title、link。"""
    from scripts.rss import render_rss_feed

    daily_dir = tmp_path / "daily"
    daily_dir.mkdir()
    _write_report(daily_dir, date(2026, 9, 21), "今日 AI agent 基础设施持续升温。")

    xml = render_rss_feed(daily_dir)

    assert '<?xml version="1.0"' in xml
    assert "<rss" in xml
    assert "<channel>" in xml
    assert "<item>" in xml
    assert "GitHub Trending 日报 · 2026-09-21" in xml
    assert "/daily/2026-09-21.html" in xml
    assert "今日 AI agent 基础设施持续升温" in xml
    assert "</item>" in xml
    assert "</channel>" in xml
    assert "</rss>" in xml


def test_render_rss_feed_sorts_by_date_descending(tmp_path):
    """多份日报时，最新日期排最前。"""
    from scripts.rss import render_rss_feed

    daily_dir = tmp_path / "daily"
    daily_dir.mkdir()
    _write_report(daily_dir, date(2026, 9, 19), "第一天")
    _write_report(daily_dir, date(2026, 9, 21), "第三天")
    _write_report(daily_dir, date(2026, 9, 20), "第二天")

    xml = render_rss_feed(daily_dir)
    pos_21 = xml.find("2026-09-21")
    pos_20 = xml.find("2026-09-20")
    pos_19 = xml.find("2026-09-19")

    assert 0 < pos_21 < pos_20 < pos_19


def test_render_rss_feed_skips_non_date_files(tmp_path):
    """非日期格式的 .md 文件应被跳过。"""
    from scripts.rss import render_rss_feed

    daily_dir = tmp_path / "daily"
    daily_dir.mkdir()
    _write_report(daily_dir, date(2026, 9, 21), "正常日报")
    (daily_dir / "README.md").write_text("not a report", encoding="utf-8")

    xml = render_rss_feed(daily_dir)

    assert "2026-09-21" in xml
    assert "README" not in xml


def test_render_rss_feed_empty_dir(tmp_path):
    """空目录应生成有效但无 item 的 RSS XML。"""
    from scripts.rss import render_rss_feed

    daily_dir = tmp_path / "daily"
    daily_dir.mkdir()

    xml = render_rss_feed(daily_dir)

    assert "<channel>" in xml
    assert "<item>" not in xml
    assert "</rss>" in xml
