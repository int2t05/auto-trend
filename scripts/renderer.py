from datetime import date


def render_daily_report(
    report_date: date,
    repos: list[dict],
    analyses: dict[str, dict],
    trend_summary: str,
    picked: list[str] | None = None,
) -> str:
    if picked is None:
        picked = [r["full_name"] for r in repos[:5]]

    lines = []
    lines.append(f"# GitHub Trending 日报 · {report_date.isoformat()}")
    lines.append("")

    # Overview
    lines.append("## 概览")
    lines.append("")
    lang_counts: dict[str, int] = {}
    for r in repos:
        lang = r.get("language", "Unknown") or "Unknown"
        lang_counts[lang] = lang_counts.get(lang, 0) + 1
    top_langs = sorted(lang_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    lang_summary = "、".join(f"{lang}({count})" for lang, count in top_langs)
    lines.append(
        f"今日共收录 **{len(repos)}** 个 Trending 项目。"
        f"主要语言分布：{lang_summary}。"
    )
    lines.append("")
    lines.append(trend_summary)
    lines.append("")

    # Picks
    lines.append("## 今日精选")
    lines.append("")
    for full_name in picked:
        analysis = analyses.get(full_name, {})
        repo = next((r for r in repos if r["full_name"] == full_name), None)
        if not repo:
            continue
        lines.append(f"### [{full_name}]({repo['url']})")
        lines.append("")
        lines.append(
            f"**语言**: {repo.get('language', 'N/A')} "
            f"| **今日 Stars**: {repo.get('stars_today', 'N/A')}"
        )
        lines.append("")
        lines.append(f"> {analysis.get('summary', repo.get('description', ''))}")
        lines.append("")
        highlights = analysis.get("highlights", [])
        if highlights:
            for h in highlights:
                lines.append(f"- **亮点**: {h}")
        lines.append(f"- **适用场景**: {analysis.get('use_cases', 'N/A')}")
        lines.append(f"- **竞品对比**: {analysis.get('comparison', 'N/A')}")
        lines.append(f"- **成熟度**: {analysis.get('maturity', 'N/A')}")
        lines.append(f"- **趋势信号**: {analysis.get('trend_signal', 'N/A')}")
        lines.append("")

    # Full list
    lines.append("## 完整列表")
    lines.append("")
    lines.append("| 排名 | 项目 | 语言 | Stars | 一句话概括 |")
    lines.append("|------|------|------|-------|-----------|")
    for i, repo in enumerate(repos, 1):
        full_name = repo["full_name"]
        summary = analyses.get(full_name, {}).get(
            "summary", repo.get("description", "")
        )
        language = repo.get("language", "")
        stars = repo.get("stars_today", "")
        lines.append(
            f"| {i} | [{full_name}]({repo['url']}) "
            f"| {language} | {stars} | {summary} |"
        )
    lines.append("")

    # Trend observation
    lines.append("## 趋势观察")
    lines.append("")
    lines.append(trend_summary)
    lines.append("")

    return "\n".join(lines)
