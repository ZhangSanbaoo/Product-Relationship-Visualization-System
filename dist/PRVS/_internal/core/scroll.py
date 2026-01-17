import re
import streamlit as st
import streamlit.components.v1 as components


def safe_dom_id(s: str) -> str:
    """把任意字符串转成安全 DOM id（只保留 0-9a-zA-Z_-）。"""
    return re.sub(r"[^0-9a-zA-Z_-]+", "_", str(s))


def soft_scroll_top() -> None:
    """best-effort 回顶（体验优化；失败不影响功能）。"""
    components.html(
        """
        <script>
        (function(){
          try{
            window.scrollTo(0,0);
            if (window.parent && window.parent.scrollTo) window.parent.scrollTo(0,0);
          }catch(e){}
        })();
        </script>
        """,
        height=0,
    )


def scroll_to_anchor(anchor_id: str, offset: int = 150) -> None:
    """
    滚动到指定 anchor（等待 DOM 渲染，轮询多次）。

    offset：顶部留白，避免被标题遮挡。
    """
    components.html(
        f"""
        <script>
        (function() {{
          const targetId = "{anchor_id}";
          const OFFSET = {int(offset)};

          try {{
            if (window.__st_scroll_timer) {{
              clearInterval(window.__st_scroll_timer);
              window.__st_scroll_timer = null;
            }}
          }} catch(e) {{}}

          function getEl() {{
            try {{
              return window.parent.document.getElementById(targetId) || document.getElementById(targetId);
            }} catch(e) {{
              return document.getElementById(targetId);
            }}
          }}

          function getScrollParent(el) {{
            if (!el) return null;
            const doc = el.ownerDocument;
            let p = el.parentElement;

            while (p) {{
              const style = doc.defaultView.getComputedStyle(p);
              const oy = style.overflowY;
              if ((oy === "auto" || oy === "scroll") && p.scrollHeight > p.clientHeight) return p;
              p = p.parentElement;
            }}

            try {{
              return window.parent.document.querySelector('div[data-testid="stAppViewContainer"]')
                  || window.parent.document.scrollingElement
                  || window.parent.document.documentElement;
            }} catch(e) {{
              return doc.scrollingElement || doc.documentElement;
            }}
          }}

          function relativeTop(el, scrollParent) {{
            let top = 0;
            let cur = el;
            while (cur && cur !== scrollParent) {{
              top += (cur.offsetTop || 0);
              cur = cur.offsetParent;
            }}
            return top;
          }}

          function runOnce() {{
            const el = getEl();
            if (!el) return false;
            const sp = getScrollParent(el);
            if (!sp) return false;

            const targetTop = relativeTop(el, sp) - OFFSET;
            sp.scrollTo({{ top: targetTop, behavior: "smooth" }});
            return true;
          }}

          let tries = 0;
          window.__st_scroll_timer = setInterval(function() {{
            tries++;
            if (runOnce() || tries > 40) {{
              clearInterval(window.__st_scroll_timer);
              window.__st_scroll_timer = null;
            }}
          }}, 120);
        }})();
        </script>
        """,
        height=0,
    )


def ensure_router_state() -> None:
    """统一初始化 session_state 路由字段。"""
    ss = st.session_state
    ss.setdefault("page", "产品线")
    ss.setdefault("line_id", None)
    ss.setdefault("product", "")
    ss.setdefault("pending", None)

    ss.setdefault("scroll_to", None)
    ss.setdefault("needs_top", 0)
    ss.setdefault("frame", 0)

    ss.setdefault("admin_module", "产品库（全局）")
    ss.setdefault("admin_line_sub", "该线包含的产品")
    ss.setdefault("admin_selected_line", None)

    for k in ["form_product_id", "form_line_id", "form_lp_id", "form_rel_id"]:
        ss.setdefault(k, 0)


def go(page_name: str, *, line_id=None, product_code=None) -> None:
    """
    统一跳转入口：用 pending 保存跳转意图，然后 rerun 应用。
    """
    st.session_state.scroll_to = None
    st.session_state.pending = dict(page=page_name, line_id=line_id, product=product_code)
    st.session_state.needs_top = 1
    st.session_state.frame += 1
    st.rerun()
