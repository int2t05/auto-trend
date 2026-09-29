import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

LLM_API_KEY = os.environ["LLM_API_KEY"]
LLM_BASE_URL = os.environ.get("LLM_BASE_URL") or "https://api.openai.com/v1"
LLM_MODEL = os.environ.get("LLM_MODEL") or "gpt-4.1-mini"
DAILY_REPO_LIMIT = int(os.environ.get("DAILY_REPO_LIMIT") or "20")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

# git 提交身份：显式环境变量优先，CI 下回退到触发者的 GitHub noreply 地址；
# 两者皆空（本地开发）时由 main 跳过 git config，沿用本地已有 git 身份
GIT_USER_NAME = os.environ.get("GIT_USER_NAME") or os.environ.get("GITHUB_ACTOR") or ""
GIT_USER_EMAIL = os.environ.get("GIT_USER_EMAIL") or (
    f"{GIT_USER_NAME}@users.noreply.github.com" if GIT_USER_NAME else ""
)
