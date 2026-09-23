"""RSS 2.0 feed 生成：将每日日报作为 RSS item 输出到 docs/feed.xml。

扫描 docs/daily/*.md，每份日报对应一条 item，供订阅者通过 RSS 链接获取更新。
"""

import re
from datetime import date, datetime, timezone
from email.utils import formatdate
from html import escape
from pathlib import Path

SITE_URL = "https://int2t05.github.io/auto-trend"


def _extract_trend_summary(md_text: str) -> str:
    """从日报 Markdown 中提取 '## 趋势观察' 段落作为 RSS description。"""
    match = re.search(
        r"^## 趋势观察\s*$\n(.+?)(?=\n##\s|\Z)",
        md_text,
        re.MULTILINE | re.DOTALL,
    )
    if not match:
        return ""
    # 取第一段非空文本，去掉 markdown 列表标记
    lines = []
    for line in match.group(1).strip().splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        lines.append(stripped)
    return " ".join(lines)[:300]


def _item_xml(report_date: date, description: str) -> str:
    """渲染单个日报 RSS item。"""
    date_str = report_date.isoformat()
    dt = datetime(
        report_date.year, report_date.month, report_date.day, tzinfo=timezone.utc
    )
    pub_date_rfc = formatdate(dt.timestamp(), usegmt=True)
    link = f"{SITE_URL}/daily/{date_str}.html"

    return (
        "    <item>\n"
        f"      <title>GitHub Trending 日报 · {date_str}</title>\n"
        f"      <link>{escape(link)}</link>\n"
        f"      <guid isPermaLink=\"true\">{escape(link)}</guid>\n"
        f"      <pubDate>{pub_date_rfc}</pubDate>\n"
        f"      <description>{escape(description)}</description>\n"
        "    </item>"
    )


def render_rss_feed(daily_dir: Path) -> str:
    """渲染完整 RSS 2.0 XML，每份日报一条 item，按日期降序排列。"""
    items = []
    for md_path in daily_dir.glob("*.md"):
        try:
            report_date = date.fromisoformat(md_path.stem)
        except ValueError:
            continue
        description = _extract_trend_summary(md_path.read_text(encoding="utf-8"))
        items.append((report_date, description))

    items.sort(key=lambda x: x[0], reverse=True)

    now_rfc = formatdate(datetime.now(timezone.utc).timestamp(), usegmt=True)
    items_xml = "\n".join(_item_xml(d, desc) for d, desc in items)

    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/">\n'
        "  <channel>\n"
        "    <title>Auto-Trend GitHub Trending 日报</title>\n"
        f"    <link>{SITE_URL}/</link>\n"
        "    <description>每日 GitHub Trending + RSS 热点 LLM 分析</description>\n"
        "    <language>zh-CN</language>\n"
        f"    <lastBuildDate>{now_rfc}</lastBuildDate>\n"
        f"{items_xml}\n"
        "  </channel>\n"
        "</rss>"
    )
