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
