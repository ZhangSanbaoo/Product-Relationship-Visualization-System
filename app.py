import streamlit as st
import streamlit.components.v1 as components

from core.db import init_db
from core.migrations import ensure_schema_migrations
from core.scroll import ensure_router_state, soft_scroll_top, go

from ui_pages.line_page import render_line_page
from ui_pages.category_page import render_category_page
from ui_pages.product_page import render_product_page
from ui_pages.admin_page import render_admin_page
from ui_pages.chat_panel import render_chat_panel
from repo.lines import list_lines_sorted
from repo.products import get_product
from repo.lines import get_line


def apply_pending_navigation():
    if not st.session_state.pending:
        return

    p = st.session_state.pending
    st.session_state.page = p["page"]
    st.session_state.line_id = p["line_id"]

    if p.get("product") not in (None, ""):
        st.session_state.product = p["product"]

    if st.session_state.page == "产品线" and st.session_state.line_id:
        _, id2d = list_lines_sorted()
        l = get_line(int(st.session_state.line_id))
        if l:
            st.session_state["line_selectbox"] = f'#{id2d.get(l["id"], l["id"])} {l["name"]}'

    if st.session_state.page == "产品详情" and st.session_state.product:
        pr = get_product(st.session_state.product)
        if pr:
            st.session_state["product_selectbox"] = f'{pr["code"]} | {pr["name"]}'

    st.session_state.pending = None


def _render_current_page():
    if st.session_state.page == "产品线":
        render_line_page()
    else:
        components.html(
            '<script>try{var b=window.parent.document.getElementById("float-back-to-graph");if(b)b.remove();}catch(e){}</script>',
            height=0,
        )
        if st.session_state.page == "产品分类":
            render_category_page()
        elif st.session_state.page == "产品详情":
            render_product_page()
        else:
            render_admin_page()


def main():
    st.set_page_config(page_title="产品关系展示（工程化）", layout="wide")

    init_db()
    ensure_schema_migrations()
    ensure_router_state()

    apply_pending_navigation()

    if st.session_state.needs_top:
        st.session_state.needs_top = 0
        st.empty()
        soft_scroll_top()

    # ── 左侧栏（导航） ──
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
                f" {name}", key=f"nav_{name}", icon=icon,
                use_container_width=True, type=btn_type,
            ):
                if name != st.session_state.page:
                    go(name, line_id=st.session_state.line_id, product_code=st.session_state.product)

        st.divider()

        # ── AI 助手开关 ──
        st.session_state.setdefault("chat_expanded", False)
        _chat_label = "收起 AI 助手" if st.session_state.chat_expanded else "AI 助手"
        _chat_icon = ":material/smart_toy:"
        if st.button(
            _chat_label, key="btn_chat_toggle", icon=_chat_icon,
            use_container_width=True,
        ):
            st.session_state.chat_expanded = not st.session_state.chat_expanded
            st.rerun()

        st.divider()
        st.caption("v1.0 · Streamlit + SQLite")

    # ── 主区域 ──
    chat_open = st.session_state.chat_expanded

    CHAT_W = 360       # 侧栏宽度 px
    TOP_BAR = 48       # deploy 横条高度 px

    # ── 全局样式（展开时主内容右移） ──
    if chat_open:
        components.html(f"""
            <script>
            (function() {{
                var doc = window.parent.document;
                var s = doc.getElementById('prvs-rsb-style');
                if (!s) {{ s = doc.createElement('style'); s.id = 'prvs-rsb-style'; doc.head.appendChild(s); }}
                s.textContent = 'section[data-testid="stMain"] {{ padding-right: {CHAT_W}px !important; }}';
                // 清除旧的浮动标签
                var tab = doc.getElementById('prvs-chat-tab');
                if (tab) tab.remove();
            }})();
            </script>
        """, height=0)
    else:
        components.html("""
            <script>
            (function() {
                var doc = window.parent.document;
                var s = doc.getElementById('prvs-rsb-style');
                if (s) s.textContent = '';
                var tab = doc.getElementById('prvs-chat-tab');
                if (tab) tab.remove();
            })();
            </script>
        """, height=0)

    # ── 主内容（正常渲染、正常滚动） ──
    _render_current_page()

    # ── 右侧 AI 侧边栏 ──
    if chat_open:
        chat_anchor = st.container()
        with chat_anchor:
            components.html(f"""
                <script>
                (function() {{
                    var frame = window.frameElement;
                    if (!frame) return;
                    var doc = window.parent.document;

                    var panel = frame;
                    while (panel) {{
                        panel = panel.parentElement;
                        if (panel && panel.getAttribute('data-testid') === 'stVerticalBlock') break;
                    }}
                    if (!panel) return;

                    var app = doc.querySelector('[data-testid="stApp"]');
                    var bg = app ? getComputedStyle(app).backgroundColor : '#ffffff';

                    panel.style.setProperty('position', 'fixed', 'important');
                    panel.style.setProperty('right', '0', 'important');
                    panel.style.setProperty('top', '{TOP_BAR}px', 'important');
                    panel.style.setProperty('width', '{CHAT_W}px', 'important');
                    panel.style.setProperty('height', 'calc(100vh - {TOP_BAR}px)', 'important');
                    panel.style.setProperty('z-index', '999', 'important');
                    panel.style.setProperty('background-color', bg, 'important');
                    panel.style.setProperty('border-left', '1px solid rgba(128,128,128,0.25)', 'important');
                    panel.style.setProperty('padding', '0.5rem 0.8rem 0.5rem', 'important');
                    panel.style.setProperty('box-shadow', '-2px 0 8px rgba(0,0,0,0.06)', 'important');
                    panel.style.setProperty('overflow-y', 'auto', 'important');
                    panel.style.setProperty('overflow-x', 'hidden', 'important');

                    var node = panel.parentElement;
                    while (node && node !== doc.body) {{
                        var cs = getComputedStyle(node);
                        if (cs.transform !== 'none') node.style.setProperty('transform', 'none', 'important');
                        if (cs.perspective !== 'none') node.style.setProperty('perspective', 'none', 'important');
                        node = node.parentElement;
                    }}
                }})();
                </script>
            """, height=0)

            st.markdown("#### :material/smart_toy: AI 助手")
            render_chat_panel()


if __name__ == "__main__":
    main()
