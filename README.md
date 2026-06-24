# Auto-Trend

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![GitHub Actions](https://img.shields.io/badge/CI-GitHub%20Actions-2088FF?logo=githubactions&logoColor=white)](https://github.com/features/actions)
[![GitHub Pages](https://img.shields.io/badge/Live-GitHub%20Pages-blue?logo=github)](https://int2t05.github.io/auto-trend/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

LLM-powered daily GitHub Trending analysis, auto-published to GitHub Pages.

[中文说明](README_CN.md)

---

## Fork & Deploy

**5 minutes to your own trending report.**

### 1. Fork this repo

Fork → uncheck "Copy the `master` branch only" → Create fork.

### 2. Enable GitHub Actions

Your repo → Settings → Actions → General → Allow all actions.

### 3. Set secrets

Settings → Secrets and variables → Actions → New repository secret:

| Secret | Description |
|--------|-------------|
| `LLM_API_KEY` | Your LLM API key (**required**) |
| `LLM_BASE_URL` | API endpoint (optional, defaults to OpenAI) |
| `LLM_MODEL` | Model name (optional, defaults to `gpt-4.1-mini`) |
| `DAILY_REPO_LIMIT` | Max repos per run (optional, defaults to `20`) |

### 4. Enable GitHub Pages

Settings → Pages → Source: **Deploy from a branch** → Branch: `master` / `/docs`.

### 5. Replace URLs

Replace `int2t05` with your GitHub username in these files:

| File | Lines to update |
|------|-----------------|
| `docs/_layouts/default.html` | GitHub link (line 406), footer (line 446) |
| `docs/index.md` | Footer link (line 14) |
| `README.md` | Badge URL, Live Reports link |

```bash
grep -r "int2t05" --include="*.md" --include="*.html" --include="*.js" --include="*.json" .
```

### 6. Trigger first run

Actions → Daily Trending Report → Run workflow. Your first report appears at:

```
https://<your-username>.github.io/auto-trend/
```

---

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

Each repo is analyzed across 6 dimensions: **summary**, **technical highlights**, **use cases**, **competitive comparison**, **maturity**, and **trend signal**.

## Local Dev

```bash
pip install -r requirements.txt

export LLM_API_KEY=sk-your-key
export LLM_BASE_URL=https://api.openai.com/v1   # optional
export LLM_MODEL=gpt-4.1-mini                   # optional
export DAILY_REPO_LIMIT=20                      # optional

python scripts/main.py
# Non-CI environments skip git commit/push
```

Compatible with OpenAI, Anthropic, DeepSeek, or any OpenAI-compatible endpoint.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_API_KEY` | LLM API key | **required** |
| `LLM_BASE_URL` | API endpoint | `https://api.openai.com/v1` |
| `LLM_MODEL` | Model name | `gpt-4.1-mini` |
| `DAILY_REPO_LIMIT` | Max repos per run | `20` |

## Project Structure

```
auto-trend/
├── .github/workflows/daily.yml    # Cron trigger
├── scripts/                       # Pipeline
│   ├── main.py                    # Orchestrator
│   ├── config.py                  # Env config
│   ├── fetcher.py                 # Scraper + README fetcher
│   ├── analyzer.py                # LLM analysis (OpenAI SDK)
│   └── renderer.py                # Markdown report generator
├── prompts/analysis.md            # LLM system prompt
├── tests/                         # pytest (unit)
├── e2e/                           # Playwright (E2E)
├── docs/                          # GitHub Pages (Jekyll)
│   ├── _layouts/default.html      # Apple-style 3-col layout
│   ├── daily/                     # Generated reports
│   └── index.md                   # Report index
├── requirements.txt
└── package.json                   # E2E dependencies
```

## Testing

```bash
# Unit
pip install -r requirements.txt
pytest tests/ -v

# E2E
npm install
npx playwright test
```

## Live Reports

**[int2t05.github.io/auto-trend](https://int2t05.github.io/auto-trend/)**

## License

MIT — see [LICENSE](LICENSE).
