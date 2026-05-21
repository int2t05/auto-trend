import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import date


def test_update_index_creates_new_file(tmp_path):
    from scripts.indexer import update_index

    index_path = tmp_path / "index.md"
    update_index(index_path, date(2026, 5, 21))

    content = index_path.read_text(encoding="utf-8")
    assert "# GitHub Trending 日报索引" in content
    assert "[2026-05-21](daily/2026-05-21.md)" in content


def test_update_index_prepends_new_entry(tmp_path):
    from scripts.indexer import update_index

    index_path = tmp_path / "index.md"
    update_index(index_path, date(2026, 5, 20))
    update_index(index_path, date(2026, 5, 21))

    content = index_path.read_text(encoding="utf-8")
    idx_21 = content.find("2026-05-21")
    idx_20 = content.find("2026-05-20")
    assert idx_21 < idx_20  # Newer entry first


def test_update_index_trims_old_entries(tmp_path):
    from scripts.indexer import update_index

    index_path = tmp_path / "index.md"
    update_index(index_path, date(2026, 5, 21), max_entries=2)

    content = index_path.read_text(encoding="utf-8")
    lines_with_links = [l for l in content.split("\n") if "[2026-" in l]
    assert len(lines_with_links) == 1
