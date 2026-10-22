# AI Knowledge MCP Server

通过 MCP 向 AI 客户端提供本地知识检索，以及在线 AI 新闻、GitHub、论文和社交资料查询。

## 环境与安装

```bash
git clone https://github.com/yxjsxy/ai-knowledge-mcp.git
cd ai-knowledge-mcp
python3 -m venv .venv
source .venv/bin/activate
pip install fastmcp httpx chromadb sentence-transformers
```

当前远端源码使用 **ChromaDB**，索引路径由 `server.py` 的 `VECTORDB_DIR` 指向相邻 `ai_knowledge/vectordb`。需要准备兼容的 collections 和 `BAAI/bge-small-zh-v1.5` embedding 环境；它不能直接读取其他版本 AI Knowledge 的 Qdrant 索引。

## MCP 客户端配置

将客户端的 stdio server 命令设置为本项目虚拟环境 Python，参数为 `server.py` 的绝对路径，并以项目目录作为工作目录。手动启动入口：

```bash
python server.py
```

该命令等待 MCP 协议通信，不会打开 HTTP 网页。

## 使用方法

连接后列出可用工具，再按需调用本地知识搜索、AI 新闻、GitHub 趋势、论文和 KOL 搜索。`daily://ai-briefing` 提供组合简报资源。

在线查询需要相应网络和账号：`BRAVE_API_KEY` 用于搜索相关能力，`GEMINI_API_KEY` 等配置由源码中的相应分支使用。重排还依赖可运行的 Gemini CLI。请提供自己的安全环境配置，不依赖历史代码中的默认值。

## 限制

此仓库没有统一锁定依赖或全功能安装器；先确认所用客户端 SDK 与传输兼容。没有索引时，在线查询成功不表示本地 RAG 可用；健康/连接检查也不能代替真实检索。结果可能不完整，应核对原始来源与日期。
