# Auto-Trend 技术文档

## 架构总览

```
GitHub Actions cron (UTC 00:17)
  │
  ├─ 1. fetcher.fetch_trending_repos()   抓 GitHub Trending 页面 HTML
  ├─ 1. fetcher.fetch_rss_items()        并发抓 RSS 源（Hacker News、dev.to 等）
  ├─ 2. fetcher.fetch_all_readmes()       并发抓各项目 README (raw.githubusercontent.com)
  │
  ├─ 3. analyzer.analyze_repo()          逐条（repo + RSS item）调 LLM 做 7 维结构化分析
  ├─ 4. analyzer.analyze_trends()         跨条目趋势总结
  │
  ├─ 5. renderer.render_daily_report()   组装 Markdown 日报
  ├─ 6. rss.render_rss_feed()            组装 RSS 2.0 XML（feed.xml）
  ├─ 7. verify_report.verify_report()    结构完整性校验，拦截 LLM 截断
  │
  └─ 8. git add + commit + push  →  GitHub Pages 自动发布
```

薄层设计，零数据库，零后端服务。整个 pipeline 由 GitHub Actions 驱动，一个 Python 脚本跑完全程。

## 技术栈

| 层 | 选择 | 说明 |
|---|------|------|
| 语言 | Python 3.12+ | async/await 原生支持 |
| HTTP | httpx (async) | 异步并发抓取，比 requests 快 3-5x |
| HTML 解析 | BeautifulSoup4 | 解析 GitHub Trending 页面 |
| RSS 解析 | feedparser | 解析 RSS/Atom feed |
| LLM SDK | openai | 兼容任何 OpenAI-API 网关 |
| 重试 | tenacity | 指数退避，LLM 调用失败自动重试 3 次 |
| 调度 | GitHub Actions | cron 定时触发，免费 2000 分钟/月 |
| 测试 | pytest + pytest-asyncio + pytest-mock | 异步测试 + mock |
| 发布 | GitHub Pages | 直接渲染 `docs/` 目录下的 Markdown |

## 模块设计

### 1. `scripts/config.py`

环境变量读取层。所有配置通过环境变量注入，代码中无硬编码。

```python
LLM_API_KEY        = os.environ["LLM_API_KEY"]        # 必填
LLM_BASE_URL       = "https://api.openai.com/v1"       # 可选
LLM_MODEL          = "gpt-4.1-mini"                    # 可选
DAILY_REPO_LIMIT   = 20                                # 可选
GITHUB_TOKEN       = ""                                # 可选，提升 GitHub API 配额
RSS_ITEMS_PER_FEED = 10                                # 可选，单 feed 抓取条数
```

`load_feeds()` 读取 `feeds.yml`，文件不存在或为空时返回空列表（降级为纯 GitHub Trending）。

### 2. `scripts/fetcher.py`

**职责**：获取 GitHub Trending 数据 + RSS 热点。

- `_parse_trending_html(html)` — 解析 Trending 页面 DOM，提取项目名、描述、语言、当日 Star 增长
- `_stars_today(article)` — 从 `span` 中提取 `"1,234 stars today"`，返回当日新增 Star 数（与页面上显示的总星数 `a.Link--muted` 区分）
- `fetch_trending_repos(limit)` — GET `github.com/trending`，并行调 GitHub API 补全总星数
- `fetch_readme(owner, repo)` — 从 `raw.githubusercontent.com` 抓 README.md（先试 master 分支，再试 main）
- `fetch_all_readmes(repos)` — `asyncio.gather` 并发抓取，每个 README 截断到 8000 字符
- `fetch_rss_items(feeds)` — 抓取多个 RSS feed，逐 feed 解析，单 feed 失败跳过不中断。每条返回统一 dict，`source` 字段标记来源（如 `rss:Hacker News`）

**GitHub repo 数据格式**：
```python
{
    "owner": "alice",
    "name": "cooltool",
    "full_name": "alice/cooltool",
    "description": "A cool tool",
    "language": "Python",
    "stars_today": 1234,          # 当日新增 Star 数（int），来自 "1,234 stars today"
    "url": "https://github.com/alice/cooltool",
    "total_stars": 100000,        # 由 GitHub API 补全（stargazers_count）
    "source": "github-trending",  # 来源标记
    "readme": "# Cool Tool\n\n..."  # 由 fetch_all_readmes 添加
}
```

**RSS item 数据格式**：
```python
{
    "full_name": "Hacker News · Title",  # "{feed_name} · {entry_title}"
    "description": "entry summary",       # 截断到 500 字符
    "readme": "entry content",            # 截断到 8000 字符
    "url": "entry link",
    "source": "rss:Hacker News",          # rss:{feed_name}
    "language": "",
    "stars_today": 0,
    "total_stars": 0,
}
```

### 3. `scripts/analyzer.py`

**职责**：调 LLM 做结构化分析 + 在 LLM 边界规整字段类型。

- `Analyzer` 类，构造函数接受可选 `client` 参数（便于测试注入 mock）
- `analyze_repo(repo)` — 单条目分析，输出 7 维 JSON：
  - `summary` — 一句话概括（中文 ≤80 字）
  - `highlights` — 1-2 个独特设计或技术决策
  - `core_features` — 2-3 条具体的技术亮点
  - `use_cases` — 适用场景
  - `competitive_comparison` — 竞品对比
  - `maturity` — 成熟度（早期/成长期/成熟）
  - `trend_signal` — 趋势信号
- `_normalize_analysis(analysis)` — 在 `json.loads` 之后立即规整字段类型：string 字段（summary/use_cases/competitive_comparison/maturity/trend_signal）强制为 str，list 字段（highlights/core_features）强制为 `list[str]`。LLM 偶尔把 string 字段返回成数组，这里在边界兜底，避免下游 `html.escape` 崩溃
- `analyze_trends(analyses)` — 跨条目趋势总结，输出 300-500 字中文段落
- 使用 `response_format={"type": "json_object"}` 确保结构化输出
- `@retry(stop=stop_after_attempt(3), wait=exponential)` 指数退避重试 3 次

**System Prompt**：定义在 `prompts/analysis.md`，要求 LLM 做判断而非复述 README。

### 4. `scripts/renderer.py`

**职责**：将结构化数据组装为 Markdown 日报。纯函数，无副作用。

日报结构：
```
# GitHub Trending 日报 · YYYY-MM-DD

## 概览          ← 项目统计 + 语言分布 + LLM 趋势总结

## 项目详情       ← GitHub repos 按当日新增 Star 降序，逐个展开 7 维分析

## RSS 热点       ← RSS items 保持抓取顺序，逐个展开 7 维分析

## 趋势观察       ← LLM 跨条目趋势判断
```

每个 GitHub 项目头部展示当日新增与总星数：
```
 `Python` ⭐ +1,234 今日新增 · 100,000 总星数
```

每个 RSS item 头部展示来源标签：
```
`RSS: Hacker News`
```

### 5. `scripts/rss.py`

**职责**：将 trending repos + RSS 热点渲染为 RSS 2.0 XML（`docs/feed.xml`）。纯函数，无副作用。

- `render_rss_feed(repos, analyses, report_date)` — 每条条目作为一个 `<item>`：
  - title: owner/repo 或 "Feed · Title"
  - link: GitHub URL 或 RSS link
  - pubDate: 日报日期（UTC 00:00，RFC 822）
  - description: LLM summary
  - content:encoded: 完整分析 HTML

GitHub repos 按日增星数降序，RSS items 同序，GitHub repos 在前、RSS items 在后。

### 6. `scripts/verify_report.py`

**职责**：生成后结构完整性校验，拦截 LLM 截断。轻量：只查结构，不查内容质量。

4 项检查：
1. `## 趋势观察` 段存在且后随内容 ≥50 字符
2. 代码块（``` ）配对闭合
3. 每个 `### [repo]` 小节有 summary（`>` 开头行），缺失率 ≤20%
4. 结尾收束（句号/问号/感叹号/分割线收尾）

### 7. `scripts/main.py`

**职责**：编排整个 pipeline。

- 支持命令行指定日期：`python scripts/main.py 2026-05-20`
- 默认取 UTC 当天日期
- `CI` 环境变量控制是否执行 git commit/push（本地运行不 push）
- 每个条目分析失败重试 3 次（`MAX_ANALYSIS_ATTEMPTS`），全失败则用 FALLBACK dict 兜底
- 整个 pipeline 最多重跑 3 次（`MAX_PIPELINE_ATTEMPTS`），由 `verify_report` 校验失败或 `run_pipeline` 运行时异常触发
- 单条目分析失败不阻塞全局趋势总结

## 数据流

```
github.com/trending (HTML)
  → _parse_trending_html()
  → list[dict] repos

raw.githubusercontent.com (README.md × N)
  → fetch_all_readmes() (asyncio.gather)
  → repos 增加 "readme" key

RSS feeds (feeds.yml)
  → fetch_rss_items() (asyncio.gather per feed)
  → list[dict] rss_items

repos + rss_items
  → Analyzer.analyze_repo() × N 次
  → _normalize_analysis() 规整字段类型
  → dict[str, dict] analyses

analyses
  → Analyzer.analyze_trends() × 1 次
  → str trend_summary

render_daily_report(repos+rss_items, analyses, trend_summary)
  → Markdown 日报 (docs/daily/YYYY-MM-DD.md)

render_rss_feed(repos+rss_items, analyses, report_date)
  → RSS XML (docs/feed.xml)

verify_report(report_path)
  → 结构校验通过 → git commit + push
  → 校验失败 → 重跑 pipeline（最多 3 次）
```

## 错误处理

| 场景 | 策略 |
|------|------|
| GitHub Trending 页面抓取失败 | httpx 抛异常，pipeline 终止（下次 cron 重试） |
| 单个 README 抓取失败 | 返回空字符串，不影响其他项目 |
| 单个 RSS feed 抓取失败 | 打日志跳过，不影响其他 feed |
| LLM 单次调用失败 | tenacity 指数退避重试 3 次 |
| LLM 重试仍失败 | 降级为 FALLBACK dict（summary 用 description 填，其余字段留空） |
| LLM 返回字段类型漂移 | `_normalize_analysis` 在边界规整为 schema 类型 |
| 趋势总结 LLM 失败 | 降级为 FALLBACK_TREND_SUMMARY（引导读者查看条目详情） |
| `verify_report` 校验失败 | 整个 pipeline 最多重跑 3 次，仍失败则保留残缺报告不 commit |
| `run_pipeline` 运行时异常 | 捕获并重跑 pipeline，最多 3 次，仍失败则退出不 commit |
| GitHub Actions 超时 | workflow 设 `timeout-minutes: 100`，正常 2-3 分钟完成 |

## 测试

34 个测试覆盖所有模块：

| 模块 | 测试数 | 策略 |
|------|--------|------|
| config | 7 | monkeypatch 环境变量 + load_feeds |
| fetcher | 9 | 1 个纯函数测试 + 8 个 mock httpx（含 RSS 解析、limit、失败跳过） |
| analyzer | 8 | mock OpenAI client + `_normalize_analysis` 类型规整测试 |
| renderer | 4 | 纯函数，验证 section、排序、RSS 分区 |
| rss | 4 | 纯函数，验证 XML 结构、类型漂移不崩、排序、来源分区 |
| main | 2 | mock run_pipeline，验证异常重试与恢复 |

```bash
LLM_API_KEY=sk-test pytest tests/ -v
```

## 本地运行

```bash
pip install -r requirements.txt
export LLM_API_KEY=sk-your-key
export LLM_BASE_URL=https://api.openai.com/v1   # 可选
export LLM_MODEL=gpt-4.1-mini                    # 可选
python scripts/main.py
```

本地运行会生成日报到 `docs/daily/` 和 RSS feed 到 `docs/feed.xml`，但**不会**执行 git commit/push（需 `CI=true`）。

## CI/CD

`.github/workflows/daily.yml`：
- **触发**：UTC 00:17 cron + workflow_dispatch（手动触发）
- **超时**：100 分钟
- **Secrets**：`LLM_API_KEY`（必填）、`LLM_BASE_URL`、`LLM_MODEL`、`DAILY_REPO_LIMIT`、`RSS_ITEMS_PER_FEED`、`GITHUB_TOKEN`

## 成本

- GitHub Actions：每次 ~3 分钟，每月 ~90 分钟，免费额度内
- LLM API：gpt-4.1-mini，每月 ~$3-5
- **总计：~$3-5/月**

## 代码量

| 模块 | 行数 |
|------|------|
| config.py | 29 |
| fetcher.py | 171 |
| analyzer.py | 160 |
| renderer.py | 143 |
| rss.py | 112 |
| verify_report.py | 90 |
| main.py | 209 |
| **总计** | **914** |
