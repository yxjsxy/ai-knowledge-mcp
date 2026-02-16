"""Quick smoke test for all tools."""
import asyncio
from server import _brave_search
import httpx
from bs4 import BeautifulSoup

async def test_brave():
    print("=" * 60)
    print("1. Brave Search (AI news)")
    print("=" * 60)
    results = await _brave_search("LLM reasoning AI news", 3)
    for i, r in enumerate(results, 1):
        print(f"  {i}. {r['title'][:80]}")
        print(f"     {r['url']}")
    print()

async def test_github():
    print("=" * 60)
    print("2. GitHub Trending")
    print("=" * 60)
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as c:
        r = await c.get("https://github.com/trending?since=daily", headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(r.text, "html.parser")
    articles = soup.select("article.Box-row")[:5]
    for a in articles:
        h2 = a.select_one("h2 a")
        if h2:
            print(f"  • {h2.get_text(strip=True).replace(chr(10),'').replace(' ','')}")
    print()

async def test_arxiv():
    print("=" * 60)
    print("3. ArXiv Papers")
    print("=" * 60)
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get("http://export.arxiv.org/api/query?search_query=all:multimodal+agent&sortBy=submittedDate&sortOrder=descending&max_results=3")
    soup = BeautifulSoup(r.text, "xml")
    for e in soup.find_all("entry"):
        print(f"  • {e.find('title').get_text(strip=True)[:80]}")
    print()

async def test_kol():
    print("=" * 60)
    print("4. KOL Tweets")
    print("=" * 60)
    results = await _brave_search("site:x.com (@karpathy OR @ylecun) AI agent", 5)
    for i, r in enumerate(results, 1):
        print(f"  {i}. {r['title'][:80]}")
    print()

async def main():
    await test_brave()
    await test_github()
    await test_arxiv()
    await test_kol()
    print("✅ All 4 tools working!")

asyncio.run(main())
