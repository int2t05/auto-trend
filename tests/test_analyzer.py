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
        if kwargs.get("response_format", {}).get("type") == "json_object":
            return MockCompletion(
                '{"summary": "一个轻量级多智能体编排框架", '
                '"core_features": ["基于 asyncio 的高并发架构", "插件式工具系统"], '
                '"use_cases": "构建多步骤 LLM 流水线的团队，需要生产级可靠性"}'
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
        "total_stars": 1000,
        "readme": "# Test Repo\n\nThis is a test repository.",
        "topics": ["llm", "agents"],
    }

    result = analyzer.analyze_repo(repo)

    assert isinstance(result, dict)
    assert "summary" in result
    assert "core_features" in result
    assert isinstance(result["core_features"], list)
    assert "use_cases" in result


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
