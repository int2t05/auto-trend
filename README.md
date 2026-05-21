# Auto-Trend

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![GitHub Actions](https://img.shields.io/badge/CI-GitHub%20Actions-2088FF?logo=githubactions&logoColor=white)](https://github.com/features/actions)
[![GitHub Pages](https://img.shields.io/badge/Live-GitHub%20Pages-blue?logo=github)](https://int2t05.github.io/auto-trend/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Daily GitHub Trending scraper with LLM-powered structured analysis, auto-published to GitHub Pages.

## How It Works

```
GitHub Actions cron (UTC 00:30)
  → Scrape GitHub Trending (httpx + BeautifulSoup)
  → Fetch READMEs concurrently (asyncio)
  → LLM structured analysis per repo (JSON mode)
  → Global trend summary
  → Render Markdown report
  → git commit + push
  → GitHub Pages auto-publish
```

Each repo gets analyzed across 6 dimensions: summary, technical highlights, use cases, competitive comparison, maturity assessment, and trend signal.

## Live Reports

Daily reports are published at: **[int2t05.github.io/auto-trend](https://int2t05.github.io/auto-trend/)**

## Quick Start

```bash
# Install
pip install -r requirements.txt

# Configure
export LLM_API_KEY=sk-your-key
export LLM_BASE_URL=https://api.openai.com/v1   # optional
export LLM_MODEL=gpt-4.1-mini                     # optional
export DAILY_REPO_LIMIT=20                        # optional

# Run
python scripts/main.py
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_API_KEY` | LLM API key | **required** |
| `LLM_BASE_URL` | LLM API endpoint | `https://api.openai.com/v1` |
| `LLM_MODEL` | Model name | `gpt-4.1-mini` |
| `DAILY_REPO_LIMIT` | Max repos to analyze | `20` |

Compatible with OpenAI, Anthropic, DeepSeek, or any OpenAI-compatible endpoint.

## Project Structure

```
auto-trend/
├── .github/workflows/daily.yml    # GitHub Actions cron job
├── scripts/                       # Core pipeline
│   ├── main.py                    # Orchestrator
│   ├── config.py                  # Env config
│   ├── fetcher.py                 # HTML scraper + README fetcher
│   ├── analyzer.py                # LLM analysis (OpenAI-compatible)
│   ├── renderer.py                # Markdown report generator
│   └── indexer.py                 # Index page updater
├── prompts/analysis.md            # LLM system prompt
├── tests/                         # Python unit tests (pytest)
├── e2e/                           # Playwright E2E tests
├── docs/                          # GitHub Pages source (Jekyll)
│   ├── _layouts/default.html      # Page layout (Apple-style 3-col)
│   ├── daily/                     # Generated daily reports
│   └── index.md                   # Report index
├── requirements.txt               # Python dependencies
└── package.json                   # E2E test dependencies
```

## Testing

```bash
# Unit tests
pip install -r requirements.txt
pytest tests/ -v

# E2E browser tests
npm install
npx playwright test
```

## License

MIT — see [LICENSE](LICENSE).
