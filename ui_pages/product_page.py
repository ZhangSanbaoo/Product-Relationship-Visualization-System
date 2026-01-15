import streamlit as st
from streamlit_agraph import agraph, Config

from core.scroll import go
from graph.nodes import img_path_or_none, show_image_with_zoom
from graph.build_product_global import build_product_graph_global
from repo.products import list_products
from repo.line_content import list_lines_for_product
from repo.lines import list_lines_sorted


def get_clicked_node(selected):
    """兼容不同 agraph 返回结构。"""
    if not selected:
        return None
    if isinstance(selected, str):
        return selected
    if isinstance(selected, dict):
        if selected.get("node"):
            return selected["node"]
        nodes = selected.get("nodes")
        if isinstance(nodes, list) and nodes:
            return nodes[0]
        s = selected.get("selected")
        if isinstance(s, dict):
            nodes2 = s.get("nodes")
            if isinstance(nodes2, list) and nodes2:
                return nodes2[0]
    return None


def render_product_page() -> None:
    """
    产品详情页：
    - 选择产品
    - 显示跨线的上下游/无向关系图（层级 UD）
    - 展示详情 + 所属产品线快捷返回
    """
    st.subheader("产品详情页面（展示该产品所有可能的上下游/可连接产品）")

    products = list_products()
    if not products:
        st.info("还没有产品。请先到【后台管理】→【产品库（全局）】新增产品。")
        return

    current_code = st.session_state.product or products[0]["code"]
    labels = [f'{p["code"]} | {p["name"]}' for p in products]
    codes = [p["code"] for p in products]
    idx = codes.index(current_code) if current_code in codes else 0

    chosen = st.selectbox("选择产品（下拉）", labels, index=idx, key="product_selectbox")
    code = chosen.split(" | ")[0].strip()
    st.session_state.product = code

    p, nodes, edges = build_product_graph_global(code)
    if not p:
        st.error("产品不存在。")
        return

    st.markdown("#### 上下游/可连接关系图（点击节点 => 跳到该产品详情）")
    config = Config(
        width="100%",
        height=360,
        directed=True,
        physics=False,
        hierarchical=True,
        hierarchy_direction="UD",
        hierarchicalSortMethod="directed",
        nodeHighlightBehavior=True,
    )

    selected = agraph(nodes=nodes, edges=edges, config=config)
    clicked = get_clicked_node(selected)

    if clicked and clicked != code:
        real_code = clicked.split("@@")[0]
        if real_code != code:
            go("产品详情", product_code=real_code)

    st.divider()
    st.markdown("#### 产品详情（左图 / 中详情 / 右相关产品线）")

    left, mid, right = st.columns([1.2, 3.8, 1.6], gap="large")

    with left:
        imgp = img_path_or_none(p["image_path"])
        if imgp:
            show_image_with_zoom(imgp)
        else:
            st.info("无图片")

    with mid:
        st.markdown(f"## {p['code']} / {p['name']}")
        if p["category"]:
            st.caption(p["category"])
        st.markdown("### 详细介绍")
        st.write(p["detail"] or "")

    with right:
        st.markdown("### 存在该产品的产品线（点击跳回产品线）")

        lines2 = list_lines_for_product(code)
        if not lines2:
            st.caption("暂无（还未加入任何产品线）")

        _, id2d = list_lines_sorted()
        for l in lines2:
            if st.button(f"↩ #{id2d.get(l['id'], l['id'])} {l['name']}", key=f"go_line_{l['id']}"):
                go("产品线", line_id=l["id"])
