# 产品关系可视化管理系统（Product Relationship Visualization System, PRVS）

一个基于 **Streamlit + SQLite + Python** 的本地部署 Web
应用，用于对多个产品线中的产品关系进行建模、管理与可视化展示。\
该系统适用于工程设计阶段的系统架构梳理、产品组合分析、上下游依赖管理以及内部产品资产管理等场景。

------------------------------------------------------------------------

## ✨ 主要功能

-   📦 **产品库管理**
    -   统一维护产品基本信息、分类、简介、详细说明与图片
    -   支持新增、修改、删除产品（自动级联清理关联关系）
-   🧩 **产品线建模**
    -   定义多个产品线（系统线 / 业务线 / 架构线等）
    -   为每条产品线配置产品成员及显示顺序
-   🔗 **产品关系管理**
    -   支持有向 / 无向关系
    -   支持强连接 / 弱连接
    -   支持在线路上标注自定义文字（如：RS485、CAN、24V、电源、信号等）
-   🗺️ **关系图可视化**
    -   产品线视角：左 → 右分层结构展示
    -   产品详情视角：跨产品线的上下游依赖关系图
    -   支持节点点击跳转与悬浮提示
-   🛠 **后台管理界面**
    -   产品管理
    -   产品线管理（含显示顺序调整）
    -   关系管理与实时预览

------------------------------------------------------------------------

## 🧱 技术架构

-   前端/交互：Streamlit
-   图可视化：streamlit-agraph（基于 vis.js）
-   数据库：SQLite
-   后端逻辑：Python 模块化分层设计

项目结构：

    core/        # 数据库连接、迁移、全局配置
    repo/        # 数据访问层（Products / Lines / Relations）
    graph/       # 图构建逻辑（节点、边、布局）
    ui_pages/    # Streamlit 页面模块
    app.py       # 应用入口

------------------------------------------------------------------------

## 🚀 运行方式

### 1. 安装依赖

``` bash
pip install -r requirements.txt
```

### 2. 启动应用

``` bash
streamlit run app.py
```

浏览器访问：

    http://localhost:8501

------------------------------------------------------------------------

## 🗄 数据说明

-   默认使用本地 SQLite 数据库：`data.sqlite3`
-   支持自动表结构迁移
-   产品图片存储在 `img/` 目录

> 建议在 GitHub 提交时忽略数据库文件与真实图片数据。

------------------------------------------------------------------------

## 📌 适用场景

-   系统架构设计与产品依赖梳理
-   工业控制系统产品组合分析
-   IoT / 嵌入式系统组件关系管理
-   内部产品资产管理与技术文档辅助

------------------------------------------------------------------------

## 📄 License

MIT License（可根据需要调整）

------------------------------------------------------------------------

# Product Relationship Visualization System (PRVS)

A locally deployed web-based system built with **Streamlit and SQLite**
for modeling, managing, and visualizing product relationships across
multiple product lines.

The system is designed to support system architecture analysis, product
dependency management, and internal product portfolio organization in
engineering and technical environments.

------------------------------------------------------------------------

## ✨ Features

-   📦 **Product Repository Management**
    -   Maintain product metadata, categories, descriptions, and images
    -   Full CRUD support with cascading cleanup
-   🧩 **Product Line Modeling**
    -   Define multiple product lines
    -   Configure product membership and display order
-   🔗 **Relationship Management**
    -   Directed and undirected relationships
    -   Strong and weak connections
    -   Custom edge labels (protocols, power lines, signals, etc.)
-   🗺️ **Graph Visualization**
    -   Left-to-right layered product line view
    -   Global upstream/downstream dependency view
    -   Interactive nodes with hover tooltips
-   🛠 **Admin Panel**
    -   Manage products, product lines, and relations
    -   Real-time preview of relationship graphs

------------------------------------------------------------------------

## 🧱 Architecture

-   Frontend: Streamlit
-   Visualization: streamlit-agraph (vis.js)
-   Database: SQLite
-   Backend: Modular Python architecture

------------------------------------------------------------------------

## 🚀 How to Run

``` bash
pip install -r requirements.txt
streamlit run app.py
```

------------------------------------------------------------------------

## 📌 Use Cases

-   System architecture planning
-   Industrial control product mapping
-   IoT component dependency analysis
-   Internal product asset management

------------------------------------------------------------------------

## 📄 License

MIT License
