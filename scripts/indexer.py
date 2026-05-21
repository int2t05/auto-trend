from datetime import date


def update_index(index_path, report_date: date, max_entries: int = 30) -> None:
    date_str = report_date.isoformat()
    new_entry = f"- [{date_str}](daily/{date_str}.md)"

    if index_path.exists():
        existing = index_path.read_text(encoding="utf-8")
        entries = [new_entry]
        for line in existing.split("\n"):
            stripped = line.strip()
            if stripped.startswith("- [20") and stripped != new_entry:
                entries.append(stripped)
        entries = entries[:max_entries]
    else:
        entries = [new_entry]

    content = "# GitHub Trending 日报索引\n\n"
    content += "\n".join(entries)
    content += "\n"

    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(content, encoding="utf-8")
