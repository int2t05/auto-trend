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
        return f"""Analyze this GitHub trending repository:

Name: {repo['full_name']}
Description: {repo.get('description', '')}
Language: {repo.get('language', '')}
Stars (total): {repo.get('total_stars', 0)}
Stars today: {repo.get('stars_today', '')}
Topics: {', '.join(repo.get('topics', []))}

README excerpt:
{repo.get('readme', '')[:8000]}
"""

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=10))
    def analyze_repo(self, repo: dict) -> dict:
        resp = self.client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": self._build_user_prompt(repo)},
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=1500,
        )
        content = resp.choices[0].message.content.strip()
        return json.loads(content)

    def analyze_trends(self, analyses: list[dict]) -> str:
        summaries = [a.get("summary", "") for a in analyses]
        joined = "\n".join(f"- {s}" for s in summaries)
        resp = self.client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a technology trend analyst. Given a list of trending "
                        "GitHub repo summaries, write a concise "
                        "trend observation paragraph (200-300 chars in Chinese). "
                        "Identify patterns, emerging themes, and what they signal "
                        "about the developer ecosystem right now. Be specific, not generic."
                    ),
                },
                {"role": "user", "content": f"Today's trending repos:\n{joined}"},
            ],
            temperature=0.5,
            max_tokens=400,
        )
        return resp.choices[0].message.content.strip()
