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
            sys_msg = ""
            for m in kwargs.get("messages", []):
                if m.get("role") == "system":
                    sys_msg = m.get("content", "")
                    break
            if "技术趋势分析员" in sys_msg:
                return MockCompletion(
                    '{"trend_summary": "Today\'s trending shows a clear focus on AI agent '
                    'infrastructure and developer tooling. Several projects aim to simplify '
                    'LLM orchestration, suggesting the market is moving from experimentation '
                    'to production."}'
                )
            return MockCompletion(
                '{"summary": "一个轻量级多智能体编排框架", '
                '"core_features": ["基于 asyncio 的高并发架构", "插件式工具系统"], '
                '"use_cases": "构建多步骤 LLM 流水线的团队，需要生产级可靠性", '
                '"trend_signal": "AI agent 编排需求激增，开发者寻求 LangChain 的轻量替代"}'
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
        "stars_today": 100,
        "total_stars": 1000,
        "readme": "# Test Repo\n\nThis is a test repository.",
    }

    result = analyzer.analyze_repo(repo)

    assert isinstance(result, dict)
    assert "summary" in result
    assert "core_features" in result
    assert isinstance(result["core_features"], list)
    assert "use_cases" in result
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


def test_audit_analysis_all_present():
    from scripts.analyzer import audit_analysis

    complete = {
        "summary": "A summary",
        "core_features": ["f1", "f2"],
        "use_cases": "Some use cases",
        "highlights": ["h1"],
        "competitive_comparison": "No competitors",
        "maturity": "Early stage",
        "trend_signal": "Hot topic",
    }
    assert audit_analysis(complete) == []


def test_audit_analysis_detects_missing_fields():
    from scripts.analyzer import audit_analysis

    incomplete = {
        "summary": "",
        "core_features": [],
        "use_cases": None,
        "highlights": ["h1"],
        "competitive_comparison": "  ",
    }
    missing = audit_analysis(incomplete)
    assert "summary" in missing
    assert "core_features" in missing
    assert "use_cases" in missing
    assert "competitive_comparison" in missing
    assert "maturity" in missing
    assert "trend_signal" in missing


def test_normalize_analysis_coerces_list_typed_string_fields():
    """LLM 偶尔把 string 字段返回成数组，normalize 必须把它们变回 str。

    回归 2026-09-19 RSS 渲染崩溃：use_cases/competitive_comparison 被返回为 list，
    传到 html.escape 时触发 AttributeError: 'list' object has no attribute 'replace'。
    """
    from scripts.analyzer import _normalize_analysis

    raw = {
        "summary": ["一句话摘要"],
        "use_cases": ["场景一", "场景二"],
        "competitive_comparison": ["对比项 A", "对比项 B"],
        "maturity": ["早期项目"],
        "trend_signal": ["信号 X"],
        "highlights": ["亮点 1"],
        "core_features": ["特性 1", "特性 2"],
    }
    normalized = _normalize_analysis(raw)

    for field in ("summary", "use_cases", "competitive_comparison",
                  "maturity", "trend_signal"):
        assert isinstance(normalized[field], str), f"{field} 应为 str"
        assert normalized[field]  # 不能为空

    for field in ("highlights", "core_features"):
        assert isinstance(normalized[field], list)
        assert all(isinstance(v, str) for v in normalized[field])

    # 多元素 list 应拼接为单个 str，不丢内容
    assert "场景一" in normalized["use_cases"]
    assert "场景二" in normalized["use_cases"]


def test_normalize_analysis_coerces_list_typed_list_fields():
    """list 字段被返回为 str 时应包装成单元素 list；None 应变成空 list。"""
    from scripts.analyzer import _normalize_analysis

    normalized = _normalize_analysis({
        "highlights": "单条亮点",
        "core_features": None,
    })
    assert normalized["highlights"] == ["单条亮点"]
    assert normalized["core_features"] == []


def test_normalize_analysis_preserves_correct_types():
    """类型已正确的输入应原样返回（不丢字段、不改值）。"""
    from scripts.analyzer import _normalize_analysis

    raw = {
        "summary": "正确摘要",
        "use_cases": "正确场景",
        "competitive_comparison": "正确对比",
        "maturity": "成熟",
        "trend_signal": "信号",
        "highlights": ["h1", "h2"],
        "core_features": ["f1"],
    }
    normalized = _normalize_analysis(raw)
    assert normalized == raw


def test_analyze_repo_normalizes_list_typed_llm_output():
    """端到端回归：mock LLM 返回 list 类型的 use_cases，
    analyzer 出口应为 str，避免下游 renderer/rss 崩溃。"""
    from scripts.analyzer import Analyzer

    class ListTypedMockChat:
        def __init__(self):
            self.completions = self

        def create(self, **kwargs):
            if kwargs.get("response_format", {}).get("type") == "json_object":
                return MockCompletion(
                    '{"summary": "Rust 1.78 发布", '
                    '"use_cases": ["Rust 开发者", "嵌入式团队"], '
                    '"competitive_comparison": ["比 Go 快", "比 C++ 安全"], '
                    '"maturity": "已发布稳定版", '
                    '"trend_signal": "Rust 生态扩张", '
                    '"highlights": ["编译器诊断增强"], '
                    '"core_features": ["proc-macro 改进"]}'
                )
            return MockCompletion("plain text")

    class ListTypedMockOpenAI:
        def __init__(self, **kwargs):
            self.chat = ListTypedMockChat()

    analyzer = Analyzer(client=ListTypedMockOpenAI())
    result = analyzer.analyze_repo({
        "full_name": "test/repo",
        "description": "test",
        "readme": "readme",
    })

    # LLM 返回了 list，但出口必须是 str，否则 html.escape 会崩
    assert isinstance(result["use_cases"], str)
    assert isinstance(result["competitive_comparison"], str)
    assert "Rust 开发者" in result["use_cases"]
    assert "嵌入式团队" in result["use_cases"]
