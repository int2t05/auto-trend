from datetime import date


def _fmt_stars(n) -> str:
    """Format star count with thousands separator."""
    try:
        n = int(n)
    except (ValueError, TypeError):
        return str(n)
    return f"{n:,}"


def _render_analysis_fields(analysis: dict) -> list[str]:
    """渲染 7 字段公共部分。"""
    lines = []

    summary = analysis.get("summary", "")
    if summary:
        lines.append(f"> {summary}")
        lines.append("")

    highlights = analysis.get("highlights", [])
    if highlights:
        lines.append("**亮点**")
        lines.append("")
        for h in highlights:
            lines.append(f"- {h}")
        lines.append("")

    core_features = analysis.get("core_features", [])
    if core_features:
        lines.append("**核心功能**")
        lines.append("")
        for f in core_features:
            lines.append(f"- {f}")
        lines.append("")

    use_cases = analysis.get("use_cases", "")
    if use_cases:
        lines.append(f"**适用场景**: {use_cases}")
        lines.append("")

    competitive_comparison = analysis.get("competitive_comparison", "")
    if competitive_comparison:
        lines.append(f"**竞品对比**: {competitive_comparison}")
        lines.append("")

    maturity = analysis.get("maturity", "")
    if maturity:
        lines.append(f"**成熟度**: {maturity}")
        lines.append("")

    trend_signal = analysis.get("trend_signal", "")
    if trend_signal:
        lines.append(f"**趋势信号**: {trend_signal}")
        lines.append("")

    return lines


def _render_item(repo: dict, analysis: dict, meta_line: str) -> list[str]:
    """渲染单个项目条目，meta_line 展示语言与星数。"""
    lines = [f"### [{repo['full_name']}]({repo['url']})", ""]
    if meta_line:
        lines.append(meta_line)
        lines.append("")
    lines.extend(_render_analysis_fields(analysis))
    lines.append("---")
    lines.append("")
    return lines


def render_daily_report(
    report_date: date,
    repos: list[dict],
    analyses: dict[str, dict],
    trend_summary: str,
) -> str:
    # 项目按日增星数降序
    repos = sorted(repos, key=lambda r: r.get("stars_today", 0), reverse=True)

    lines = [f"# GitHub Trending 日报 · {report_date.isoformat()}", ""]

    # Overview
    lines.append("## 概览")
    lines.append("")
    lang_counts: dict[str, int] = {}
    for r in repos:
        lang = r.get("language", "Unknown") or "Unknown"
        lang_counts[lang] = lang_counts.get(lang, 0) + 1
    top_langs = sorted(lang_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    lang_summary = "、".join(f"{lang}({count})" for lang, count in top_langs)
    lines.append(f"今日共收录 **{len(repos)}** 个 GitHub Trending 项目。")
    if lang_summary:
        lines.append(f"主要语言分布：{lang_summary}。")
    lines.append("")
    lines.append(trend_summary)
    lines.append("")

    # Project details — sorted by daily stars descending
    lines.append("## 项目详情")
    lines.append("")
    for repo in repos:
        analysis = analyses.get(repo["full_name"], {})
        lang = repo.get("language", "") or ""
        today = _fmt_stars(repo.get("stars_today", 0))
        total_stars = _fmt_stars(repo.get("total_stars", 0))
        lang_tag = f" `{lang}`" if lang else ""
        meta_line = f"{lang_tag} ⭐ +{today} 今日新增 · {total_stars} 总星数"
        lines.extend(_render_item(repo, analysis, meta_line))

    # Trend observation
    lines.append("## 趋势观察")
    lines.append("")
    lines.append(trend_summary)
    lines.append("")

    return "\n".join(lines)
