import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import date


def test_update_index_is_noop(tmp_path):
    """update_index is a no-op since the index is now rendered by Jekyll Liquid."""
    from scripts.indexer import update_index

    index_path = tmp_path / "index.md"
    update_index(index_path, date(2026, 5, 21))
    assert not index_path.exists()
