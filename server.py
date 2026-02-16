"""ai-knowledge MCP Server v0.1 — AI news, GitHub trending, papers, KOL tweets."""

import os
import json
from datetime import datetime

from fastmcp import FastMCP
import httpx
from bs4 import BeautifulSoup

BRAVE_API_KEY = os.environ.get("BRAVE_SEARCH_API_KEY", "BSAmy1TF2yYdWrwepYxbpWLO3dfnR6K")
XAI_API_KEY = os.environ.get("XAI_API_KEY", "")

mcp = FastMCP("ai-knowledge")

# ── helpers ──────────────────────────────────────────────────────────────

async def _brave_search(query: str, count: int = 5) -> list[dict]:
    """Call Brave Web Search API with retry on 429."""
    import asyncio as _aio
    async with httpx.AsyncClient(timeout=15) as c:
        for attempt in range(3):
            r = await c.get(
                "https://api.search.brave.com/res/v1/web/search",
                params={"q": query, "count": count, "freshness": "pw"},
                headers={"X-Subscription-Token": BRAVE_API_KEY, "Accept": "application/json"},
            )
            if r.status_code == 429:
                await _aio.sleep(2 ** attempt)
                continue
            r.raise_for_status()
            results = r.json().get("web", {}).get("results", [])
            return [{"title": x["title"], "url": x["url"], "snippet": x.get("description", "")} for x in results]
    return []


# ── tools ────────────────────────────────────────────────────────────────

@mcp.tool()
async def search_ai_news(query: str = "artificial intelligence", limit: int = 5) -> str:
    """Search the latest AI news via Brave Search.

    Args:
        query: Search query (default: 'artificial intelligence')
        limit: Number of results (1-10, default 5)
    """
    limit = max(1, min(limit, 10))
    results = await _brave_search(f"{query} AI news", limit)
    if not results:
        return "No results found."
    lines = []
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. **{r['title']}**\n   {r['url']}\n   {r['snippet']}\n")
    return "\n".join(lines)


@mcp.tool()
async def get_github_trending(language: str = "", since: str = "daily") -> str:
    """Get GitHub trending repositories.

    Args:
        language: Filter by programming language (e.g. 'python'). Empty = all.
        since: Time range — 'daily', 'weekly', or 'monthly'.
    """
    url = "https://github.com/trending"
    if language:
        url += f"/{language}"
    url += f"?since={since}"

    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as c:
        r = await c.get(url, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")
    repos = []
    for article in soup.select("article.Box-row")[:15]:
        h2 = article.select_one("h2 a")
        if not h2:
            continue
        name = h2.get_text(strip=True).replace("\n", "").replace(" ", "")
        desc_p = article.select_one("p")
        desc = desc_p.get_text(strip=True) if desc_p else ""
        stars_span = article.select_one("span.d-inline-block.float-sm-right")
        stars = stars_span.get_text(strip=True) if stars_span else ""
        lang_span = article.select_one("span[itemprop='programmingLanguage']")
        lang = lang_span.get_text(strip=True) if lang_span else ""
        repos.append(f"• **{name}** ({lang}) ⭐ {stars}\n  {desc}")

    if not repos:
        return "Could not parse GitHub trending page."
    return f"GitHub Trending ({since}):\n\n" + "\n\n".join(repos)


@mcp.tool()
async def get_ai_papers(topic: str = "large language model", limit: int = 5) -> str:
    """Search recent AI papers on ArXiv.

    Args:
        topic: Search topic (default: 'large language model')
        limit: Number of papers (1-10, default 5)
    """
    limit = max(1, min(limit, 10))
    query = topic.replace(" ", "+")
    api_url = (
        f"http://export.arxiv.org/api/query?search_query=all:{query}"
        f"&sortBy=submittedDate&sortOrder=descending&max_results={limit}"
    )
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get(api_url)
        r.raise_for_status()

    soup = BeautifulSoup(r.text, "xml")
    entries = soup.find_all("entry")
    if not entries:
        return "No papers found."

    lines = []
    for i, e in enumerate(entries, 1):
        title = e.find("title").get_text(strip=True).replace("\n", " ")
        published = e.find("published").get_text(strip=True)[:10]
        link = e.find("id").get_text(strip=True)
        summary = e.find("summary").get_text(strip=True).replace("\n", " ")[:200]
        authors = ", ".join(a.find("name").get_text(strip=True) for a in e.find_all("author")[:3])
        if len(e.find_all("author")) > 3:
            authors += " et al."
        lines.append(f"{i}. **{title}**\n   {authors} | {published}\n   {link}\n   {summary}…\n")
    return "\n".join(lines)


@mcp.tool()
async def search_kol_tweets(query: str = "AI LLM") -> str:
    """Search AI KOL tweets/posts via Brave Search (X/Twitter results).

    Args:
        query: Search query for AI KOL opinions
    """
    kols = "@karpathy OR @ylecun OR @dotey OR @sama OR @AndrewYNg"
    results = await _brave_search(f"site:x.com ({kols}) {query}", 8)
    if not results:
        return "No KOL tweets found."
    lines = []
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. **{r['title']}**\n   {r['url']}\n   {r['snippet']}\n")
    return "\n".join(lines)


# ── resource ─────────────────────────────────────────────────────────────

@mcp.resource("daily://ai-briefing")
async def daily_briefing() -> str:
    """Today's AI briefing: top news + trending repos + latest papers."""
    today = datetime.now().strftime("%Y-%m-%d")
    sections = []

    # News
    try:
        news = await search_ai_news("AI breakthrough", 5)
        sections.append(f"📰 AI News\n{news}")
    except Exception as e:
        sections.append(f"📰 AI News\n⚠️ Error: {e}")

    # GitHub
    try:
        gh = await get_github_trending(since="daily")
        sections.append(f"🔥 {gh}")
    except Exception as e:
        sections.append(f"🔥 GitHub Trending\n⚠️ Error: {e}")

    # Papers
    try:
        papers = await get_ai_papers("large language model", 3)
        sections.append(f"📄 Latest Papers\n{papers}")
    except Exception as e:
        sections.append(f"📄 Papers\n⚠️ Error: {e}")

    return f"# AI Daily Briefing — {today}\n\n" + "\n\n---\n\n".join(sections)


# ── main ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()
