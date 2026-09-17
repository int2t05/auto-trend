import os
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent

LLM_API_KEY = os.environ["LLM_API_KEY"]
LLM_BASE_URL = os.environ.get("LLM_BASE_URL") or "https://api.openai.com/v1"
LLM_MODEL = os.environ.get("LLM_MODEL") or "gpt-4.1-mini"
DAILY_REPO_LIMIT = int(os.environ.get("DAILY_REPO_LIMIT") or "20")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

# RSS 源配置
FEEDS_CONFIG_PATH = REPO_ROOT / "feeds.yml"
RSS_ITEMS_PER_FEED = int(os.environ.get("RSS_ITEMS_PER_FEED") or "10")


def load_feeds() -> list[dict]:
    """读取 feeds.yml，文件不存在或为空时返回空列表（降级为纯 GitHub Trending）。"""
    if not FEEDS_CONFIG_PATH.exists():
        return []
    try:
        data = yaml.safe_load(FEEDS_CONFIG_PATH.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return []
    feeds = data.get("feeds") or []
    return [f for f in feeds if f.get("name") and f.get("url")]

