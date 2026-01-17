import streamlit as st

from core.db import init_db
from core.migrations import ensure_schema_migrations
from core.scroll import ensure_router_state, soft_scroll_top, go

from ui_pages.line_page import render_line_page
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
    st.session_state.nav_radio = st.session_state.page

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
    st.sidebar.title("导航")
    pages = ["产品线", "产品详情", "后台管理"]

    # 只要 session_state.page 变了，radio 就会自动显示对应项
    if "nav_radio" not in st.session_state:
        st.session_state.nav_radio = st.session_state.page

    chosen = st.sidebar.radio("页面", pages, key="nav_radio")

    # 统一用 chosen 驱动 page
    if chosen != st.session_state.page:
        go(chosen, line_id=st.session_state.line_id, product_code=st.session_state.product)


    # 手动切页：统一走 go()
    if chosen != st.session_state.page:
        go(chosen, line_id=st.session_state.line_id, product_code=st.session_state.product)

    # Render
    if st.session_state.page == "产品线":
        render_line_page()
    elif st.session_state.page == "产品详情":
        render_product_page()
    else:
        render_admin_page()


if __name__ == "__main__":
    main()
