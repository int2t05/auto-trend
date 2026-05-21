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
