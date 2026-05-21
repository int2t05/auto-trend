# Auto-Trend PRD

> 每日自动抓取 GitHub Trending 项目，经 LLM 结构化分析后生成 Markdown 日报，
> commit 回仓库并通过 GitHub Pages 直接浏览。

---

## 1. 项目背景

GitHub Trending 每天涌现大量值得关注的开源项目，但原始列表缺乏上下文：项目解决了什么问题？代码质量如何？与其他同类项目有何差异？本项目的目标是**自动化这一分析过程**，每天产出一份高信息密度的日报。

### 1.1 参考项目

调研了以下同类开源项目的做法，取其共性作为本项目的分析框架基础：

| 项目 | 核心思路 | 参考价值 |
|------|---------|---------|
| [agents-radar](https://github.com/gsscsd/big_model_radar) | TS + GitHub Actions，多源抓取，LLM 分类与趋势信号提取，双语 Markdown，GitHub Issues/Pages 发布 | 报告结构设计、维度分类法 |
| [dailydawn](https://github.com/TangSY/dailydawn) | Python ~1500 行，零数据库，异步抓取 + 多专家 LLM pipeline，双语日报，GitHub Actions 每日 cron | 薄层架构、Pipeline 设计模式 |
| [gh-explorer](https://github.com/zjy365/gh-explorer) | CLI 工具，LLM 分析 Trending 仓库，输出 JSON/Table/Markdown | LLM 对单仓库的结构化分析方式 |

### 1.2 设计原则

**薄层**。不引入数据库、不搭建后端服务、不做前端框架。整个系统由以下部分串联：

> GitHub Actions cron → Python 脚本 → zread.ai API → LLM → Markdown → git commit → GitHub Pages

---

## 2. 功能需求

### 2.1 数据获取

**来源**：通过 [zread.ai](https://zread.ai) 获取 GitHub Trending 项目列表。zread.ai 是一个已聚合好的 GitHub Trending 数据平台，省去了直接解析 GitHub Trending 页面 HTML 的复杂度。

**获取内容**：
- Trending 项目列表（按日/周/月）
- 项目基础元数据：名称、作者、描述、语言、Star 数、Fork 数、Topic 标签
- 项目 README 内容（用于 LLM 分析）

### 2.2 LLM 结构化分析

对每个 Trending 项目，LLM 执行以下分析：

| 分析维度 | 说明 |
|---------|------|
| **一句话概括** | 该项目是什么、解决什么问题 |
| **技术亮点** | 架构设计、算法、工程实践的创新点 |
| **适用场景** | 谁需要这个项目、在什么情况下使用 |
| **与同类对比** | 横向对比已知的竞品，指出差异化 |
| **成熟度评估** | 从代码质量、文档、社区活跃度等角度判断项目阶段（早期/成长/成熟） |
| **趋势信号** | 为什么现在 trending？是否反映某个技术趋势？ |

### 2.3 日报生成

每日生成一份 Markdown 文件，结构如下：

```markdown
# GitHub Trending 日报 · YYYY-MM-DD

## 📊 概览
（当日 Trending 项目的整体统计和趋势总结，LLM 生成 300 字左右）

## 🔥 今日精选
（LLM 从当日列表中选出 3-5 个最值得关注的项目，给出深度分析）

## 📋 完整列表
（所有 Trending 项目的分类列表，每项包含基础元数据和一句话概括）

| 排名 | 项目 | 语言 | Stars | 一句话概括 |
|------|------|------|-------|-----------|
| 1    | ...  | ...  | ...   | ...       |

## 💡 趋势观察
（LLM 对当日整体技术趋势的判断，跨项目分析）
```

### 2.4 定时执行

- **频率**：每天一次（北京时间 08:30 触发 = UTC 00:30）
- **载体**：GitHub Actions `schedule` cron
- **失败处理**：重试 1 次；失败不阻塞，下一天照常执行

### 2.5 发布与浏览

- Markdown 文件直接 commit 到仓库 `docs/` 目录
- GitHub Pages 指向 `docs/` 根目录，开启后即可通过 `https://<user>.github.io/auto-trend/` 浏览
- 日报文件路径：`docs/daily/YYYY-MM-DD.md`
- 首页 `docs/index.md` 列出所有日报索引，按日期倒序

---

## 3. 技术方案

### 3.1 技术选型

| 层级 | 选择 | 理由 |
|------|------|------|
| 脚本语言 | **Python 3.12+** | httpx + asyncio 异步抓取，OpenAI SDK 调 LLM，生态成熟 |
| LLM SDK | **openai (Python)** | 兼容任何 OpenAI-API 网关（OpenAI / DeepSeek / 硅基流动等） |
| HTTP 客户端 | **httpx** (async) | 支持异步并发抓取多个 README |
| HTML/Markdown 解析 | **markdownify** / **html2text** | 将 README HTML 转为纯文本供 LLM 分析 |
| 任务调度 | **GitHub Actions** cron | 零成本、零运维 |
| 发布 | **git commit + GitHub Pages** | 无需额外服务 |

### 3.2 项目结构

```
auto-trend/
├── .github/workflows/
│   └── daily.yml            # 定时触发工作流
├── scripts/
│   ├── main.py              # 入口：编排整个 pipeline
│   ├── fetcher.py           # 从 zread.ai 抓取 trending 数据
│   ├── analyzer.py          # 调 LLM 做结构化分析
│   ├── renderer.py          # 生成 Markdown 日报
│   └── indexer.py           # 更新 docs/index.md 日报索引
├── prompts/
│   └── analysis.md          # LLM 分析用的 system prompt
├── docs/
│   ├── index.md             # 日报索引（自动生成）
│   └── daily/
│       └── YYYY-MM-DD.md    # 每日日报
├── requirements.txt
└── README.md
```

### 3.3 Pipeline 流程

```
GitHub Actions cron (UTC 00:30)
  │
  ├─ 1. fetcher: 调 zread.ai API 获取当日 Trending 列表 (~10s)
  ├─ 2. fetcher: 并发抓取各项目 README（异步，~30s）
  │
  ├─ 3. analyzer: 调 LLM 逐项目结构化分析（~60s，可并行）
  ├─ 4. analyzer: 调 LLM 生成全局趋势总结（~15s）
  │
  ├─ 5. renderer: 组装 Markdown 日报
  ├─ 6. indexer: 更新日报索引
  │
  ├─ 7. git add + commit + push
  └─ 8. GitHub Pages 自动发布
```

**估算 LLM 调用次数**：每个项目 1 次分析调用 + 1 次全局总结调用。以 25 个 Trending 项目计，约 26 次 LLM 调用。使用 `gpt-4.1-mini` 级别模型，单次耗时约 2-3 秒，总计约 60-80 秒。

### 3.4 配置化

所有可变参数通过环境变量（GitHub Secrets）配置：

| 变量 | 说明 | 示例 |
|------|------|------|
| `LLM_API_KEY` | LLM API 密钥 | `sk-xxx` |
| `LLM_BASE_URL` | LLM API 地址 | `https://api.openai.com/v1` |
| `LLM_MODEL` | 模型名称 | `gpt-4.1-mini` |
| `ZREAD_API_URL` | zread.ai API 地址 | `https://zread.ai/api/...` |

### 3.5 LLM Prompt 设计

参考 agents-radar 和 dailydawn 的做法，采用**结构化输出**方式：

- **System prompt** 定义分析框架、输出格式要求
- **User prompt** 传入项目元数据和 README 摘要
- **输出格式** 要求 JSON，便于程序化组装 Markdown

Prompt 核心要求：
- 不要复述 README，要提炼和判断
- 横向对比需要基于 LLM 训练数据中的知识
- 一句话概括控制在 50 字以内
- 趋势信号必须具体，避免空泛的"AI 在增长"类判断

---

## 4. 非功能需求

### 4.1 可靠性

- 单源失败不阻塞：zread.ai 不可用时跳过当日任务，下次正常执行
- LLM 单次调用失败重试 2 次，指数退避
- GitHub Actions 执行超时设为 10 分钟（正常耗时约 2-3 分钟）

### 4.2 成本

- GitHub Actions：免费额度 2000 分钟/月，每次运行约 3 分钟，每月约 90 分钟，远在免费额度内
- LLM API：以 gpt-4.1-mini 计，每项目约 2K input + 500 output tokens，25 项目约 62.5K tokens/天，月费约 $3-5
- 仓库存储：Markdown 文件极小，无存储成本
- **总成本：~$3-5/月，纯 LLM API 费用**

### 4.3 可维护性

- 总代码量控制在 **500 行以内**
- 无框架依赖，仅标准 Python 库 + httpx + openai
- 配置与代码分离，换模型/换数据源无需改代码

---

## 5. 实施计划

| 阶段 | 内容 | 预计时间 |
|------|------|---------|
| Phase 1 | 基础框架：项目结构、GitHub Actions workflow、fetcher 实现 | 0.5d |
| Phase 2 | LLM 分析：analyzer + prompt 调优 | 0.5d |
| Phase 3 | 日报生成：renderer + indexer + Markdown 模板 | 0.25d |
| Phase 4 | 联调测试：端到端跑通，GitHub Pages 验证 | 0.25d |

---

## 6. 风险与缓解

| 风险 | 缓解措施 |
|------|---------|
| zread.ai API 不稳定或变更 | fetcher 模块独立，可切换到直接解析 GitHub Trending 页面 |
| LLM 输出格式不稳定 | 使用 JSON mode 或 structured output；解析失败时退化为原始文本嵌入 |
| GitHub Actions 执行超时 | 异步并发抓取；控制每日分析项目上限（默认 20 个） |
| LLM 幻觉导致分析不准确 | Prompt 明确要求"不确定时标注'待验证'"；不要求 LLM 给出精确数据 |
