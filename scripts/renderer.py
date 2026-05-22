from datetime import date


def _fmt_stars(n) -> str:
    """Format star count with thousands separator."""
    try:
        n = int(n)
    except (ValueError, TypeError):
        return str(n)
    return f"{n:,}"


def render_daily_report(
    report_date: date,
    repos: list[dict],
    analyses: dict[str, dict],
    trend_summary: str,
) -> str:
    # Sort by daily stars descending
    def _sort_key(r):
        raw = r.get("stars_today", "0")
        try:
            return int(raw.replace(",", ""))
        except (ValueError, TypeError):
            return 0

    sorted_repos = sorted(repos, key=_sort_key, reverse=True)

    lines = []
    lines.append(f"# GitHub Trending 日报 · {report_date.isoformat()}")
    lines.append("")

    # Overview
    lines.append("## 概览")
    lines.append("")
    lang_counts: dict[str, int] = {}
    for r in sorted_repos:
        lang = r.get("language", "Unknown") or "Unknown"
        lang_counts[lang] = lang_counts.get(lang, 0) + 1
    top_langs = sorted(lang_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    lang_summary = "、".join(f"{lang}({count})" for lang, count in top_langs)
    lines.append(
        f"今日共收录 **{len(sorted_repos)}** 个 Trending 项目。"
        f"主要语言分布：{lang_summary}。"
    )
    lines.append("")
    lines.append(trend_summary)
    lines.append("")

    # Project details — sorted by weekly stars descending
    lines.append("## 项目详情")
    lines.append("")
    for repo in sorted_repos:
        full_name = repo["full_name"]
        analysis = analyses.get(full_name, {})

        lang = repo.get("language", "") or ""
        total_stars = _fmt_stars(repo.get("total_stars", 0))
        today = repo.get("stars_today", "0")

        lines.append(f"### [{full_name}]({repo['url']})")
        lines.append("")
        lang_tag = f" `{lang}`" if lang else ""
        lines.append(f"{lang_tag} ⭐ {total_stars} · 今日 +{today}")
        lines.append("")

        summary = analysis.get("summary", repo.get("description", ""))
        if summary:
            lines.append(f"> {summary}")
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

        trend_signal = analysis.get("trend_signal", "")
        if trend_signal:
            lines.append(f"**趋势信号**: {trend_signal}")
            lines.append("")

        lines.append("---")
        lines.append("")

    # Trend observation
    lines.append("## 趋势观察")
    lines.append("")
    lines.append(trend_summary)
    lines.append("")

    return "\n".join(lines)
