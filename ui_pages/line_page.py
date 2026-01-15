import streamlit as st
from streamlit_agraph import agraph, Config

from core.scroll import safe_dom_id, scroll_to_anchor, go
from graph.nodes import img_path_or_none, show_image_with_zoom
from graph.build_line import build_line_graph
from repo.lines import list_lines_sorted, get_line


def get_clicked_node(selected):
    """
    兼容 agraph 版本差异：提取点击的 node id。
    """
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


def render_line_page() -> None:
    """
    产品线页：
    - 选择产品线
    - 显示线内关系图（手动坐标）
    - 下方卡片列表：点击节点 => 滚动到卡片；按钮 => 进入详情页
    """
    st.subheader("产品线页面（左→右分层，强=实线，弱=虚线）")

    lines, id2d = list_lines_sorted()
    if not lines:
        st.info("还没有产品线。请先到【后台管理】→【产品线管理】新增产品线。")
        return

    current_line_id = st.session_state.line_id or lines[0]["id"]
    line_map = {f'#{id2d[l["id"]]} {l["name"]}': l["id"] for l in lines}
    keys = list(line_map.keys())
    vals = list(line_map.values())
    idx = vals.index(current_line_id) if current_line_id in vals else 0

    chosen = st.selectbox("选择产品线（下拉）", keys, index=idx, key="line_selectbox")
    line_id = line_map[chosen]
    st.session_state.line_id = line_id

    line = get_line(int(line_id))
    if line and line["description"]:
        st.caption(line["description"])

    products, nodes, edges = build_line_graph(int(line_id))
    if not products:
        st.warning("该产品线里还没有产品。请先到【后台管理】→【产品线内容管理】加入产品。")
        return

    st.markdown("#### 产品线关系图（点击节点 => 滚动到卡片）")
    config = Config(width="100%", height=520, directed=True, physics=False, hierarchical=False, nodeHighlightBehavior=True)
    selected = agraph(nodes=nodes, edges=edges, config=config)
    clicked = get_clicked_node(selected)

    if clicked:
        real_code = clicked.split("@@")[0]
        st.session_state.scroll_to = real_code
        st.session_state.needs_top = 0

    st.divider()
    st.markdown("#### 产品介绍（左图 / 中介绍 / 右按钮）")

    main_ps = [p for p in products if int(p["is_main"]) == 1]
    sub_ps = [p for p in products if int(p["is_main"]) == 0]
    main_ps.sort(key=lambda r: (float(r["sort_order"] or 0.0), r["code"]))
    sub_ps.sort(key=lambda r: (float(r["sort_order"] or 0.0), r["code"]))

    for p in main_ps + sub_ps:
        code = p["code"]
        anchor = f"prod-{safe_dom_id(code)}"

        with st.container():
            st.markdown(f'<div id="{anchor}"></div>', unsafe_allow_html=True)

            c1, c2, c3 = st.columns([1.2, 3.8, 1.2], gap="large")
            with c1:
                imgp = img_path_or_none(p["image_path"])
                if imgp:
                    show_image_with_zoom(imgp)
                else:
                    st.info("无图片")

            with c2:
                st.markdown(f"### {p['code']} / {p['name']}")
                if p["category"]:
                    st.caption(p["category"])
                st.write(p["intro"] or "")

            with c3:
                st.write("")
                st.write("")
                if st.button("查看详情", key=f"btn_detail_{code}"):
                    go("产品详情", product_code=code)

        st.divider()

    if st.session_state.scroll_to:
        a = f"prod-{safe_dom_id(st.session_state.scroll_to)}"
        scroll_to_anchor(a, offset=250)
        st.session_state.scroll_to = None
