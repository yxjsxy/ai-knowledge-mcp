# ai-knowledge MCP Server

AI knowledge aggregator for Claude Desktop / any MCP client.

## Tools

| Tool | Description |
|------|-------------|
| `search_ai_news` | Search latest AI news (Brave Search) |
| `get_github_trending` | GitHub trending repos |
| `get_ai_papers` | ArXiv paper search |
| `search_kol_tweets` | AI KOL tweets via Brave |

## Resource

- `daily://ai-briefing` — Combined daily AI briefing

## Setup

```bash
cd ai_knowledge_mcp
python3 -m venv .venv && source .venv/bin/activate
pip install fastmcp httpx beautifulsoup4
```

## Run

```bash
# Dev inspector
fastmcp dev server.py

# Install in Claude Desktop
fastmcp install server.py -e BRAVE_SEARCH_API_KEY=your_key
```

## Claude Desktop Config

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ai-knowledge": {
      "command": "/path/to/.venv/bin/python",
      "args": ["/path/to/server.py"],
      "env": {
        "BRAVE_SEARCH_API_KEY": "your_key"
      }
    }
  }
}
```
