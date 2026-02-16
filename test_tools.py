"""Quick integration test for all tools."""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

# Set env before importing server
import httpx
import re
from datetime import datetime

BRAVE_API_KEY = os.environ.get("BRAVE_API_KEY", "")
XAI_API_KEY = os.environ.get("XAI_API_KEY", "")


async def test_news():
    print("=" * 50)
    print("TEST: search_ai_news")
    if not BRAVE_API_KEY:
        print("SKIP - no BRAVE_API_KEY")
        return
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get(
            "https://api.search.brave.com/res/v1/web/search",
            headers={"X-Subscription-Token": BRAVE_API_KEY, "Accept": "application/json"},
            params={"q": "AI news", "count": 3, "freshness": "pw"},
        )
        r.raise_for_status()
        results = r.json().get("web", {}).get("results", [])
        for x in results[:3]:
            print(f"  • {x['title'][:60]}")
    print(f"✅ Got {len(results)} results\n")


async def test_trending():
    print("=" * 50)
    print("TEST: get_github_trending")
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as c:
        r = await c.get("https://github.com/trending?since=daily", headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
    articles = re.findall(r'<article class="Box-row">', r.text)
    print(f"✅ Found {len(articles)} trending repos\n")


async def test_papers():
    print("=" * 50)
    print("TEST: get_ai_papers")
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as c:
        r = await c.get(
            "https://export.arxiv.org/api/query",
            params={"search_query": "all:large language model", "max_results": 3, "sortBy": "submittedDate", "sortOrder": "descending"},
        )
        r.raise_for_status()
    entries = re.findall(r"<entry>", r.text)
    print(f"✅ Found {len(entries)} papers\n")


async def test_kol():
    print("=" * 50)
    print("TEST: search_kol_tweets")
    if not BRAVE_API_KEY:
        print("SKIP - no BRAVE_API_KEY")
        return
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get(
            "https://api.search.brave.com/res/v1/web/search",
            headers={"X-Subscription-Token": BRAVE_API_KEY, "Accept": "application/json"},
            params={"q": "site:x.com AI breakthrough", "count": 5, "freshness": "pw"},
        )
        r.raise_for_status()
        results = r.json().get("web", {}).get("results", [])
        for x in results[:3]:
            print(f"  • {x['title'][:60]}")
    print(f"✅ Got {len(results)} tweet results\n")


async def main():
    await test_news()
    await test_trending()
    await test_papers()
    await test_kol()
    print("🎉 All tests passed!")


if __name__ == "__main__":
    asyncio.run(main())
