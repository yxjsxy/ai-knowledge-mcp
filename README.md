# ai-knowledge MCP Server

AI knowledge aggregator via [MCP](https://modelcontextprotocol.io) — search news, GitHub trending, ArXiv papers, and AI KOL tweets.

## Tools

| Tool | Description |
|------|-------------|
| `search_ai_news` | Search latest AI news (Brave Search) |
| `get_github_trending` | GitHub trending repos (scrape) |
| `get_ai_papers` | ArXiv paper search |
| `search_kol_tweets` | AI KOL tweets via Grok/xAI |

## Resource

| URI | Description |
|-----|-------------|
| `daily://ai-briefing` | Combined daily AI briefing |

## Setup

```bash
cd ai_knowledge_mcp
python3 -m venv .venv && source .venv/bin/activate
pip install fastmcp httpx beautifulsoup4

# Set API keys
export BRAVE_API_KEY="your_key"
export XAI_API_KEY="your_key"    # optional, for KOL tweets
```

## Run

```bash
# Inspector (dev/test)
fastmcp dev server.py

# Install in Claude Desktop
fastmcp install server.py --name "AI Knowledge" \
  -e BRAVE_API_KEY="$BRAVE_API_KEY" \
  -e XAI_API_KEY="$XAI_API_KEY"
```

## Claude Desktop Config

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ai-knowledge": {
      "command": "/path/to/ai_knowledge_mcp/.venv/bin/python",
      "args": ["/path/to/ai_knowledge_mcp/server.py"],
      "env": {
        "BRAVE_API_KEY": "your_key",
        "XAI_API_KEY": "your_key"
      }
    }
  }
}
```
