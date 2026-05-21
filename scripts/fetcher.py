import httpx
from bs4 import BeautifulSoup

GITHUB_TRENDING_URL = "https://github.com/trending"


def _parse_trending_html(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    repos = []

    for article in soup.select(".Box-row"):
        h2 = article.select_one("h2 a")
        if not h2:
            continue
        href = h2.get("href", "").strip()
        parts = href.strip("/").split("/")
        if len(parts) < 2:
            continue
        owner, name = parts[0], parts[1]

        desc_el = article.select_one("p.col-9")
        description = desc_el.get_text(strip=True) if desc_el else ""

        lang_el = article.select_one('[itemprop="programmingLanguage"]')
        language = lang_el.get_text(strip=True) if lang_el else ""

        links = article.select("a.Link--muted")
        stars_today = ""
        forks_today = ""
        if len(links) >= 2:
            stars_today = links[0].get_text(strip=True)
            forks_today = links[1].get_text(strip=True)

        repos.append({
            "owner": owner,
            "name": name,
            "full_name": f"{owner}/{name}",
            "description": description,
            "language": language,
            "stars_today": stars_today,
            "forks_today": forks_today,
            "url": f"https://github.com/{owner}/{name}",
        })

    return repos


async def fetch_trending_repos(limit: int = 20) -> list[dict]:
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            GITHUB_TRENDING_URL,
            headers={"Accept": "text/html"},
            follow_redirects=True,
        )
        resp.raise_for_status()
        repos = _parse_trending_html(resp.text)
        return repos[:limit]


async def fetch_readme(owner: str, repo: str) -> str:
    url = f"https://raw.githubusercontent.com/{owner}/{repo}/master/README.md"
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, follow_redirects=True)
        if resp.status_code == 200:
            return resp.text
        url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/README.md"
        resp = await client.get(url, follow_redirects=True)
        if resp.status_code == 200:
            return resp.text
        return ""


async def fetch_all_readmes(repos: list[dict]) -> list[dict]:
    import asyncio

    async def _fetch_one(repo):
        readme = await fetch_readme(repo["owner"], repo["name"])
        repo["readme"] = readme[:8000]
        return repo

    return await asyncio.gather(*[_fetch_one(r) for r in repos])
