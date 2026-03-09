# PRVS — Product Relationship Visualization System

> **中文** | [English](#english)

## 简介

PRVS 是一个基于 Streamlit + SQLite 的本地产品关系可视化管理系统。它帮助团队建模、管理和分析产品体系中的上下游依赖、连接关系与产品线结构，并内置 AI 对话助手，可基于数据库内容智能问答。

## 功能

- **产品线视图** — 交互式关系图（手动坐标布局），点击节点滚动到产品卡片并高亮，浮动按钮快速返回图表
- **产品分类浏览** — 按类别筛选产品，查看简介
- **产品详情** — 跨产品线聚合展示上下游与无向关系图，一键跳转关联产品线
- **后台管理** — 产品库 CRUD（含图片上传）、产品线管理与排序、线内成员与关系配置、实时图预览
- **术语系统** — 自定义术语表，产品文本中自动高亮并悬停显示解释，后台可查看术语引用状态
- **AI 对话助手** — 支持本地 GGUF 模型和在线 API（OpenAI / DeepSeek / 通义千问 / 智谱 GLM / Moonshot 等），基于数据库内容的 RAG 问答，分级上下文策略适配不同模型
- **自动迁移** — 数据库 schema 自动升级，兼容旧库
- **多种部署** — 本地 Python / Docker / 一键启动脚本 / PyInstaller 打包

## 技术栈

| 层 | 技术 |
|---|------|
| UI | Streamlit |
| 可视化 | streamlit-agraph (vis.js) |
| 数据库 | SQLite |
| AI | OpenAI 兼容 API / llama-cpp-python (本地 GGUF) |
| 后端 | Python 3.11+，模块化架构 |
| 部署 | 本地 / Docker / PyInstaller |

## 项目结构

```
app.py                      # 入口：路由、导航、AI侧栏
core/
  db.py                     # 数据库连接与通用查询
  migrations.py             # Schema 自动迁移
  settings.py               # 路径与常量配置
  scroll.py                 # 路由状态、滚动、跳转
  ui_utils.py               # 共享 UI 工具函数
  runtime_paths.py          # 打包态/开发态路径适配
  llm_engine.py             # LLM 引擎：本地GGUF + 在线API
  rag_context.py            # RAG 上下文构建（分级策略）
  glossary_render.py        # 术语高亮渲染
repo/
  products.py               # 产品 CRUD
  lines.py                  # 产品线 CRUD 与排序
  line_content.py           # 线内成员管理
  relations.py              # 关系 CRUD 与跨线查询
  glossary.py               # 术语表 CRUD + 引用检测
graph/
  nodes.py                  # 节点构造、图片处理、缩放查看
  build_line.py             # 产品线关系图数据构建
  build_product_global.py   # 产品全局上下游图构建
ui_pages/
  line_page.py              # 产品线页面
  category_page.py          # 产品分类页面
  product_page.py           # 产品详情页面
  admin_page.py             # 后台管理页面
  chat_panel.py             # AI 对话面板
```

## 快速开始

### 方式一：一键启动脚本

**Linux / macOS：**
```bash
chmod +x run.sh && ./run.sh
```

**Windows：**
```
run.bat
```

脚本会自动创建虚拟环境、安装依赖并启动应用。

### 方式二：手动运行

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

### 方式三：Docker

```bash
docker build -t prvs .
docker run -p 8501:8501 prvs
```

启动后访问 `http://localhost:8501`

## AI 对话助手

侧栏点击"AI 助手"按钮即可展开对话面板。支持两种模式：

- **本地 GGUF** — 将 `.gguf` 模型文件放入 `models/` 文件夹，选择模型后加载
- **在线 API** — 选择服务商（或自定义），填入 API Key 后连接。配置自动保存到本地，下次无需重复输入

AI 会严格基于数据库中的产品、产品线、关系和术语信息回答问题，不会编造内容。

## Roadmap

- [ ] 权限系统
- [ ] JSON 导入/导出
- [ ] 图自动布局算法
- [ ] 多用户支持
- [ ] Web 公网部署模式

## License

MIT

## 作者

张三包 — [GitHub](https://github.com/ZhangSanbaoo/Product-Relationship-Visualization-System)

---

<a id="english"></a>

# PRVS — Product Relationship Visualization System

> [中文](#prvs--product-relationship-visualization-system) | **English**

## Overview

PRVS is a locally deployed product relationship visualization and management system built with Streamlit and SQLite. It helps teams model, manage, and analyze upstream/downstream dependencies, connectivity, and product line structures, with a built-in AI chat assistant for database-aware Q&A.

## Features

- **Product Line View** — Interactive relationship graph (manual coordinate layout), click a node to scroll to its product card with highlight animation, floating button to jump back to the graph
- **Category Browser** — Filter products by category with introductions
- **Product Detail** — Cross-line upstream/downstream and undirected relationship graph, quick-jump to related product lines
- **Admin Panel** — Product CRUD (with image upload), product line management and ordering, line member and relationship configuration, live graph preview
- **Glossary System** — Custom glossary with auto-highlighting in product text, hover popups for definitions, usage status tracking in admin
- **AI Chat Assistant** — Supports local GGUF models and online APIs (OpenAI / DeepSeek / Qwen / GLM / Moonshot, etc.), RAG Q&A based on database content, tiered context strategy for different model sizes
- **Auto Migration** — Database schema auto-upgrade, backward compatible
- **Flexible Deployment** — Local Python / Docker / one-click scripts / PyInstaller standalone

## Tech Stack

| Layer | Technology |
|-------|-----------|
| UI | Streamlit |
| Visualization | streamlit-agraph (vis.js) |
| Database | SQLite |
| AI | OpenAI-compatible API / llama-cpp-python (local GGUF) |
| Backend | Python 3.11+, modular architecture |
| Deployment | Local / Docker / PyInstaller |

## Project Structure

```
app.py                      # Entry: routing, navigation, AI sidebar
core/
  db.py                     # Database connection and generic queries
  migrations.py             # Automatic schema migration
  settings.py               # Path and constant configuration
  scroll.py                 # Router state, scrolling, navigation
  ui_utils.py               # Shared UI utilities
  runtime_paths.py          # Packaged/dev mode path resolution
  llm_engine.py             # LLM engine: local GGUF + online API
  rag_context.py            # RAG context builder (tiered strategy)
  glossary_render.py        # Glossary term highlighting
repo/
  products.py               # Product CRUD
  lines.py                  # Product line CRUD and ordering
  line_content.py           # Line member management
  relations.py              # Relationship CRUD and cross-line queries
  glossary.py               # Glossary CRUD + usage detection
graph/
  nodes.py                  # Node construction, image processing, zoom view
  build_line.py             # Product line graph data builder
  build_product_global.py   # Global upstream/downstream graph builder
ui_pages/
  line_page.py              # Product line page
  category_page.py          # Category browser page
  product_page.py           # Product detail page
  admin_page.py             # Admin panel page
  chat_panel.py             # AI chat panel
```

## Quick Start

### Option 1: One-click Script

**Linux / macOS:**
```bash
chmod +x run.sh && ./run.sh
```

**Windows:**
```
run.bat
```

The script automatically creates a virtual environment, installs dependencies, and starts the app.

### Option 2: Manual Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

### Option 3: Docker

```bash
docker build -t prvs .
docker run -p 8501:8501 prvs
```

Then open `http://localhost:8501`

## AI Chat Assistant

Click the "AI Assistant" button in the sidebar to open the chat panel. Two modes are supported:

- **Local GGUF** — Place `.gguf` model files in the `models/` folder, select and load
- **Online API** — Choose a provider (or custom), enter your API Key to connect. Configuration is auto-saved locally for future sessions

The AI strictly answers based on products, product lines, relationships, and glossary data in the database — it will not fabricate information.

## Roadmap

- [ ] Authentication & authorization
- [ ] JSON import/export
- [ ] Automatic graph layout algorithm
- [ ] Multi-user support
- [ ] Public web deployment mode

## License

MIT

## Author

ZhangSanbao — [GitHub](https://github.com/ZhangSanbaoo/Product-Relationship-Visualization-System)
