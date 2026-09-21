# 审计报告 · 2026-09-19 · RSS 崩溃与类型漂移

## 触发

GitHub Actions `Daily Trending Report` 在 2026-09-19 运行时崩溃：

```
File ".../html/__init__.py", line 19, in escape
    s = s.replace("&", "&amp;")
AttributeError: 'list' object has no attribute 'replace'
Error: Process completed with exit code 1.
```

崩溃发生在 `Rendering RSS feed...` 阶段。

## 根因

LLM 偶尔把 string 字段返回成 JSON 数组。证据在 `docs/daily/2026-09-18.md`：

- 第 95 行：`**适用场景**: ['让 Agent 操作已有登录账号的网页：...', '沙箱里跑 Agent 的场景：...']`
- 第 597 行：`**适用场景**: ['Alphabet/Waymo 的战略和 BD 团队...', '关注自动驾驶出海的投资人和分析师...']`
- 第 599 行：`**竞品对比**: ['对手很明确：...', '和特斯拉 Robotaxi...']`

`use_cases` / `competitive_comparison` 在 prompt 中定义为 string 字段，但 LLM 返回了 list。

**为什么 Markdown 没崩，RSS 崩了**：
- `renderer.py` 用 f-string 插值，list 被 `str()` 成 `['a', 'b']` —— 输出丑但不崩
- `rss.py` 调 `html.escape(field)`，`escape` 内部 `s.replace("&", ...)` —— list 没有 `.replace` 方法，直接崩

**为什么 `audit_analysis` 没拦住**：它只检查 missing/empty，不检查类型。list 类型的 `use_cases` 非空，pass。

**为什么 pipeline 重试没拦住**：`main.py` 的 `MAX_PIPELINE_ATTEMPTS` 循环只在 `verify_report` 失败时重试，不捕获运行时异常。一次 `AttributeError` 直接杀掉整个进程。

## 已修复

### 1. `scripts/analyzer.py` — 在 LLM 边界规整字段类型

新增 `_normalize_analysis(analysis)`，在 `analyze_repo` 的 `json.loads` 之后立即调用：

- string 字段（`summary` / `use_cases` / `competitive_comparison` / `maturity` / `trend_signal`）：list 拼接为 str，None 变空串，非 str 转 str
- list 字段（`highlights` / `core_features`）：str 包装为单元素 list，None 变空 list，非 list 包装为单元素 list

这是根因修复 —— 下游 `renderer.py` 和 `rss.py` 拿到的数据契约统一，不再需要各自防御。

### 2. `scripts/analyzer.py` — `analyze_repo` 处理 `content is None`

与 `analyze_trends` 对齐：推理模型可能返回 `content=None`，原代码 `resp.choices[0].message.content.strip()` 会 `AttributeError`。现在显式检查 None 和空字符串，抛 `ValueError` 触发 tenacity 重试。

### 3. 回归测试（`tests/test_analyzer.py` +4 个，`tests/test_rss.py` +4 个）

- `test_normalize_analysis_coerces_list_typed_string_fields` —— 直接验证 list 类型 string 字段被拼成 str
- `test_normalize_analysis_coerces_list_typed_list_fields` —— list 字段 str/None 转换
- `test_normalize_analysis_preserves_correct_types` —— 正确类型原样通过
- `test_analyze_repo_normalizes_list_typed_llm_output` —— 端到端：mock LLM 返回 list，analyzer 出口为 str
- `test_render_rss_feed_basic_structure` / `handles_list_typed_fields` / `sorts_by_stars_today_descending` / `includes_rss_items_after_github_repos` —— 覆盖此前零测试的 `rss.py`

测试总数：24 → 32，全部通过。

## 待评审

以下问题本次未改，列出供决策。

### A. `main.py` pipeline 重试不捕获运行时异常

**现状**：`for attempt in range(1, MAX_PIPELINE_ATTEMPTS + 1)` 循环只在 `verify_report` 返回失败时重试；`asyncio.run(run_pipeline(report_date))` 抛异常会直接传播出循环，进程崩溃，重试机制形同虚设。

**影响**：任何运行时异常（网络抖动、LLM 边界 case、第三方 API 变动）都会让当天日报彻底缺失，而不是重试后可能恢复。

**建议**：在循环内 `try/except Exception` 包住 `asyncio.run(run_pipeline(...))`，把异常当作 verify 失败处理 —— 打日志、重试、达到上限后退出。改动小，但对 GitHub Actions 稳定性提升明显。

### B. `docs/TECH.md` 文档与代码漂移

- `TECH.md` 第 73 行：`scripts/analyzer.py (89 行)` —— 实际改完后约 161 行
- `TECH.md` 第 154 行：`13 个测试覆盖所有模块` —— 实际 32 个
- `TECH.md` 第 160 行：`analyzer | 2 | mock OpenAI client` —— 实际 8 个
- `TECH.md` 第 161 行：`renderer | 1 | 纯函数` —— 实际 4 个
- `TECH.md` 第 201 行：`总计 474 行` —— 已超出 500 行目标（`rss.py` 113 行未计入）
- `TECH.md` 架构总览图未画 RSS feed 数据源（`fetch_rss_items`）和 `render_rss_feed` 步骤
- `TECH.md` 第 148 行 `LLM 重试仍失败 | 降级为仅使用 description` —— `main.py` 的 `FALLBACK` dict 实际把所有字段都置空 + summary 用 description 填，与文档表述有出入

建议跑一次 `documentation-audit` 同步 `TECH.md`。

### C. `rss.py` 自身仍是脆的

当前修复把类型规整放在 analyzer 边界。如果未来有新的数据源绕过 analyzer 直接喂 `render_rss_feed`，`html.escape` 仍会崩。当前所有数据都流经 analyzer，暂无风险。若未来扩展数据源，需要重新评估是否在 `render_rss_feed` 入口再做一次 schema 校验。

### D. `fetcher.py` 的 RSS 入口类型契约

`fetch_rss_items` 调用 `entry.get("title", "").strip()`、`entry.get("summary", "")`、`entry.get("link", "")`。feedparser 框架契约保证这些字段为 string，目前没有观察到违约。如果未来遇到畸形 RSS 源导致 feedparser 返回 list，可在此处再加一层 normalize，与 analyzer 边界策略一致。

## 验证

```bash
$ LLM_API_KEY=sk-test python -m pytest tests/ -v
============================= 32 passed in 0.70s ==============================
```

回归测试 `test_analyze_repo_normalizes_list_typed_llm_output` 精确复现了 2026-09-19 的崩溃场景：mock LLM 返回 list 类型的 `use_cases`，验证 analyzer 出口为 str，下游 `render_rss_feed` 不再崩。
