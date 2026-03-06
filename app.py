import streamlit as st

from core.db import init_db
from core.migrations import ensure_schema_migrations
from core.scroll import ensure_router_state, soft_scroll_top, go

from ui_pages.line_page import render_line_page
from ui_pages.category_page import render_category_page
from ui_pages.product_page import render_product_page
from ui_pages.admin_page import render_admin_page
from repo.lines import list_lines_sorted
from repo.products import get_product
from repo.lines import get_line


def apply_pending_navigation():
    """
    应用 pending 跳转意图，并同步 UI 下拉框显示值（避免 UI 与状态不一致）。
    """
    if not st.session_state.pending:
        return

    p = st.session_state.pending
    st.session_state.page = p["page"]
    st.session_state.line_id = p["line_id"]

    if p.get("product") not in (None, ""):
        st.session_state.product = p["product"]

    # 同步产品线下拉显示值
    if st.session_state.page == "产品线" and st.session_state.line_id:
        _, id2d = list_lines_sorted()
        l = get_line(int(st.session_state.line_id))
        if l:
            st.session_state["line_selectbox"] = f'#{id2d.get(l["id"], l["id"])} {l["name"]}'

    # 同步产品下拉显示值
    if st.session_state.page == "产品详情" and st.session_state.product:
        pr = get_product(st.session_state.product)
        if pr:
            st.session_state["product_selectbox"] = f'{pr["code"]} | {pr["name"]}'

    st.session_state.pending = None


def main():
    st.set_page_config(page_title="产品关系展示（工程化）", layout="wide")

    init_db()
    ensure_schema_migrations()
    ensure_router_state()

    apply_pending_navigation()

    # 回顶兜底
    if st.session_state.needs_top:
        st.session_state.needs_top = 0
        st.empty()
        soft_scroll_top()

    # Sidebar
    NAV_ITEMS = [
        ("产品线",   ":material/account_tree:"),
        ("产品分类", ":material/category:"),
        ("产品详情", ":material/info:"),
        ("后台管理", ":material/settings:"),
    ]

    with st.sidebar:
        st.markdown(
            "<h2 style='text-align:center; margin-bottom:0.2em;'>PRVS</h2>"
            "<p style='text-align:center; font-size:0.82em; color:gray; margin-top:0;'>"
            "产品关系可视化系统</p>",
            unsafe_allow_html=True,
        )
        st.divider()

        for name, icon in NAV_ITEMS:
            btn_type = "primary" if st.session_state.page == name else "secondary"
            if st.button(
                f" {name}",
                key=f"nav_{name}",
                icon=icon,
                use_container_width=True,
                type=btn_type,
            ):
                if name != st.session_state.page:
                    go(name, line_id=st.session_state.line_id, product_code=st.session_state.product)

        st.divider()
        st.caption("v1.0 · Streamlit + SQLite")

    # Render
    if st.session_state.page == "产品线":
        render_line_page()
    elif st.session_state.page == "产品分类":
        render_category_page()
    elif st.session_state.page == "产品详情":
        render_product_page()
    else:
        render_admin_page()


if __name__ == "__main__":
    main()
