import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_config_reads_required_env(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "sk-test")
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.delenv("DAILY_REPO_LIMIT", raising=False)

    from scripts import config
    import importlib
    importlib.reload(config)

    assert config.LLM_API_KEY == "sk-test"
    assert config.LLM_BASE_URL == "https://api.openai.com/v1"
    assert config.LLM_MODEL == "gpt-4.1-mini"
    assert config.DAILY_REPO_LIMIT == 20


def test_config_reads_custom_env(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "sk-custom")
    monkeypatch.setenv("LLM_BASE_URL", "https://custom.api.com/v1")
    monkeypatch.setenv("LLM_MODEL", "deepseek-chat")
    monkeypatch.setenv("DAILY_REPO_LIMIT", "10")

    from scripts import config
    import importlib
    importlib.reload(config)

    assert config.LLM_API_KEY == "sk-custom"
    assert config.LLM_BASE_URL == "https://custom.api.com/v1"
    assert config.LLM_MODEL == "deepseek-chat"
    assert config.DAILY_REPO_LIMIT == 10


def test_config_missing_api_key_raises():
    import importlib
    import os
    old = os.environ.pop("LLM_API_KEY", None)
    try:
        import scripts.config
        importlib.reload(scripts.config)
        assert scripts.config.LLM_API_KEY != ""
    except KeyError:
        pass
    finally:
        if old is not None:
            os.environ["LLM_API_KEY"] = old


def test_load_feeds_reads_yaml():
    from scripts.config import load_feeds
    feeds = load_feeds()
    assert isinstance(feeds, list)
    assert len(feeds) >= 1
    assert all("name" in f and "url" in f for f in feeds)


def test_load_feeds_returns_empty_when_missing(monkeypatch):
    from scripts import config
    import importlib
    importlib.reload(config)
    monkeypatch.setattr(config, "FEEDS_CONFIG_PATH",
                        config.REPO_ROOT / "nonexistent_feeds.yml")
    feeds = config.load_feeds()
    assert feeds == []


def test_config_reads_rss_items_per_feed(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "sk-test")
    monkeypatch.setenv("RSS_ITEMS_PER_FEED", "5")

    from scripts import config
    import importlib
    importlib.reload(config)

    assert config.RSS_ITEMS_PER_FEED == 5


def test_config_rss_items_per_feed_default(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "sk-test")
    monkeypatch.delenv("RSS_ITEMS_PER_FEED", raising=False)

    from scripts import config
    import importlib
    importlib.reload(config)

    assert config.RSS_ITEMS_PER_FEED == 10
