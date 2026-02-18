"""ai-knowledge MCP Server v0.2 — AI news, GitHub trending, papers, KOL tweets + 向量语义搜索."""

from fastmcp import FastMCP
import httpx
import os
import re
from datetime import datetime

import json as _json
import subprocess

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyAH086KFi7ggyU0mBckyHUNlwsWtxZXjxU")

mcp = FastMCP(
    "ai-knowledge",
    instructions="AI knowledge hub: semantic search over local vector DB, plus live news/GitHub/papers/KOL search",
)

BRAVE_API_KEY = os.environ.get("BRAVE_API_KEY", "")
XAI_API_KEY = os.environ.get("XAI_API_KEY", "")
VECTORDB_DIR = os.path.join(os.path.dirname(__file__), "..", "ai_knowledge", "vectordb")
EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"

COLLECTION_NAMES = ["ai_tweets", "ai_articles", "ai_fulltext", "ai_github", "ai_kol_tweets"]

_embedding_fn = None

def _get_embedding_fn():
    global _embedding_fn
    if _embedding_fn is None:
        _embedding_fn = SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL)
    return _embedding_fn

def _get_chroma():
    return chromadb.PersistentClient(path=VECTORDB_DIR)


def _gemini_rerank(query: str, results: list[dict], top_k: int = 5) -> list[dict]:
    """Use Gemini Flash to rerank search results."""
    if not results or len(results) <= top_k:
        return results[:top_k]

    candidates = []
    for i, r in enumerate(results):
        candidates.append(f"[{i}] {r.get('title', '')} | {r['text'][:150]}")
    candidates_text = "\n".join(candidates)

    prompt = f"""You are a relevance scorer. Given a query and candidate documents, return the indices of the top {top_k} most relevant documents, ordered by relevance (most relevant first).

Query: {query}

Candidates:
{candidates_text}

Return ONLY a JSON array of indices, e.g. [3, 0, 7, 1, 5]. No explanation."""

    try:
        env = {**os.environ, "GEMINI_API_KEY": GEMINI_API_KEY}
        result = subprocess.run(
            ["gemini", "-p", prompt],
            capture_output=True, text=True, timeout=30, env=env
        )
        output = result.stdout.strip()
        match = re.search(r'\[[\d,\s]+\]', output)
        if match:
            indices = _json.loads(match.group())
            reranked = []
            for idx in indices[:top_k]:
                if 0 <= idx < len(results):
                    results[idx]["rerank_score"] = top_k - len(reranked)
                    reranked.append(results[idx])
            return reranked
    except Exception:
        pass

    return results[:top_k]


# ── Semantic Search ──────────────────────────────────────

@mcp.tool()
async def semantic_search(
    query: str,
    source: str = "all",
    limit: int = 10,
    date_from: str = "",
    date_to: str = "",
    rerank: bool = False,
) -> str:
    """语义搜索 AI 知识库。支持按数据源和日期范围过滤，可选 Gemini rerank 提升精度。

    Args:
        query: 搜索查询（中英文均可）
        source: 数据源过滤 (all/tweets/articles/fulltext/github/kol)
        limit: 返回数量 (1-20, default 10)
        date_from: 开始日期 YYYYMMDD（可选）
        date_to: 结束日期 YYYYMMDD（可选）
        rerank: 是否启用 Gemini rerank 提升相关性（默认关闭）
    """
    limit = min(max(limit, 1), 20)
    client = _get_chroma()

    source_map = {
        "tweets": ["ai_tweets"],
        "articles": ["ai_articles"],
        "fulltext": ["ai_fulltext"],
        "github": ["ai_github"],
        "kol": ["ai_kol_tweets"],
        "all": COLLECTION_NAMES,
    }
    collections = source_map.get(source, COLLECTION_NAMES)

    # Build where filter for date range
    where = None
    if date_from or date_to:
        conditions = []
        if date_from:
            conditions.append({"date": {"$gte": date_from.replace("-", "")}})
        if date_to:
            conditions.append({"date": {"$lte": date_to.replace("-", "")}})
        if len(conditions) == 1:
            where = conditions[0]
        else:
            where = {"$and": conditions}

    all_results = []
    for cname in collections:
        try:
            coll = client.get_collection(cname, embedding_function=_get_embedding_fn())
            kwargs = {"query_texts": [query], "n_results": limit}
            if where:
                kwargs["where"] = where
            results = coll.query(**kwargs)

            for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            ):
                all_results.append({
                    "collection": cname,
                    "score": round(1 - dist, 3),
                    "text": doc[:300],
                    "title": meta.get("title", ""),
                    "url": meta.get("url", ""),
                    "date": meta.get("date", ""),
                    "source": meta.get("source", ""),
                })
        except Exception:
            pass

    all_results.sort(key=lambda x: x["score"], reverse=True)

    # Deduplicate by URL+title (same article across different dates)
    seen = set()
    deduped = []
    for r in all_results:
        dedup_key = (r.get("url", "") or "", r.get("title", "") or "")
        if dedup_key != ("", "") and dedup_key in seen:
            continue
        seen.add(dedup_key)
        deduped.append(r)

    # Rerank if requested
    fetch_limit = min(limit * 3, len(deduped)) if rerank else limit
    candidates = deduped[:fetch_limit]

    if rerank and len(candidates) > limit:
        top = _gemini_rerank(query, candidates, top_k=limit)
    else:
        top = candidates[:limit]

    if not top:
        return f"未找到与 '{query}' 相关的结果"

    lines = [f"## 🔍 语义搜索: {query}"]
    if rerank:
        lines[0] += " (Gemini reranked)"
    lines.append("")
    for i, r in enumerate(top, 1):
        score_str = f"score: {r['score']}"
        if "rerank_score" in r:
            score_str += f", rerank: {r['rerank_score']}"
        lines.append(f"**{i}. [{r['collection']}] {r['title'] or '(untitled)'}** ({score_str})")
        lines.append(f"   📅 {r['date']}  🔗 {r['url']}")
        lines.append(f"   {r['text'][:200]}...")
        lines.append("")

    return "\n".join(lines)


@mcp.resource("stats://knowledge-base")
async def kb_stats() -> str:
    """知识库统计信息：各 collection 数据量、日期范围、磁盘占用。"""
    client = _get_chroma()
    lines = ["# 📊 AI Knowledge Base Stats\n"]
    total = 0

    for cname in COLLECTION_NAMES:
        try:
            coll = client.get_collection(cname, embedding_function=_get_embedding_fn())
            n = coll.count()
            total += n

            date_range = "-"
            if n > 0:
                meta_rows = coll.get(include=["metadatas"])
                dates = sorted(
                    m.get("date", "")
                    for m in (meta_rows.get("metadatas") or [])
                    if m and m.get("date")
                )
                if dates:
                    date_range = f"{dates[0]} → {dates[-1]}"

            lines.append(f"- **{cname}**: {n} records | 📅 {date_range}")
        except Exception:
            lines.append(f"- **{cname}**: (not found)")

    lines.append(f"\n**Total: {total} records**")

    # Disk size
    size_bytes = sum(
        os.path.getsize(os.path.join(dp, f))
        for dp, dn, fnames in os.walk(VECTORDB_DIR)
        for f in fnames
    ) if os.path.exists(VECTORDB_DIR) else 0
    lines.append(f"**Disk: {size_bytes / (1024*1024):.1f} MB**")

    return "\n".join(lines)


# ── Existing Tools (kept) ──────────────────────────────────

@mcp.tool()
async def search_ai_news(query: str = "artificial intelligence", limit: int = 5) -> str:
    """Search latest AI news via Brave Search API."""
    limit = min(max(limit, 1), 20)
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            "https://api.search.brave.com/res/v1/web/search",
            headers={"X-Subscription-Token": BRAVE_API_KEY, "Accept": "application/json"},
            params={"q": query, "count": limit, "freshness": "pw"},
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
    """Get GitHub trending repositories."""
    url = "https://github.com/trending"
    if language:
        url += f"/{language}"
    params = {"since": since}

    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        resp = await client.get(url, params=params, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        html = resp.text

    articles = re.findall(r'<article class="Box-row">(.*?)</article>', html, re.DOTALL)

    lines = [f"## GitHub Trending ({since}){f' — {language}' if language else ''}\n"]
    for i, article in enumerate(articles[:10]):
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

    return "\n".join(lines) if len(lines) > 1 else "Could not parse trending repos."


@mcp.tool()
async def get_ai_papers(topic: str = "artificial intelligence", limit: int = 5) -> str:
    """Search recent AI papers on ArXiv."""
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
    """Search AI KOL tweets via Brave Search (Twitter/X results)."""
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
    """Today's AI briefing."""
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
