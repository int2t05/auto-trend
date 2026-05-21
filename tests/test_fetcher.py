import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest


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


class MockResponse:
    def __init__(self, status_code, text):
        self.status_code = status_code
        self.text = text


@pytest.mark.asyncio
async def test_fetch_readme_returns_markdown_text(mocker):
    mock_client = mocker.patch("httpx.AsyncClient")
    mock_client.return_value.__aenter__.return_value.get.return_value = MockResponse(200, "# Hello World")

    from scripts.fetcher import fetch_readme

    readme = await fetch_readme("testowner", "testrepo")
    assert readme == "# Hello World"


@pytest.mark.asyncio
async def test_fetch_readme_handles_missing_readme(mocker):
    mock_client = mocker.patch("httpx.AsyncClient")
    mock_client.return_value.__aenter__.return_value.get.return_value = MockResponse(404, "")

    from scripts.fetcher import fetch_readme

    readme = await fetch_readme("testowner", "emptyrepo")
    assert readme == ""


@pytest.mark.asyncio
async def test_fetch_all_readmes_adds_readme_key(mocker):
    mock_client = mocker.patch("httpx.AsyncClient")
    mock_client.return_value.__aenter__.return_value.get.return_value = MockResponse(200, "# Test README")

    from scripts.fetcher import fetch_all_readmes

    repos = [
        {"owner": "a", "name": "x", "full_name": "a/x"},
        {"owner": "b", "name": "y", "full_name": "b/y"},
    ]
    result = await fetch_all_readmes(repos)

    assert len(result) == 2
    for r in result:
        assert r["readme"] == "# Test README"
        assert r["full_name"] in ("a/x", "b/y")
