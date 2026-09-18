"""RSS 2.0 feed 生成：将 trending repos + RSS 热点渲染为 RSS XML。

供 main.py 在生成 Markdown 日报后追加调用，输出到 docs/feed.xml，
供 rss-feed 等下游聚合器通过公网 URL 拉取。
"""

from datetime import date, datetime, timezone
from email.utils import formatdate
from html import escape


def _html_content(analysis: dict) -> str:
    """将 LLM 分析结果渲染为 HTML，放入 content:encoded。"""
    parts = []

    summary = analysis.get("summary", "")
    if summary:
        parts.append(f"<p><em>{escape(summary)}</em></p>")

    highlights = analysis.get("highlights", [])
    if highlights:
        items = "".join(f"<li>{escape(h)}</li>" for h in highlights)
        parts.append(f"<p><strong>亮点</strong></p><ul>{items}</ul>")

    core_features = analysis.get("core_features", [])
    if core_features:
        items = "".join(f"<li>{escape(f)}</li>" for f in core_features)
        parts.append(f"<p><strong>核心功能</strong></p><ul>{items}</ul>")

    use_cases = analysis.get("use_cases", "")
    if use_cases:
        parts.append(f"<p><strong>适用场景</strong>: {escape(use_cases)}</p>")

    competitive_comparison = analysis.get("competitive_comparison", "")
    if competitive_comparison:
        parts.append(
            f"<p><strong>竞品对比</strong>: {escape(competitive_comparison)}</p>"
        )

    maturity = analysis.get("maturity", "")
    if maturity:
        parts.append(f"<p><strong>成熟度</strong>: {escape(maturity)}</p>")

    trend_signal = analysis.get("trend_signal", "")
    if trend_signal:
        parts.append(f"<p><strong>趋势信号</strong>: {escape(trend_signal)}</p>")

    return "\n".join(parts)


def _item_xml(item: dict, analysis: dict, pub_date_rfc: str) -> str:
    """渲染单个 RSS item。"""
    title = item["full_name"]
    link = item.get("url", "")
    guid = link or title
    description = analysis.get("summary", "") or item.get("description", "")
    content = _html_content(analysis)

    return (
        "    <item>\n"
        f"      <title>{escape(title)}</title>\n"
        f"      <link>{escape(link)}</link>\n"
        f"      <guid isPermaLink=\"false\">{escape(guid)}</guid>\n"
        f"      <pubDate>{pub_date_rfc}</pubDate>\n"
        f"      <description>{escape(description)}</description>\n"
        f"      <content:encoded><![CDATA[{content}]]></content:encoded>\n"
        "    </item>"
    )


def render_rss_feed(
    repos: list[dict],
    analyses: dict[str, dict],
    report_date: date,
) -> str:
    """渲染完整 RSS 2.0 XML。

    每个 trending repo / RSS 热点作为一条 item：
    - title: owner/repo 或 "Feed · Title"
    - link: GitHub URL 或 RSS link
    - pubDate: 日报日期（UTC 00:00）
    - description: LLM summary
    - content:encoded: 完整分析 HTML
    """
    # report_date -> RFC 822 格式（UTC 00:00）
    dt = datetime(report_date.year, report_date.month, report_date.day, tzinfo=timezone.utc)
    pub_date_rfc = formatdate(dt.timestamp(), usegmt=True)

    # 与 Markdown 日报同序：GitHub repos 按日增星数降序，RSS 热点保持顺序
    github_repos = [r for r in repos if not r.get("source", "").startswith("rss:")]
    rss_items = [r for r in repos if r.get("source", "").startswith("rss:")]
    github_repos.sort(key=lambda r: r.get("stars_today", 0), reverse=True)
    rss_items.sort(key=lambda r: r.get("stars_today", 0), reverse=True)

    items_xml = "\n".join(
        _item_xml(item, analyses.get(item["full_name"], {}), pub_date_rfc)
        for item in github_repos + rss_items
    )

    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/">\n'
        "  <channel>\n"
        "    <title>Auto-Trend GitHub Trending 日报</title>\n"
        "    <link>https://int2t05.github.io/auto-trend/</link>\n"
        f"    <description>每日 GitHub Trending + RSS 热点 LLM 分析 · {report_date.isoformat()}</description>\n"
        "    <language>zh-CN</language>\n"
        f"    <lastBuildDate>{pub_date_rfc}</lastBuildDate>\n"
        f"{items_xml}\n"
        "  </channel>\n"
        "</rss>"
    )
