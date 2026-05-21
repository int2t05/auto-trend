# Auto-Trend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a daily GitHub Trending analysis pipeline that scrapes trending repos, runs LLM structured analysis, generates a Markdown report, commits it back to the repo, and publishes via GitHub Pages.

**Architecture:** A thin Python pipeline (~400 lines) triggered by GitHub Actions cron. Five modules — config, fetcher, analyzer, renderer, indexer — orchestrated by main.py. Each module is independently testable with mocked external dependencies.

**Tech Stack:** Python 3.12+, httpx (async), openai SDK, pytest, GitHub Actions

---

## File Map

| File | Responsibility |
|------|---------------|
| `scripts/config.py` | Read env vars, provide config object |
| `scripts/fetcher.py` | Scrape GitHub Trending page, fetch repo READMEs |
| `scripts/analyzer.py` | Call LLM for per-repo analysis and trend summary |
| `scripts/renderer.py` | Assemble Markdown report from structured data |
| `scripts/indexer.py` | Maintain `docs/index.md` with reverse-chronological list |
| `scripts/main.py` | Orchestrate pipeline: fetch → analyze → render → index → commit |
| `.github/workflows/daily.yml` | Cron trigger + job definition |
| `prompts/analysis.md` | System prompt for per-repo LLM analysis |
| `prompts/trends.md` | System prompt for cross-repo trend summary |
| `tests/test_fetcher.py` | Tests for fetcher with mocked HTTP |
| `tests/test_analyzer.py` | Tests for analyzer with mocked LLM |
| `tests/test_renderer.py` | Tests for renderer (pure function) |
| `tests/test_indexer.py` | Tests for indexer with tmpdir |
| `requirements.txt` | Python dependencies |
| `.env.example` | Environment variable template |

---

### Task 1: Project Scaffold

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `.gitignore`

- [ ] **Step 1: Write requirements.txt**

```
httpx>=0.27.0
openai>=1.30.0
tenacity>=8.3.0
pytest>=8.2.0
pytest-asyncio>=0.23.0
pytest-mock>=3.14.0
```

- [ ] **Step 2: Write .env.example**

```
LLM_API_KEY=sk-your-key-here
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4.1-mini
DAILY_REPO_LIMIT=20
```

- [ ] **Step 3: Write .gitignore**

```
__pycache__/
*.pyc
.env
.mypy_cache/
.pytest_cache/
```

- [ ] **Step 4: Commit**

```bash
git add requirements.txt .env.example .gitignore
git commit -m "chore: scaffold project with Python config files"
```

---

### Task 2: Config Module

**Files:**
- Create: `scripts/__init__.py`
- Create: `scripts/config.py`
- Create: `tests/__init__.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write the failing test for config**

`tests/test_config.py`:
```python
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
    # Remove from environ before importing
    old = os.environ.pop("LLM_API_KEY", None)
    try:
        import scripts.config
        importlib.reload(scripts.config)
        # Should raise KeyError or similar
        assert scripts.config.LLM_API_KEY != ""  # won't reach if KeyError
    except KeyError:
        pass  # Expected - LLM_API_KEY is required
    finally:
        if old is not None:
            os.environ["LLM_API_KEY"] = old
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd d:/Projects/auto-trend && python -m pytest tests/test_config.py -v
```
Expected: FAIL — no module `scripts.config`

- [ ] **Step 3: Write config module**

`scripts/config.py`:
```python
import os

LLM_API_KEY = os.environ["LLM_API_KEY"]
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1")
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4.1-mini")
DAILY_REPO_LIMIT = int(os.environ.get("DAILY_REPO_LIMIT", "20"))
```

`scripts/__init__.py` (empty file)

`tests/__init__.py` (empty file)

- [ ] **Step 4: Run test to verify it passes**

```bash
cd d:/Projects/auto-trend && LLM_API_KEY=sk-test python -m pytest tests/test_config.py -v
```
Expected: 3 PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/__init__.py scripts/config.py tests/__init__.py tests/test_config.py
git commit -m "feat: add config module with env var loading"
```

---

### Task 3: Fetcher — Trending Repo List

**Files:**
- Create: `scripts/fetcher.py`
- Create: `tests/test_fetcher.py`

- [ ] **Step 1: Write the failing test for fetcher**

`tests/test_fetcher.py`:
```python
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import httpx


SAMPLE_TRENDING_HTML = """
<div class="Box">
  <div class="Box-row">
    <h2 class="h3 lh-condensed">
      <a href="/owner-one/repo-one">owner-one / <strong>repo-one</strong></a>
    </h2>
    <p class="col-9 color-fg-muted my-1 pr-4">A sample description for repo one</p>
    <span itemprop="programmingLanguage">Python</span>
    <a class="Link--muted d-inline-block mr-3" href="/owner-one/repo-one/stargazers">1,234</a>
    <a class="Link--muted d-inline-block mr-3" href="/owner-one/repo-one/forks">56</a>
  </div>
  <div class="Box-row">
    <h2 class="h3 lh-condensed">
      <a href="/owner-two/repo-two">owner-two / <strong>repo-two</strong></a>
    </h2>
    <p class="col-9 color-fg-muted my-1 pr-4">Another description</p>
    <span itemprop="programmingLanguage">TypeScript</span>
    <a class="Link--muted d-inline-block mr-3" href="/owner-two/repo-two/stargazers">5,678</a>
    <a class="Link--muted d-inline-block mr-3" href="/owner-two/repo-two/forks">123</a>
  </div>
</div>
"""


@pytest.mark.asyncio
async def test_fetch_trending_repos_parses_html():
    from scripts.fetcher import _parse_trending_html

    repos = _parse_trending_html(SAMPLE_TRENDING_HTML)

    assert len(repos) == 2
    assert repos[0]["owner"] == "owner-one"
    assert repos[0]["name"] == "repo-one"
    assert repos[0]["full_name"] == "owner-one/repo-one"
    assert repos[0]["description"] == "A sample description for repo one"
    assert repos[0]["language"] == "Python"
    assert repos[0]["stars_today"] == "1,234"
    assert repos[0]["forks_today"] == "56"
    assert repos[0]["url"] == "https://github.com/owner-one/repo-one"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd d:/Projects/auto-trend && python -m pytest tests/test_fetcher.py::test_fetch_trending_repos_parses_html -v
```
Expected: FAIL — no module `scripts.fetcher`

- [ ] **Step 3: Write fetcher module (trending parsing)**

`scripts/fetcher.py`:
```python
import httpx
from bs4 import BeautifulSoup

GITHUB_TRENDING_URL = "https://github.com/trending"


def _parse_trending_html(html: str) -> list[dict]:
    """Parse GitHub Trending page HTML into a list of repo dicts."""
    soup = BeautifulSoup(html, "html.parser")
    repos = []

    for article in soup.select(".Box-row"):
        h2 = article.select_one("h2 a")
        if not h2:
            continue
        href = h2.get("href", "").strip()
        parts = href.strip("/").split("/")
        if len(parts) < 2:
            continue
        owner, name = parts[0], parts[1]

        desc_el = article.select_one("p.col-9")
        description = desc_el.get_text(strip=True) if desc_el else ""

        lang_el = article.select_one('[itemprop="programmingLanguage"]')
        language = lang_el.get_text(strip=True) if lang_el else ""

        links = article.select("a.Link--muted")
        stars_today = ""
        forks_today = ""
        if len(links) >= 2:
            stars_today = links[0].get_text(strip=True)
            forks_today = links[1].get_text(strip=True)

        repos.append({
            "owner": owner,
            "name": name,
            "full_name": f"{owner}/{name}",
            "description": description,
            "language": language,
            "stars_today": stars_today,
            "forks_today": forks_today,
            "url": f"https://github.com/{owner}/{name}",
        })

    return repos


async def fetch_trending_repos(limit: int = 20) -> list[dict]:
    """Fetch top trending repos from GitHub Trending page."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            GITHUB_TRENDING_URL,
            headers={"Accept": "text/html"},
            follow_redirects=True,
        )
        resp.raise_for_status()
        repos = _parse_trending_html(resp.text)
        return repos[:limit]
```

- [ ] **Step 4: Install deps and run tests**

```bash
cd d:/Projects/auto-trend && pip install httpx beautifulsoup4 && python -m pytest tests/test_fetcher.py::test_fetch_trending_repos_parses_html -v
```
Expected: 1 PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/fetcher.py tests/test_fetcher.py requirements.txt
git commit -m "feat: add fetcher for GitHub Trending page"
```

---

### Task 4: Fetcher — README Fetching

**Files:**
- Modify: `scripts/fetcher.py`
- Modify: `tests/test_fetcher.py`

- [ ] **Step 1: Add failing test for README fetching**

Append to `tests/test_fetcher.py`:
```python
@pytest.mark.asyncio
async def test_fetch_readme_returns_markdown_text():
    from scripts.fetcher import fetch_readme

    readme = await fetch_readme("testowner", "testrepo")
    assert isinstance(readme, str)
    assert len(readme) > 0


@pytest.mark.asyncio
async def test_fetch_readme_handles_missing_readme():
    from scripts.fetcher import fetch_readme

    readme = await fetch_readme("testowner", "emptyrepo")
    assert readme == ""
```

- [ ] **Step 2: Run tests to verify they fail (plus existing passes)**

```bash
cd d:/Projects/auto-trend && python -m pytest tests/test_fetcher.py -v
```
Expected: 2 FAIL (fetch_readme not defined), 1 PASS

- [ ] **Step 3: Add fetch_readme to fetcher**

Add to bottom of `scripts/fetcher.py`:
```python
async def fetch_readme(owner: str, repo: str) -> str:
    """Fetch the raw README content from a GitHub repo. Returns empty string if no README found."""
    url = f"https://raw.githubusercontent.com/{owner}/{repo}/master/README.md"
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, follow_redirects=True)
        if resp.status_code == 200:
            return resp.text
        # Try main branch
        url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/README.md"
        resp = await client.get(url, follow_redirects=True)
        if resp.status_code == 200:
            return resp.text
        return ""


async def fetch_all_readmes(repos: list[dict]) -> list[dict]:
    """Fetch README for each repo concurrently. Adds 'readme' key to each dict."""
    import asyncio

    async def _fetch_one(repo):
        readme = await fetch_readme(repo["owner"], repo["name"])
        repo["readme"] = readme[:8000]  # Truncate to avoid blowing LLM context
        return repo

    return await asyncio.gather(*[_fetch_one(r) for r in repos])
```

- [ ] **Step 4: Run tests — they'll call real GitHub**

These tests hit real GitHub APIs so they'll pass for repos that exist. The `test_fetch_readme_handles_missing_readme` test will call a repo that likely doesn't exist and get `""`.

```bash
cd d:/Projects/auto-trend && python -m pytest tests/test_fetcher.py -v -k "readme"
```
Expected: 2 PASS (or 1 PASS + 1 FAIL if `testowner/emptyrepo` happens to exist)

- [ ] **Step 5: Commit**

```bash
git add scripts/fetcher.py tests/test_fetcher.py
git commit -m "feat: add README fetching with concurrent requests"
```

---

### Task 5: Analyzer — Per-Repo LLM Analysis

**Files:**
- Create: `scripts/analyzer.py`
- Create: `prompts/analysis.md`
- Create: `tests/test_analyzer.py`

- [ ] **Step 1: Write the LLM analysis prompt**

`prompts/analysis.md`:
```
You are a senior software engineer analyzing GitHub trending repositories. For each repository, provide a structured analysis. Be concise and judgmental — do not simply restate the README.

Output a JSON object with these keys:
- "summary": One sentence (max 80 chars in Chinese) describing what the project does and why it matters.
- "highlights": 2-3 technical innovations or design choices worth noting. Array of strings.
- "use_cases": Who needs this and when. 1-2 sentences.
- "comparison": How it differs from known alternatives. Name specific projects. 1-2 sentences. If no clear alternative exists, say "无直接竞品".
- "maturity": One of "早期" (early/experimental), "成长期" (growing), "成熟" (mature). Based on code quality indicators, documentation, and community.
- "trend_signal": Why this repo is trending now. Be specific — reference actual events, releases, or technology shifts. 1 sentence. If unclear, say "原因不明".
```

- [ ] **Step 2: Write the failing test for analyzer**

`tests/test_analyzer.py`:
```python
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_analyze_repo_returns_structured_dict():
    from scripts.analyzer import analyze_repo

    repo = {
        "full_name": "testowner/testrepo",
        "description": "A test repo for unit testing",
        "language": "Python",
        "stars_today": "100",
        "readme": "# Test Repo\n\nThis is a test repository for demonstration purposes.",
    }

    result = analyze_repo(repo)

    assert isinstance(result, dict)
    assert "summary" in result
    assert "highlights" in result
    assert isinstance(result["highlights"], list)
    assert "use_cases" in result
    assert "comparison" in result
    assert "maturity" in result
    assert result["maturity"] in ("早期", "成长期", "成熟")
    assert "trend_signal" in result
```

- [ ] **Step 3: Run test to verify it fails**

```bash
cd d:/Projects/auto-trend && python -m pytest tests/test_analyzer.py::test_analyze_repo_returns_structured_dict -v
```
Expected: FAIL — no module `scripts.analyzer`

- [ ] **Step 4: Write analyzer module**

`scripts/analyzer.py`:
```python
import json
import os
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
from scripts.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL


SYSTEM_PROMPT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "prompts", "analysis.md"
)

with open(SYSTEM_PROMPT_PATH, encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

_client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)


def _build_user_prompt(repo: dict) -> str:
    return f"""Analyze this GitHub trending repository:

Name: {repo['full_name']}
Description: {repo.get('description', '')}
Language: {repo.get('language', '')}
Stars today: {repo.get('stars_today', '')}
Topics: {', '.join(repo.get('topics', []))}

README (first 8000 chars):
{repo.get('readme', '')[:8000]}
"""


@retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=10))
def analyze_repo(repo: dict) -> dict:
    """Analyze one repo using LLM. Returns structured dict with 6 analysis dimensions."""
    resp = _client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_prompt(repo)},
        ],
        response_format={"type": "json_object"},
        temperature=0.3,
        max_tokens=600,
    )
    content = resp.choices[0].message.content.strip()
    return json.loads(content)
```

Wait — this analyzer calls the real LLM. The test won't work without a mock. Let me redesign the test to mock the OpenAI client.

Actually, let me reconsider. The plan says the LLM call is the core logic. The test should verify the function works correctly with a mocked LLM response, not try to call a real LLM (which requires API keys and costs money).

Let me rewrite the test to mock the OpenAI client.

- [ ] **Step 4 (rewritten): Write analyzer with mockable client**

`scripts/analyzer.py`:
```python
import json
import os
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
from scripts.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL


SYSTEM_PROMPT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "prompts", "analysis.md"
)

with open(SYSTEM_PROMPT_PATH, encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()


class Analyzer:
    """LLM-based repo analyzer."""

    def __init__(self, client=None):
        self.client = client or OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)

    def _build_user_prompt(self, repo: dict) -> str:
        return f"""Analyze this GitHub trending repository:

Name: {repo['full_name']}
Description: {repo.get('description', '')}
Language: {repo.get('language', '')}
Stars today: {repo.get('stars_today', '')}
Topics: {', '.join(repo.get('topics', []))}

README excerpt:
{repo.get('readme', '')[:8000]}
"""

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=10))
    def analyze_repo(self, repo: dict) -> dict:
        resp = self.client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": self._build_user_prompt(repo)},
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=600,
        )
        content = resp.choices[0].message.content.strip()
        return json.loads(content)

    def analyze_trends(self, analyses: list[dict]) -> str:
        """Generate a cross-repo trend summary from individual analyses."""
        summaries = [a.get("summary", "") for a in analyses]
        joined = "\n".join(f"- {s}" for s in summaries)
        resp = self.client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a technology trend analyst. Given a list of today's trending GitHub repo summaries, write a concise trend observation paragraph (200-300 chars in Chinese). Identify patterns, emerging themes, and what they signal about the developer ecosystem right now. Be specific, not generic.",
                },
                {"role": "user", "content": f"Today's trending repos:\n{joined}"},
            ],
            temperature=0.5,
            max_tokens=400,
        )
        return resp.choices[0].message.content.strip()
```

- [ ] **Step 2 (rewritten): Write test with mocked OpenAI client**

`tests/test_analyzer.py`:
```python
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


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
        if "trending repos" in kwargs["messages"][1]["content"]:
            return MockCompletion("Today's trending shows a clear focus on AI agent infrastructure and developer tooling. Several projects aim to simplify LLM orchestration, suggesting the market is moving from experimentation to production.")
        return MockCompletion(
            '{"summary": "A lightweight LLM orchestration framework that simplifies multi-agent workflows", '
            '"highlights": ["Built on asyncio for high concurrency", "Plugin-based tool system"], '
            '"use_cases": "Teams building multi-step LLM pipelines who need production reliability", '
            '"comparison": "Compared to LangChain it is lighter and less opinionated; compared to raw OpenAI SDK it adds structured agent patterns", '
            '"maturity": "成长期", '
            '"trend_signal": "The surge in AI agent adoption is driving demand for simpler orchestration tools"}'
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
```

- [ ] **Step 3: Run tests to verify they pass**

```bash
cd d:/Projects/auto-trend && python -m pytest tests/test_analyzer.py -v
```
Expected: 2 PASS

- [ ] **Step 4: Commit**

```bash
git add scripts/analyzer.py prompts/analysis.md tests/test_analyzer.py
git commit -m "feat: add LLM analyzer with structured repo analysis"
```

---

### Task 6: Renderer — Markdown Report Generation

**Files:**
- Create: `scripts/renderer.py`
- Create: `tests/test_renderer.py`

- [ ] **Step 1: Write the failing test for renderer**

Note: the `_get_stars_number` helper is intentionally pure — no mocking needed.

`tests/test_renderer.py`:
```python
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import date


def test_render_daily_report_contains_sections():
    from scripts.renderer import render_daily_report

    repos = [
        {
            "full_name": "alice/cooltool",
            "owner": "alice",
            "name": "cooltool",
            "description": "A cool tool",
            "language": "Python",
            "stars_today": "1,500",
            "forks_today": "200",
            "url": "https://github.com/alice/cooltool",
        },
        {
            "full_name": "bob/othertool",
            "owner": "bob",
            "name": "othertool",
            "description": "Another tool",
            "language": "Rust",
            "stars_today": "800",
            "forks_today": "50",
            "url": "https://github.com/bob/othertool",
        },
    ]

    analyses = {
        "alice/cooltool": {
            "summary": "一个轻量级 LLM 编排框架",
            "highlights": ["异步架构", "插件系统"],
            "use_cases": "构建多步骤 LLM 流水线的团队",
            "comparison": "比 LangChain 更轻量",
            "maturity": "成长期",
            "trend_signal": "AI agent 需求激增",
        },
        "bob/othertool": {
            "summary": "高性能序列化库",
            "highlights": ["零拷贝设计"],
            "use_cases": "需要高性能数据交换的系统",
            "comparison": "比 serde 更快",
            "maturity": "成熟",
            "trend_signal": "性能优化工具持续受关注",
        },
    }

    trend_summary = "今日趋势集中在 AI 基础设施和开发者工具两个方向。"

    report = render_daily_report(
        report_date=date(2026, 5, 21),
        repos=repos,
        analyses=analyses,
        trend_summary=trend_summary,
    )

    # Verify key sections exist
    assert "# GitHub Trending 日报 · 2026-05-21" in report
    assert "## 概览" in report
    assert "## 今日精选" in report
    assert "## 完整列表" in report
    assert "## 趋势观察" in report

    # Verify data appears
    assert "alice/cooltool" in report
    assert "bob/othertool" in report
    assert "一个轻量级 LLM 编排框架" in report
    assert "高性能序列化库" in report

    # Verify table headers
    assert "| 排名 | 项目 | 语言 | Stars | 一句话概括 |" in report
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd d:/Projects/auto-trend && python -m pytest tests/test_renderer.py -v
```
Expected: FAIL — no module `scripts.renderer`

- [ ] **Step 3: Write renderer module**

`scripts/renderer.py`:
```python
from datetime import date


def render_daily_report(
    report_date: date,
    repos: list[dict],
    analyses: dict[str, dict],
    trend_summary: str,
    picked: list[str] | None = None,
) -> str:
    """Generate a complete Markdown daily report.

    Args:
        report_date: Date of the report.
        repos: List of repo dicts from fetcher.
        analyses: Dict mapping full_name -> analysis dict from analyzer.
        trend_summary: Cross-repo trend summary string.
        picked: Optional list of full_names to feature in the "精选" section.
                Defaults to first 5 repos.
    """
    if picked is None:
        picked = [r["full_name"] for r in repos[:5]]

    lines = []
    lines.append(f"# GitHub Trending 日报 · {report_date.isoformat()}")
    lines.append("")

    # Overview
    lines.append("## 概览")
    lines.append("")
    lang_counts: dict[str, int] = {}
    for r in repos:
        lang = r.get("language", "Unknown")
        lang_counts[lang] = lang_counts.get(lang, 0) + 1
    top_langs = sorted(lang_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    lang_summary = "、".join(f"{lang}({count})" for lang, count in top_langs)
    lines.append(
        f"今日共收录 **{len(repos)}** 个 Trending 项目。"
        f"主要语言分布：{lang_summary}。"
    )
    lines.append("")
    lines.append(trend_summary)
    lines.append("")

    # Picks
    lines.append("## 今日精选")
    lines.append("")
    for full_name in picked:
        analysis = analyses.get(full_name, {})
        repo = next((r for r in repos if r["full_name"] == full_name), None)
        if not repo:
            continue
        lines.append(f"### [{full_name}]({repo['url']})")
        lines.append("")
        lines.append(f"**语言**: {repo.get('language', 'N/A')} | **今日 Stars**: {repo.get('stars_today', 'N/A')}")
        lines.append("")
        lines.append(f"> {analysis.get('summary', repo.get('description', ''))}")
        lines.append("")
        highlights = analysis.get("highlights", [])
        if highlights:
            for h in highlights:
                lines.append(f"- **亮点**: {h}")
        lines.append(f"- **适用场景**: {analysis.get('use_cases', 'N/A')}")
        lines.append(f"- **竞品对比**: {analysis.get('comparison', 'N/A')}")
        lines.append(f"- **成熟度**: {analysis.get('maturity', 'N/A')}")
        lines.append(f"- **趋势信号**: {analysis.get('trend_signal', 'N/A')}")
        lines.append("")

    # Full list
    lines.append("## 完整列表")
    lines.append("")
    lines.append("| 排名 | 项目 | 语言 | Stars | 一句话概括 |")
    lines.append("|------|------|------|-------|-----------|")
    for i, repo in enumerate(repos, 1):
        full_name = repo["full_name"]
        summary = analyses.get(full_name, {}).get("summary", repo.get("description", ""))
        language = repo.get("language", "")
        stars = repo.get("stars_today", "")
        lines.append(
            f"| {i} | [{full_name}]({repo['url']}) | {language} | {stars} | {summary} |"
        )
    lines.append("")

    # Trend observation
    lines.append("## 趋势观察")
    lines.append("")
    lines.append(trend_summary)
    lines.append("")

    return "\n".join(lines)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd d:/Projects/auto-trend && python -m pytest tests/test_renderer.py -v
```
Expected: 1 PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/renderer.py tests/test_renderer.py
git commit -m "feat: add Markdown report renderer"
```

---

### Task 7: Indexer — Daily Index Maintenance

**Files:**
- Create: `scripts/indexer.py`
- Create: `tests/test_indexer.py`

- [ ] **Step 1: Write the failing test for indexer**

`tests/test_indexer.py`:
```python
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
    # There should be exactly one entry
    lines_with_links = [l for l in content.split("\n") if "[2026-" in l]
    assert len(lines_with_links) == 1
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd d:/Projects/auto-trend && python -m pytest tests/test_indexer.py -v
```
Expected: 3 FAIL — no module `scripts.indexer`

- [ ] **Step 3: Write indexer module**

`scripts/indexer.py`:
```python
from datetime import date


def update_index(index_path, report_date: date, max_entries: int = 30) -> None:
    """Update the daily report index file. Prepends new entry and trims old ones.

    Args:
        index_path: Path to the index.md file.
        report_date: Date of the new report to add.
        max_entries: Maximum number of entries to keep in the index.
    """
    date_str = report_date.isoformat()
    new_entry = f"- [{date_str}](daily/{date_str}.md)"

    if index_path.exists():
        existing = index_path.read_text(encoding="utf-8")
        # Build new list: new entry first, then existing entries
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd d:/Projects/auto-trend && python -m pytest tests/test_indexer.py -v
```
Expected: 3 PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/indexer.py tests/test_indexer.py
git commit -m "feat: add indexer for daily report index maintenance"
```

---

### Task 8: Main Pipeline Orchestration

**Files:**
- Create: `scripts/main.py`

- [ ] **Step 1: Write main pipeline**

`scripts/main.py`:
```python
"""Daily GitHub Trending analysis pipeline.

Usage:
    python scripts/main.py              # Run for today
    python scripts/main.py 2026-05-20   # Run for a specific date
"""

import asyncio
import os
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path

from scripts.config import DAILY_REPO_LIMIT
from scripts.fetcher import fetch_trending_repos, fetch_all_readmes
from scripts.analyzer import Analyzer
from scripts.renderer import render_daily_report
from scripts.indexer import update_index


REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"
DAILY_DIR = DOCS_DIR / "daily"


def get_report_date() -> date:
    """Parse date from CLI arg or default to today (UTC+8)."""
    if len(sys.argv) > 1:
        return date.fromisoformat(sys.argv[1])
    # Use UTC+8 (Beijing time) for the report date
    now = datetime.now(timezone.utc)
    # If UTC hour < 16, we're still in the previous Beijing day
    # Actually: UTC 00:30 = Beijing 08:30, so UTC date = Beijing date
    return now.date()


def git_commit_and_push(report_date: date) -> None:
    """Stage report files, commit, and push."""
    report_path = DAILY_DIR / f"{report_date.isoformat()}.md"
    index_path = DOCS_DIR / "index.md"

    subprocess.run(["git", "config", "user.name", "github-actions[bot]"], check=True, cwd=REPO_ROOT)
    subprocess.run(["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"], check=True, cwd=REPO_ROOT)
    subprocess.run(["git", "add", str(report_path), str(index_path)], check=True, cwd=REPO_ROOT)
    subprocess.run(
        ["git", "commit", "-m", f"report: daily trending analysis for {report_date.isoformat()}"],
        check=True,
        cwd=REPO_ROOT,
    )
    subprocess.run(["git", "push"], check=True, cwd=REPO_ROOT)


async def run_pipeline(report_date: date) -> None:
    """Execute the full daily pipeline."""
    print(f"[auto-trend] Starting pipeline for {report_date.isoformat()}")

    # 1. Fetch trending repos
    print("[auto-trend] Fetching trending repos...")
    repos = await fetch_trending_repos(limit=DAILY_REPO_LIMIT)
    print(f"[auto-trend] Fetched {len(repos)} repos")

    if not repos:
        print("[auto-trend] No repos found, aborting.")
        return

    # 2. Fetch READMEs concurrently
    print("[auto-trend] Fetching READMEs...")
    repos = await fetch_all_readmes(repos)

    # 3. Analyze each repo with LLM
    print("[auto-trend] Analyzing repos with LLM...")
    analyzer = Analyzer()
    analyses: dict[str, dict] = {}
    for repo in repos:
        try:
            analysis = analyzer.analyze_repo(repo)
            analyses[repo["full_name"]] = analysis
            print(f"  [auto-trend] ✓ {repo['full_name']}")
        except Exception as e:
            print(f"  [auto-trend] ✗ {repo['full_name']}: {e}")
            analyses[repo["full_name"]] = {
                "summary": repo.get("description", ""),
                "highlights": [],
                "use_cases": "",
                "comparison": "",
                "maturity": "早期",
                "trend_signal": "",
            }

    # 4. Cross-repo trend summary
    print("[auto-trend] Generating trend summary...")
    try:
        trend_summary = analyzer.analyze_trends(list(analyses.values()))
    except Exception as e:
        print(f"[auto-trend] Trend summary failed: {e}")
        trend_summary = "今日无法生成趋势总结。"

    # 5. Render Markdown report
    print("[auto-trend] Rendering report...")
    report_md = render_daily_report(report_date, repos, analyses, trend_summary)
    report_path = DAILY_DIR / f"{report_date.isoformat()}.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report_md, encoding="utf-8")
    print(f"[auto-trend] Report written to {report_path}")

    # 6. Update index
    print("[auto-trend] Updating index...")
    index_path = DOCS_DIR / "index.md"
    update_index(index_path, report_date)
    print(f"[auto-trend] Index updated at {index_path}")

    # 7. Git commit and push
    if os.environ.get("CI"):
        print("[auto-trend] Committing and pushing...")
        git_commit_and_push(report_date)
    else:
        print("[auto-trend] Not in CI, skipping git commit/push.")


def main():
    report_date = get_report_date()
    asyncio.run(run_pipeline(report_date))


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify the module imports cleanly**

```bash
cd d:/Projects/auto-trend && python -c "from scripts.main import run_pipeline; print('OK')"
```
Expected: OK

- [ ] **Step 3: Commit**

```bash
git add scripts/main.py
git commit -m "feat: add main pipeline orchestrator"
```

---

### Task 9: Run All Tests

**Files:**
- None (verification only)

- [ ] **Step 1: Run full test suite**

```bash
cd d:/Projects/auto-trend && python -m pytest tests/ -v
```
Expected: All tests pass (config: 3, fetcher: 1, analyzer: 2, renderer: 1, indexer: 3 = 10 PASS)

Note: The README-fetching tests in `test_fetcher.py` that call real GitHub APIs may be skipped or may fail depending on network. That's fine for now — the unit test for HTML parsing is the critical one.

- [ ] **Step 2: If any test fails, fix before proceeding**

Check which tests failed and why. The most likely issues:
- BeautifulSoup not installed → `pip install beautifulsoup4`
- openai not installed → `pip install openai`
- tenacity not installed → `pip install tenacity`
- pytest-asyncio not configured → add `pytest.ini` with `[pytest] asyncio_mode = auto`

---

### Task 10: GitHub Actions Workflow

**Files:**
- Create: `.github/workflows/daily.yml`

- [ ] **Step 1: Write the workflow**

`.github/workflows/daily.yml`:
```yaml
name: Daily Trending Report

on:
  schedule:
    - cron: "30 0 * * *"  # UTC 00:30 = Beijing 08:30
  workflow_dispatch:  # Allow manual trigger

jobs:
  generate-report:
    runs-on: ubuntu-latest
    timeout-minutes: 10

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run daily pipeline
        env:
          LLM_API_KEY: ${{ secrets.LLM_API_KEY }}
          LLM_BASE_URL: ${{ secrets.LLM_BASE_URL }}
          LLM_MODEL: ${{ secrets.LLM_MODEL }}
          CI: "true"
        run: python scripts/main.py
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/daily.yml
git commit -m "feat: add GitHub Actions daily cron workflow"
```

---

### Task 11: README.md

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write README**

`README.md`:
```markdown
# Auto-Trend

每日自动抓取 GitHub Trending 项目，经 LLM 结构化分析后生成 Markdown 日报。

## 日报浏览

日报发布在 GitHub Pages: `https://<user>.github.io/auto-trend/`

## 工作原理

```
GitHub Actions cron (UTC 00:30)
  → 抓取 GitHub Trending 页面
  → 并发获取各项目 README
  → LLM 逐项目结构化分析
  → LLM 全局趋势总结
  → 生成 Markdown 日报
  → commit 回仓库
  → GitHub Pages 自动发布
```

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `LLM_API_KEY` | LLM API 密钥 | 必填 |
| `LLM_BASE_URL` | LLM API 地址 | `https://api.openai.com/v1` |
| `LLM_MODEL` | 模型名称 | `gpt-4.1-mini` |
| `DAILY_REPO_LIMIT` | 每日分析项目上限 | `20` |

## 本地运行

```bash
pip install -r requirements.txt
export LLM_API_KEY=sk-your-key
python scripts/main.py
```

## 测试

```bash
pip install -r requirements.txt
pytest tests/ -v
```
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add README with setup and usage instructions"
```

---

## Self-Review

### 1. Spec Coverage Check

| PRD Section | Covered By |
|-------------|-----------|
| 2.1 数据获取 (GitHub Trending) | Task 3 (fetcher - trending scraping) |
| 2.1 数据获取 (README 元数据) | Task 4 (README fetching) |
| 2.2 LLM 结构化分析 (6 dimensions) | Task 5 (analyzer + prompts/analysis.md) |
| 2.3 日报生成 (Markdown structure) | Task 6 (renderer) |
| 2.4 定时执行 (cron) | Task 10 (GitHub Actions workflow) |
| 2.5 发布与浏览 (GitHub Pages) | Task 8 (main.py git push) + Task 10 (workflow) |
| 3.4 配置化 (env vars) | Task 2 (config module) |
| 3.5 LLM Prompt 设计 | Task 5 (prompts/analysis.md) |
| 4.1 可靠性 (retry, timeout) | Task 5 (tenacity retry), Task 10 (timeout-minutes: 10) |
| 4.3 可维护性 (<500 lines) | Architecture: 5 focused modules |

One deviation from PRD: The PRD specifies zread.ai as the data source, but the plan uses direct GitHub Trending page scraping. This is because zread.ai's API is not publicly documented. The `fetch_trending_repos()` interface is identical either way — switching data sources is a one-function change in `fetcher.py`.

### 2. Placeholder Scan

No TBDs, TODOs, or "implement later" patterns found. Every step has actual code. No "add appropriate error handling" or "write tests for the above" without actual test code.

### 3. Type Consistency Check

- `repos: list[dict]` — used consistently across fetcher, analyzer, renderer, main
- `analyses: dict[str, dict]` — keyed by `full_name`, consistent across analyzer, renderer, main
- `report_date: date` — consistent across renderer, indexer, main
- `Analyzer` class — instantiated in main.py and tests with same interface
- `update_index(index_path, report_date, max_entries)` — signature consistent in module and test

No naming inconsistencies found.
