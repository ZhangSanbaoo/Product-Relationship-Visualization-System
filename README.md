# PRVS – Product Relationship Visualization System

PRVS 是一个基于 **Streamlit + SQLite + Graph Visualization** 的本地部署产品关系可视化与管理系统，用于构建、维护和分析复杂产品体系中的上下游关系、依赖关系及产品线结构。

本项目适用于：
- 企业内部产品架构梳理
- 系统依赖关系管理
- 技术产品线规划
- 架构评审与知识沉淀

---

# PRVS – Product Relationship Visualization System

PRVS is a **locally deployed web-based product relationship management and visualization system** built with Streamlit, SQLite, and interactive graph rendering.

It helps teams model, manage, and analyze complex product ecosystems including dependencies, upstream/downstream relationships, and product line structures.

---

## ✨ 功能特性 | Features

### 中文

- 📦 全局产品库管理（增删改查 + 图片支持）
- 🧩 产品线管理与排序（支持显示顺序调整）
- 🔗 产品关系管理（有向 / 无向，强 / 弱关系，支持线上文字标注）
- 🗺 产品线关系图（手动坐标布局，稳定可控）
- 🔍 产品详情页上下游关系图（跨产品线聚合展示）
- 🧠 自动数据库迁移
- 🐳 Docker 容器化部署支持
- ▶ 一键启动脚本支持（run.sh / run.bat）

### English

- Global product repository management (CRUD + images)
- Product line management and ordering
- Relationship management (directed/undirected, strong/weak, edge labels supported)
- Product line visualization with manual layout control
- Global upstream/downstream visualization per product
- Automatic schema migration
- Docker deployment support
- One-click startup scripts (run.sh / run.bat)

---

## 🏗 技术架构 | Architecture

- UI: Streamlit
- Visualization: streamlit-agraph (vis.js)
- Database: SQLite
- Backend: Modular Python architecture
- Deployment: Local execution / Docker container

---

## 🚀 运行方式 | How to Run

### 方式零：一键启动脚本（推荐给非技术用户）

适用于不熟悉 Python 或 Docker 的用户。

#### Linux / macOS

```bash
chmod +x run.sh
./run.sh
```

#### Windows

双击运行：

```
run.bat
```

或在命令行中：

```cmd
run.bat
```

浏览器访问：

```
http://localhost:8501
```

脚本会自动：

- 创建虚拟环境
- 安装依赖
- 启动系统

---

### 方式一：本地运行（Python）

#### 1. 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate
```

#### 2. 安装依赖

```bash
pip install -r requirements.txt
```

#### 3. 启动

```bash
streamlit run app.py
```

---

### 🐳 方式二：使用 Docker（推荐）

#### 构建镜像

```bash
docker build -t prvs .
```

#### 运行容器

```bash
docker run -p 8501:8501 prvs
```

浏览器访问：

```
http://localhost:8501
```

后台运行：

```bash
docker run -d -p 8501:8501 --name prvs_app prvs
```

---

### Option 2: Run with Docker (Recommended)

```bash
docker build -t prvs .
docker run -p 8501:8501 prvs
```

Then open:

```
http://localhost:8501
```

---

## 📁 项目结构 | Project Structure

```
.
├── app.py
├── core/
├── repo/
├── graph/
├── ui_pages/
├── migrations.py
├── requirements.txt
├── Dockerfile
├── run.sh
├── run.bat
├── README.md
└── img/
```

---

## 🧭 项目定位 | Project Type

- 中文：本地部署的产品关系可视化管理系统
- English: Locally deployed web-based product relationship visualization system

---

## 🧩 典型应用场景 | Use Cases

- 产品体系建模
- 系统依赖分析
- 架构评审
- 技术规划
- 内部知识库

---

## 📜 License

MIT License (free to use, modify and commercialize)

---

## 👤 作者 | Author

Developed by: 张三包  
GitHub Repository: https://github.com/ZhangSanbaoo/Product-Relationship-Visualization-System

---

## 🛣 Roadmap

- [ ] 权限系统 / Authentication & authorization
- [ ] 导入/导出 JSON
- [ ] 图自动布局算法
- [ ] 多用户支持
- [ ] Web 公网部署模式

---

如果你觉得这个项目对你有帮助，欢迎 Star ⭐ 或 Fork 🚀
