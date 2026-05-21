import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Ensure LLM_API_KEY is set before analyzer module tries to read config
os.environ.setdefault("LLM_API_KEY", "sk-test-mock")


class MockCompletion:
    def __init__(self, content):
        class Choice:
            def __init__(self, content):
                self.message = type("Message", (), {"content": content})()
        self.choices = [Choice(content)]


class MockChat:
    def __init__(self):
        self.completions = self

    def create(self, **kwargs):
        # analyze_trends doesn't pass response_format; analyze_repo passes json_object
        if kwargs.get("response_format", {}).get("type") == "json_object":
            return MockCompletion(
                '{"summary": "A lightweight LLM orchestration framework that simplifies multi-agent workflows", '
                '"highlights": ["Built on asyncio for high concurrency", "Plugin-based tool system"], '
                '"use_cases": "Teams building multi-step LLM pipelines who need production reliability", '
                '"comparison": "Compared to LangChain it is lighter and less opinionated", '
                '"maturity": "成长期", '
                '"trend_signal": "The surge in AI agent adoption is driving demand for simpler orchestration tools"}'
            )
        return MockCompletion(
            "Today's trending shows a clear focus on AI agent infrastructure "
            "and developer tooling. Several projects aim to simplify LLM "
            "orchestration, suggesting the market is moving from experimentation "
            "to production."
        )


class MockOpenAI:
    def __init__(self, **kwargs):
        self.chat = MockChat()


def test_analyze_repo_returns_structured_dict():
    from scripts.analyzer import Analyzer

    analyzer = Analyzer(client=MockOpenAI())
    repo = {
        "full_name": "testowner/testrepo",
        "description": "A test repo for unit testing",
        "language": "Python",
        "stars_today": "100",
        "readme": "# Test Repo\n\nThis is a test repository.",
        "topics": ["llm", "agents"],
    }

    result = analyzer.analyze_repo(repo)

    assert isinstance(result, dict)
    assert "summary" in result
    assert "highlights" in result
    assert isinstance(result["highlights"], list)
    assert "use_cases" in result
    assert "comparison" in result
    assert "maturity" in result
    assert result["maturity"] in ("早期", "成长期", "成熟")
    assert "trend_signal" in result


def test_analyze_trends_returns_string():
    from scripts.analyzer import Analyzer

    analyzer = Analyzer(client=MockOpenAI())
    analyses = [
        {"summary": "A tool for AI agents"},
        {"summary": "A devtool framework"},
    ]

    result = analyzer.analyze_trends(analyses)

    assert isinstance(result, str)
    assert len(result) > 0
