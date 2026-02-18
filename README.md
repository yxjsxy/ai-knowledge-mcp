# ai-knowledge MCP Server

AI knowledge aggregator via [MCP](https://modelcontextprotocol.io) — semantic search over local ChromaDB + live news/GitHub/papers/KOL tools.

## Tools

| Tool | Description | API Key Required |
|------|-------------|-----------------|
| `semantic_search` | 语义搜索本地 AI 向量知识库（支持 source/date filter + 可选 rerank） | ❌ None |
| `search_ai_news` | Search latest AI news | Brave Search API |
| `get_github_trending` | GitHub trending repos | ❌ None |
| `get_ai_papers` | ArXiv paper search | ❌ None |
| `search_kol_tweets` | AI KOL tweets search | Brave Search API |

## Resource

| URI | Description |
|-----|-------------|
| `daily://ai-briefing` | Combined daily AI briefing (news + trending + papers) |
| `stats://knowledge-base` | 向量知识库统计（collection 数量、日期范围、磁盘占用） |

---

## Quick Start

```bash
git clone https://github.com/yxjsxy/ai-knowledge-mcp.git
cd ai-knowledge-mcp
python3 -m venv .venv && source .venv/bin/activate
pip install fastmcp httpx
```

---

## 🔑 API Keys Setup

### Brave Search API (Required for news & tweet search)

1. Go to [https://brave.com/search/api/](https://brave.com/search/api/)
2. Click **"Get Started for Free"**
3. Sign up with email (or GitHub/Google)
4. Choose **"Free" plan** — 2,000 queries/month, no credit card needed
5. Go to [API Keys](https://api.search.brave.com/app/keys) dashboard
6. Click **"Add API Key"**, give it a name (e.g. `ai-knowledge`)
7. Copy the key (starts with `BSA...`)

### Grok / xAI API (Optional, for enhanced KOL tweet search)

> Coming soon — will provide direct X/Twitter search via Grok API

1. Go to [https://console.x.ai/](https://console.x.ai/)
2. Sign up and create an API key
3. Copy the key (starts with `xai-...`)

### Configure Keys

Create a `.env` file in the project root (**this file is git-ignored and never committed**):

```bash
# .env — DO NOT COMMIT THIS FILE
BRAVE_API_KEY=BSAxxxxxxxxxxxxxxxxxxxxx
XAI_API_KEY=xai-xxxxxxxxxxxxxxxxxxxxx   # optional
```

Or export as environment variables:

```bash
export BRAVE_API_KEY="BSAxxxxxxxxxxxxxxxxxxxxx"
export XAI_API_KEY="xai-xxxxxxxxxxxxxxxxxxxxx"   # optional
```

> ⚠️ **Security**: API keys are loaded from environment variables only. They are NEVER hardcoded in source code. The `.env` file is in `.gitignore`.

---

## Run

```bash
# Dev mode with Inspector UI (test tools interactively)
fastmcp dev server.py

# Install in Claude Desktop
fastmcp install server.py --name "AI Knowledge" \
  -e BRAVE_API_KEY="$BRAVE_API_KEY"
```

## Claude Desktop Config

Alternatively, add manually to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ai-knowledge": {
      "command": "/path/to/ai_knowledge_mcp/.venv/bin/python",
      "args": ["/path/to/ai_knowledge_mcp/server.py"],
      "env": {
        "BRAVE_API_KEY": "your_brave_api_key_here"
      }
    }
  }
}
```

## Cursor / Windsurf / Other MCP Clients

Most MCP clients support stdio transport. Point them to:
- **Command**: `/path/to/.venv/bin/python`
- **Args**: `/path/to/server.py`
- **Env**: `BRAVE_API_KEY=...`

---

## Roadmap

- [ ] Grok API integration for real-time X/Twitter search
- [ ] Hacker News top stories tool
- [ ] Reddit AI subreddit search
- [ ] Fallback search (DuckDuckGo) when no API key configured
- [ ] Caching layer for rate limit management

## License

MIT
