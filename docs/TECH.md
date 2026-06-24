# Auto-Trend 技术文档

## 架构总览

```
GitHub Actions cron (UTC 00:30)
  │
  ├─ 1. fetcher.fetch_trending_repos()   抓 GitHub Trending 页面 HTML
  ├─ 2. fetcher.fetch_all_readmes()      并发抓各项目 README (raw.githubusercontent.com)
  │
  ├─ 3. analyzer.analyze_repo()          逐项目调 LLM 做 6 维结构化分析
  ├─ 4. analyzer.analyze_trends()        跨项目趋势总结
  │
  ├─ 5. renderer.render_daily_report()   组装 Markdown 日报
  │
  ├─ 6. git add + commit + push
  └─ 7. GitHub Pages 自动发布
```

薄层设计，零数据库，零后端服务。整个 pipeline 由 GitHub Actions 驱动，一个 Python 脚本跑完全程。

## 技术栈

| 层 | 选择 | 说明 |
|---|------|------|
| 语言 | Python 3.12+ | async/await 原生支持 |
| HTTP | httpx (async) | 异步并发抓取，比 requests 快 3-5x |
| HTML 解析 | BeautifulSoup4 | 解析 GitHub Trending 页面 |
| LLM SDK | openai | 兼容任何 OpenAI-API 网关 |
| 重试 | tenacity | 指数退避，LLM 调用失败自动重试 2 次 |
| 调度 | GitHub Actions | cron 定时触发，免费 2000 分钟/月 |
| 测试 | pytest + pytest-asyncio + pytest-mock | 异步测试 + mock |
| 发布 | GitHub Pages | 直接渲染 `docs/` 目录下的 Markdown |

## 模块设计

### 1. `scripts/config.py` (6 行)

环境变量读取层。所有配置通过环境变量注入，代码中无硬编码。

```python
LLM_API_KEY       = os.environ["LLM_API_KEY"]       # 必填
LLM_BASE_URL      = "https://api.openai.com/v1"      # 可选
LLM_MODEL         = "gpt-4.1-mini"                   # 可选
DAILY_REPO_LIMIT  = 20                               # 可选
```

### 2. `scripts/fetcher.py` (81 行)

**职责**：获取 GitHub Trending 数据。

- `_parse_trending_html(html)` — 解析 Trending 页面 DOM，提取项目名、描述、语言、Star/Fork 数
- `fetch_trending_repos(limit)` — GET `github.com/trending`，返回 repo dict 列表
- `fetch_readme(owner, repo)` — 从 `raw.githubusercontent.com` 抓 README.md（先试 master 分支，再试 main）
- `fetch_all_readmes(repos)` — `asyncio.gather` 并发抓取，每个 README 截断到 8000 字符

**数据格式**：
```python
{
    "owner": "alice",
    "name": "cooltool",
    "full_name": "alice/cooltool",
    "description": "A cool tool",
    "language": "Python",
    "stars_today": "1,234",
    "forks_today": "56",
    "url": "https://github.com/alice/cooltool",
    "readme": "# Cool Tool\n\n..."  # 由 fetch_all_readmes 添加
}
```

### 3. `scripts/analyzer.py` (71 行)

**职责**：调 LLM 做结构化分析。

- `Analyzer` 类，构造函数接受可选 `client` 参数（便于测试注入 mock）
- `analyze_repo(repo)` — 单项目分析，输出 6 维 JSON：
  - `summary` — 一句话概括（中文 ≤80 字）
  - `highlights` — 2-3 个技术亮点
  - `use_cases` — 适用场景
  - `comparison` — 竞品对比
  - `maturity` — 成熟度（早期/成长期/成熟）
  - `trend_signal` — 趋势信号
- `analyze_trends(analyses)` — 跨项目趋势总结，输出 200-300 字中文段落
- 使用 `response_format={"type": "json_object"}` 确保结构化输出
- `@retry(stop=2, wait=exponential)` 指数退避重试

**System Prompt**：定义在 `prompts/analysis.md`，要求 LLM 做判断而非复述 README。

### 4. `scripts/renderer.py` (86 行)

**职责**：将结构化数据组装为 Markdown 日报。纯函数，无副作用。

日报结构：
```
# GitHub Trending 日报 · YYYY-MM-DD

## 概览          ← 项目统计 + 语言分布 + LLM 趋势总结

## 今日精选       ← 前 5 个项目深度分析（6 维展开）

## 完整列表       ← 所有项目的表格（排名/项目/语言/Stars/一句话概括）

## 趋势观察       ← LLM 跨项目趋势判断
```

### 5. `scripts/main.py` (124 行)

**职责**：编排整个 pipeline。

- 支持命令行指定日期：`python scripts/main.py 2026-05-20`
- 默认取 UTC 当天日期
- `CI` 环境变量控制是否执行 git commit/push（本地运行不 push）
- 每个步骤有独立 try/except，单项目分析失败不阻塞全局趋势总结

## 数据流

```
github.com/trending (HTML)
  → _parse_trending_html()
  → list[dict] repos

raw.githubusercontent.com (README.md × N)
  → fetch_all_readmes() (asyncio.gather)
  → repos 增加 "readme" key

LLM API
  → Analyzer.analyze_repo() × N 次
  → Analyzer.analyze_trends() × 1 次
  → dict[str, dict] analyses + str trend_summary

render_daily_report(repos, analyses, trend_summary)
  → Markdown string
```

## 错误处理

| 场景 | 策略 |
|------|------|
| GitHub Trending 页面抓取失败 | httpx 抛异常，pipeline 终止（下次 cron 重试） |
| 单个 README 抓取失败 | 返回空字符串，不影响其他项目 |
| LLM 单次调用失败 | tenacity 指数退避重试 2 次 |
| LLM 重试仍失败 | 降级为仅使用 description，maturity=早期 |
| 趋势总结 LLM 失败 | 降级为"今日无法生成趋势总结" |
| GitHub Actions 超时 | workflow 设 `timeout-minutes: 10`，正常 2-3 分钟完成 |

## 测试

13 个测试覆盖所有模块：

| 模块 | 测试数 | 策略 |
|------|--------|------|
| config | 3 | monkeypatch 环境变量 |
| fetcher | 4 | 1 个纯函数测试 + 3 个 mock httpx |
| analyzer | 2 | mock OpenAI client，按 `response_format` 区分返回值 |
| renderer | 1 | 纯函数，给定输入验证输出包含所有 section |

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

本地运行会生成日报到 `docs/daily/`，但**不会**执行 git commit/push（需 `CI=true`）。

## CI/CD

`.github/workflows/daily.yml`：
- **触发**：UTC 00:30 cron + workflow_dispatch（手动触发）
- **超时**：10 分钟
- **Secrets**：`LLM_API_KEY`（必填）、`LLM_BASE_URL`、`LLM_MODEL`

## 成本

- GitHub Actions：每次 ~3 分钟，每月 ~90 分钟，免费额度内
- LLM API：gpt-4.1-mini，每月 ~$3-5
- **总计：~$3-5/月**

## 代码量

| 模块 | 行数 |
|------|------|
| config.py | 6 |
| fetcher.py | 81 |
| analyzer.py | 71 |
| renderer.py | 86 |
| main.py | 124 |
| **总计** | **368** |

控制在 500 行以内的目标达成。
