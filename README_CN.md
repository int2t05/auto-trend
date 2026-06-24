# Auto-Trend

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![GitHub Actions](https://img.shields.io/badge/CI-GitHub%20Actions-2088FF?logo=githubactions&logoColor=white)](https://github.com/features/actions)
[![GitHub Pages](https://img.shields.io/badge/Live-GitHub%20Pages-blue?logo=github)](https://int2t05.github.io/auto-trend/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

LLM 驱动的 GitHub Trending 日报，自动发布到 GitHub Pages。

[English](README.md)

---

## Fork 部署

**5 分钟拥有自己的趋势日报。**

### 1. Fork 仓库

Fork → 取消勾选 "Copy the `master` branch only" → Create fork。

### 2. 启用 GitHub Actions

你的仓库 → Settings → Actions → General → Allow all actions。

### 3. 设置 Secrets

Settings → Secrets and variables → Actions → New repository secret：

| Secret | 说明 |
|--------|------|
| `LLM_API_KEY` | LLM API 密钥（**必填**） |
| `LLM_BASE_URL` | API 地址（可选，默认 OpenAI） |
| `LLM_MODEL` | 模型名称（可选，默认 `gpt-4.1-mini`） |
| `DAILY_REPO_LIMIT` | 每日分析上限（可选，默认 `20`） |

### 4. 启用 GitHub Pages

Settings → Pages → Source: **Deploy from a branch** → Branch: `master` / `/docs`。

### 5. 替换 URL

将以下文件中的 `int2t05` 替换为你的 GitHub 用户名：

| 文件 | 需修改位置 |
|------|-----------|
| `docs/_layouts/default.html` | GitHub 链接（第 406 行）、页脚（第 446 行） |
| `docs/index.md` | 页脚链接（第 14 行） |
| `README.md` | Badge URL、Live Reports 链接 |

```bash
grep -r "int2t05" --include="*.md" --include="*.html" --include="*.js" --include="*.json" .
```

### 6. 触发首次运行

Actions → Daily Trending Report → Run workflow。首次报告将出现在：

```
https://<你的用户名>.github.io/auto-trend/
```

---

## 工作原理

```
GitHub Actions cron (UTC 00:30)
  → 抓取 GitHub Trending 页面 (httpx + BeautifulSoup)
  → 并发获取各项目 README (asyncio)
  → LLM 结构化分析 (JSON mode)
  → 全局趋势总结
  → 生成 Markdown 日报
  → git commit + push
  → GitHub Pages 自动发布
```

每个仓库输出 6 个维度的分析：**一句话概括**、**技术亮点**、**适用场景**、**竞品对比**、**成熟度评估**、**趋势信号**。

## 本地运行

```bash
pip install -r requirements.txt

export LLM_API_KEY=sk-your-key
export LLM_BASE_URL=https://api.openai.com/v1   # 可选
export LLM_MODEL=gpt-4.1-mini                   # 可选
export DAILY_REPO_LIMIT=20                      # 可选

python scripts/main.py
# 非 CI 环境不会自动 commit/push
```

兼容 OpenAI、Anthropic、DeepSeek 及所有 OpenAI 兼容端点。

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `LLM_API_KEY` | LLM API 密钥 | **必填** |
| `LLM_BASE_URL` | API 地址 | `https://api.openai.com/v1` |
| `LLM_MODEL` | 模型名称 | `gpt-4.1-mini` |
| `DAILY_REPO_LIMIT` | 每日分析上限 | `20` |

## 项目结构

```
auto-trend/
├── .github/workflows/daily.yml    # Cron 触发器
├── scripts/                       # 核心流水线
│   ├── main.py                    # 编排器
│   ├── config.py                  # 环境配置
│   ├── fetcher.py                 # 爬虫 + README 获取
│   ├── analyzer.py                # LLM 分析 (OpenAI SDK)
│   └── renderer.py                # Markdown 报告生成
├── prompts/analysis.md            # LLM 系统提示
├── tests/                         # pytest 单元测试
├── e2e/                           # Playwright E2E 测试
├── docs/                          # GitHub Pages (Jekyll)
│   ├── _layouts/default.html      # Apple 风格三栏布局
│   ├── daily/                     # 生成的日报
│   └── index.md                   # 日报索引
├── requirements.txt
└── package.json                   # E2E 依赖
```

## 测试

```bash
# 单元测试
pip install -r requirements.txt
pytest tests/ -v

# E2E 测试
npm install
npx playwright test
```

## 日报浏览

**[int2t05.github.io/auto-trend](https://int2t05.github.io/auto-trend/)**

## License

MIT — 详见 [LICENSE](LICENSE)。
