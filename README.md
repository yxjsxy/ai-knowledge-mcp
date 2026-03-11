# 🔌 AI Knowledge MCP Server

[MCP](https://modelcontextprotocol.io) server for AI knowledge retrieval — semantic search over local ChromaDB + live news/GitHub/papers/KOL tools.

## ✨ Features

- 🔍 **语义搜索** — 本地 ChromaDB 向量检索 AI 知识库
- 📰 **实时新闻** — 在线获取最新 AI 新闻
- 🐙 **GitHub 搜索** — 开源项目和趋势查询
- 📄 **论文检索** — AI 论文搜索
- 👤 **KOL 追踪** — AI 领域意见领袖动态

## 🛠️ Tech Stack

- Python 3 + MCP SDK
- ChromaDB（向量存储）
- FastAPI / HTTP transport

## 📂 Structure

```
server.py         # MCP 服务端主入口
test_tools.py     # 工具测试
```

## 🚀 Usage

```bash
# 启动 MCP Server
python server.py

# 测试工具
python test_tools.py
```
