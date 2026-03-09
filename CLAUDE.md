# CLAUDE.md

> 本文件为 AI 助手（Claude Code）提供项目上下文，帮助其理解代码库。
> This file provides project context for AI assistants (Claude Code).

---

## 项目概览 / Project Overview

PRVS（Product Relationship Visualization System）是基于 Streamlit + SQLite 的本地产品关系可视化管理系统，支持产品建模、上下游依赖分析、产品线关系图展示，并内置 AI 对话助手。

PRVS is a local product relationship visualization and management system built with Streamlit + SQLite. It supports product modeling, upstream/downstream dependency analysis, product line relationship graph display, and includes a built-in AI chat assistant.

---

## 技术栈 / Tech Stack

- **前端 / UI**: Streamlit, streamlit-agraph (vis.js)
- **数据库 / Database**: SQLite (`data.sqlite3`)
- **后端 / Backend**: Python 3.11+
- **AI 对话 / AI Chat**: OpenAI 兼容 API + 本地 GGUF (llama-cpp-python)
- **部署 / Deploy**: 本地 / Docker / PyInstaller

---

## 项目结构 / Project Structure

```
app.py                      # 入口：路由、导航、AI侧栏 / Entry: routing, nav, AI sidebar
core/
  db.py                     # 数据库连接、通用查询 / DB connection, generic queries
  migrations.py             # Schema 自动迁移 / Auto schema migration
  settings.py               # 路径与常量 / Paths and constants
  scroll.py                 # 路由状态、滚动、跳转 / Router state, scrolling, navigation
  ui_utils.py               # 共享 UI 工具 / Shared UI utilities
  runtime_paths.py          # 打包/开发路径适配 / Packaged/dev path resolution
  llm_engine.py             # LLM 引擎：本地GGUF + 在线API / LLM engine: local & API
  rag_context.py            # RAG 上下文构建（分级策略） / RAG context (tiered strategy)
  glossary_render.py        # 术语高亮渲染 / Glossary term highlighting
repo/
  products.py               # 产品 CRUD
  lines.py                  # 产品线 CRUD 与排序 / Product line CRUD & ordering
  line_content.py           # 线内成员管理 / Line member management
  relations.py              # 关系 CRUD 与跨线查询 / Relation CRUD & cross-line queries
  glossary.py               # 术语表 CRUD + 引用检测 / Glossary CRUD + usage detection
graph/
  nodes.py                  # 节点构造、图片处理 / Node building, image handling
  build_line.py             # 产品线关系图 / Product line graph builder
  build_product_global.py   # 产品全局上下游图 / Global upstream/downstream graph
ui_pages/
  line_page.py              # 产品线页面 / Product line page
  category_page.py          # 产品分类页面 / Category browser page
  product_page.py           # 产品详情页面 / Product detail page
  admin_page.py             # 后台管理页面 / Admin panel page
  chat_panel.py             # AI 对话面板 / AI chat panel
```

---

## 关键架构决策 / Key Architecture Decisions

### RAG 分级策略 / Tiered RAG Strategy

AI 对话根据模型类型自动选择不同的上下文注入方式：
The AI chat automatically selects context injection based on model type:

- **在线 API（大上下文）/ Online API (large context)**: 全量注入所有产品完整信息 / Full injection of all product data
- **本地 GGUF（小上下文）/ Local GGUF (small context)**: 精简摘要 + 用户提及产品按需补充详情 / Compact summary + on-demand detail for mentioned products

相关文件 / Related files: `core/rag_context.py`, `core/llm_engine.py`

### 术语系统 / Glossary System

产品简介和详情中的术语会自动高亮，悬停显示解释浮窗。后台可查看每个术语的引用状态。
Glossary terms in product text are auto-highlighted with hover popups. Admin panel shows usage status per term.

相关文件 / Related files: `core/glossary_render.py`, `repo/glossary.py`

### API 配置持久化 / API Config Persistence

在线 API 配置（服务商、URL、Key、模型名）保存在本地 `api_config.json`，已被 `.gitignore` 忽略，不会提交。
Online API config is saved locally in `api_config.json`, which is gitignored and never committed.

---

## 常用命令 / Common Commands

```bash
# 启动 / Start
streamlit run app.py

# 安装依赖 / Install dependencies
pip install -r requirements.txt

# Docker
docker build -t prvs . && docker run -p 8501:8501 prvs
```

---

## 注意事项 / Notes

- 数据库文件 `data.sqlite3` 在 `.gitignore` 中，不会提交 / DB file is gitignored
- `api_config.json` 包含 API Key，已被忽略 / Contains API keys, gitignored
- `models/*.gguf` 本地模型文件已被忽略 / Local model files are gitignored
- LLM API 每次对话都重新发送 system prompt（无状态），不存在"记忆"机制 / LLM API is stateless, system prompt is sent every call
- 本地模型历史轮数限制为 3 轮，在线 API 为 10 轮 / Local model keeps 3 rounds of history, API keeps 10
