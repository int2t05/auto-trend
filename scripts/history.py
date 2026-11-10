"""从近期日报中读取项目记录，供日报排序使用。"""

import re
from datetime import date, timedelta
from pathlib import Path


RECENT_REPO_WINDOW_DAYS = 7
_REPO_HEADING_RE = re.compile(
    r"^### \[([^\]]+)\]\(https://github\.com/[^)\r\n]+\)\r?$",
    re.MULTILINE,
)


def load_recent_repo_names(daily_dir: Path, report_date: date) -> set[str]:
    """读取日报日期之前七天内出现过的仓库名，并统一为小写。"""
    repo_names: set[str] = set()

    for days_ago in range(1, RECENT_REPO_WINDOW_DAYS + 1):
        previous_date = report_date - timedelta(days=days_ago)
        report_path = daily_dir / f"{previous_date.isoformat()}.md"
        if not report_path.is_file():
            continue

        report = report_path.read_text(encoding="utf-8")
        repo_names.update(name.casefold() for name in _REPO_HEADING_RE.findall(report))

    return repo_names
