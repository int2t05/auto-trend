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

REQUIRED_FIELDS = [
    "summary", "core_features", "use_cases",
    "highlights", "competitive_comparison", "maturity", "trend_signal",
]

# 字段类型契约：string 字段必须为 str，list 字段必须为 list[str]
STRING_FIELDS = (
    "summary", "use_cases", "competitive_comparison", "maturity", "trend_signal",
)
LIST_FIELDS = ("highlights", "core_features")


def _normalize_analysis(analysis: dict) -> dict:
    """规整 LLM 返回的字段类型，确保下游消费方拿到一致的 schema。

    LLM 偶尔会把本应是字符串的字段（如 use_cases）返回成数组，
    直接传给 html.escape 会触发 AttributeError。这里在 LLM 边界做兜底：
    string 字段统一为 str，list 字段统一为 list[str]。
    """
    result = dict(analysis)
    for field in STRING_FIELDS:
        value = result.get(field, "")
        if isinstance(value, list):
            value = " ".join(str(v) for v in value if v)
        elif value is None:
            value = ""
        elif not isinstance(value, str):
            value = str(value)
        result[field] = value
    for field in LIST_FIELDS:
        value = result.get(field, [])
        if value is None:
            value = []
        elif isinstance(value, str):
            value = [value] if value else []
        elif not isinstance(value, list):
            value = [str(value)]
        else:
            value = [str(v) for v in value if v]
        result[field] = value
    return result


def audit_analysis(analysis: dict) -> list[str]:
    """Return list of field names that are missing or empty."""
    missing = []
    for field in REQUIRED_FIELDS:
        value = analysis.get(field)
        if value is None:
            missing.append(field)
        elif isinstance(value, str) and not value.strip():
            missing.append(field)
        elif isinstance(value, list) and len(value) == 0:
            missing.append(field)
    return missing


class Analyzer:
    """LLM-based repo analyzer."""

    def __init__(self, client=None):
        self.client = client or OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)

    def _build_user_prompt(self, repo: dict) -> str:
        source = repo.get("source", "github-trending")
        if source.startswith("rss:"):
            feed_name = source.split(":", 1)[1]
            return f"""Analyze this RSS item from {feed_name}:

Title: {repo['full_name']}
Link: {repo.get('url', '')}
Source: {source}

Summary:
{repo.get('description', '')}

Content excerpt:
{repo.get('readme', '')[:8000]}
"""
        return f"""Analyze this GitHub trending repository:

Name: {repo['full_name']}
Description: {repo.get('description', '')}
Language: {repo.get('language', '')}
Stars (total): {repo.get('total_stars', 0)}
Stars today: {repo.get('stars_today', '')}

README excerpt:
{repo.get('readme', '')[:8000]}
"""

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=20))
    def analyze_repo(self, repo: dict) -> dict:
        resp = self.client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": self._build_user_prompt(repo)},
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=2500,
        )
        content = resp.choices[0].message.content
        if content is None:
            raise ValueError("LLM 返回 content 为 None，可能为推理模型未输出最终回答")
        content = content.strip()
        if not content:
            raise ValueError("LLM 返回 content 为空字符串")
        return _normalize_analysis(json.loads(content))

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=20))
    def analyze_trends(self, analyses: list[dict]) -> str:
        summaries = [a.get("summary", "") for a in analyses]
        joined = "\n".join(f"- {s}" for s in summaries)
        resp = self.client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是技术趋势分析员。根据下面的热门 GitHub 项目摘要，写一段"
                        "热点观察（300-500 字中文）。要求：用大白话，短句为主；"
                        "点出这些项目反映了什么共同趋势，说明当下的新闻热点和开发者"
                        "生态正在发生什么；不写空话套话，也不要扭捏的感叹。"
                        "必须写完整，不要中途停止——结尾要收束，不要留半句话。\n"
                        '返回 JSON: {"trend_summary": "你的观察"}'
                    ),
                },
                {"role": "user", "content": f"Today's trending repos:\n{joined}"},
            ],
            response_format={"type": "json_object"},
            temperature=0.5,
            max_tokens=2000,
        )
        content = resp.choices[0].message.content
        if content is None:
            raise ValueError("LLM 返回 content 为 None，可能为推理模型未输出最终回答")
        content = content.strip()
        if not content:
            raise ValueError("LLM 返回 content 为空字符串")
        result = json.loads(content)
        trend_summary = result.get("trend_summary", "")
        if not trend_summary or not trend_summary.strip():
            raise ValueError("LLM 返回的 trend_summary 为空")
        return trend_summary.strip()
