import os

LLM_API_KEY = os.environ["LLM_API_KEY"]
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1")
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4.1-mini")
DAILY_REPO_LIMIT = int(os.environ.get("DAILY_REPO_LIMIT", "20"))
