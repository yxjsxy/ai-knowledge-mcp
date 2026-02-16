"""ai-knowledge MCP Server v0.1 — AI news, GitHub trending, papers, KOL tweets."""

from fastmcp import FastMCP
import httpx
import os
from datetime import datetime

mcp = FastMCP(
    "ai-knowledge",
    instructions="AI knowledge hub: news search, GitHub trending, ArXiv papers, KOL tweets",
)

BRAVE_API_KEY = os.environ.get("BRAVE_API_KEY", "")
XAI_API_KEY = os.environ.get("XAI_API_KEY", "")


@mcp.tool()
async def search_ai_news(query: str = "artificial intelligence", limit: int = 5) -> str:
    """Search latest AI news via Brave Search API.

    Args:
        query: Search query (default: "artificial intelligence")
        limit: Number of results (1-20, default 5)
    """
    limit = min(max(limit, 1), 20)
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            "https://api.search.brave.com/res/v1/web/search",
            headers={"X-Subscription-Token": BRAVE_API_KEY, "Accept": "application/json"},
            params={"q": query, "count": limit, "freshness": "pw"},  # past week
        )
        resp.raise_for_status()
        data = resp.json()

    results = data.get("web", {}).get("results", [])
    if not results:
        return f"No results found for '{query}'"

    lines = [f"## AI News: {query}\n"]
    for i, r in enumerate(results[:limit], 1):
        lines.append(f"**{i}. [{r.get('title', 'Untitled')}]({r.get('url', '')})**")
        if desc := r.get("description"):
            lines.append(f"   {desc}")
        lines.append("")
    return "\n".join(lines)


@mcp.tool()
async def get_github_trending(language: str = "", since: str = "daily") -> str:
    """Get GitHub trending repositories.

    Args:
        language: Filter by programming language (e.g. "python", "rust"). Empty = all.
        since: Time range: "daily", "weekly", or "monthly"
    """
    url = "https://github.com/trending"
    if language:
        url += f"/{language}"
    params = {"since": since}

    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        resp = await client.get(url, params=params, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        html = resp.text

    import re
    articles = re.findall(r'<article class="Box-row">(.*?)</article>', html, re.DOTALL)

    lines = [f"## GitHub Trending ({since}){f' — {language}' if language else ''}\n"]
    for i, article in enumerate(articles[:10]):
        # Extract repo from stargazers link pattern /owner/repo/stargazers
        repo_match = re.search(r'href="(/[^/]+/[^/]+)/stargazers"', article)
        if not repo_match:
            continue
        repo_path = repo_match.group(1)
        repo_name = repo_path.lstrip("/")

        desc_match = re.search(r'<p class="col-9[^"]*">\s*(.+?)\s*</p>', article)
        desc = desc_match.group(1).strip() if desc_match else ""

        star_match = re.search(r'([\d,]+)\s*stars today', article)
        star = star_match.group(1) if star_match else "?"

        lines.append(f"**{i+1}. [{repo_name}](https://github.com{repo_path})** ⭐ {star}/day")
        if desc:
            lines.append(f"   {desc}")
        lines.append("")

    return "\n".join(lines) if len(lines) > 1 else "Could not parse trending repos. Try again later."


@mcp.tool()
async def get_ai_papers(topic: str = "artificial intelligence", limit: int = 5) -> str:
    """Search recent AI papers on ArXiv.

    Args:
        topic: Search topic (default: "artificial intelligence")
        limit: Number of papers (1-20, default 5)
    """
    limit = min(max(limit, 1), 20)
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        resp = await client.get(
            "https://export.arxiv.org/api/query",
            params={
                "search_query": f"all:{topic}",
                "start": 0,
                "max_results": limit,
                "sortBy": "submittedDate",
                "sortOrder": "descending",
            },
        )
        resp.raise_for_status()
        xml = resp.text

    import re
    entries = re.findall(r"<entry>(.*?)</entry>", xml, re.DOTALL)
    if not entries:
        return f"No papers found for '{topic}'"

    lines = [f"## ArXiv Papers: {topic}\n"]
    for i, entry in enumerate(entries[:limit], 1):
        title = re.search(r"<title>(.*?)</title>", entry, re.DOTALL)
        title = title.group(1).strip().replace("\n", " ") if title else "Untitled"
        
        summary = re.search(r"<summary>(.*?)</summary>", entry, re.DOTALL)
        summary = summary.group(1).strip().replace("\n", " ")[:200] if summary else ""
        
        link = re.search(r'<id>(.*?)</id>', entry)
        link = link.group(1).strip() if link else ""
        
        published = re.search(r"<published>(.*?)</published>", entry)
        published = published.group(1)[:10] if published else ""

        authors = re.findall(r"<name>(.*?)</name>", entry)
        author_str = ", ".join(authors[:3])
        if len(authors) > 3:
            author_str += " et al."

        lines.append(f"**{i}. {title}**")
        lines.append(f"   {author_str} | {published}")
        lines.append(f"   {link}")
        if summary:
            lines.append(f"   > {summary}...")
        lines.append("")

    return "\n".join(lines)


@mcp.tool()
async def search_kol_tweets(query: str = "AI") -> str:
    """Search AI KOL tweets via Brave Search (Twitter/X results).

    Args:
        query: Search query for AI KOL content
    """
    search_query = f"site:x.com {query}"
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            "https://api.search.brave.com/res/v1/web/search",
            headers={"X-Subscription-Token": BRAVE_API_KEY, "Accept": "application/json"},
            params={"q": search_query, "count": 10, "freshness": "pw"},
        )
        resp.raise_for_status()
        data = resp.json()

    results = data.get("web", {}).get("results", [])
    if not results:
        return f"No KOL tweets found for '{query}'"

    lines = [f"## AI KOL Tweets: {query}\n"]
    for i, r in enumerate(results[:8], 1):
        lines.append(f"**{i}. [{r.get('title', '')}]({r.get('url', '')})**")
        if desc := r.get("description"):
            lines.append(f"   {desc[:200]}")
        lines.append("")

    return "\n".join(lines)


@mcp.resource("daily://ai-briefing")
async def daily_briefing() -> str:
    """Today's AI briefing — aggregates news, trending repos, and latest papers."""
    today = datetime.now().strftime("%Y-%m-%d")
    sections = [f"# 🤖 AI Daily Briefing — {today}\n"]

    try:
        news = await search_ai_news("AI breakthroughs OR AI launch OR LLM", limit=5)
        sections.append(news)
    except Exception as e:
        sections.append(f"*News unavailable: {e}*\n")

    try:
        trending = await get_github_trending(language="python", since="daily")
        sections.append(trending)
    except Exception as e:
        sections.append(f"*Trending unavailable: {e}*\n")

    try:
        papers = await get_ai_papers("large language model", limit=3)
        sections.append(papers)
    except Exception as e:
        sections.append(f"*Papers unavailable: {e}*\n")

    return "\n---\n".join(sections)


if __name__ == "__main__":
    mcp.run()
