import streamlit as st
import streamlit.components.v1 as components

from core.scroll import safe_dom_id, scroll_to_anchor, go
from core.ui_utils import get_clicked_node
from core.glossary_render import render_glossary_text
from graph.nodes import img_path_or_none, show_image_with_zoom
from graph.build_line import build_line_graph
from repo.lines import list_lines_sorted, get_line


def _inject_float_btn() -> None:
    """注入右下角浮动按钮（纯 JS 滚动到页面锚点）。"""
    components.html(
        """
        <script>
        (function() {
          try { var doc = window.parent.document; } catch(e) { var doc = document; }

          if (!doc.getElementById("float-btn-style")) {
            var s = doc.createElement("style");
            s.id = "float-btn-style";
            s.textContent =
              '#float-back-to-graph{position:fixed;bottom:32px;right:32px;z-index:99999;' +
              'width:44px;height:44px;border-radius:50%;border:none;background:#4A90D9;' +
              'color:#fff;font-size:22px;cursor:pointer;box-shadow:0 2px 8px rgba(0,0,0,.25);' +
              'display:flex;align-items:center;justify-content:center;' +
              'transition:opacity .3s,transform .3s;opacity:0;pointer-events:none;}' +
              '#float-back-to-graph.visible{opacity:1;pointer-events:auto;}' +
              '#float-back-to-graph:hover{transform:scale(1.12);background:#357ABD;}';
            doc.head.appendChild(s);
          }

          var btn = doc.getElementById("float-back-to-graph");
          if (!btn) {
            btn = doc.createElement("button");
            btn.id = "float-back-to-graph";
            btn.title = "回到顶部";
            btn.innerHTML = "\\u21E7";
            doc.body.appendChild(btn);
          }

          // 每次重新绑定 click（移除旧的防止重复）
          btn.onclick = function() {
            var anchor = doc.getElementById("line-page-top");
            if (anchor) anchor.scrollIntoView({ behavior:"smooth", block:"start" });
          };

          function check() {
            var b = doc.getElementById("float-back-to-graph");
            if (!b) return;
            var anchor = doc.getElementById("line-page-top");
            if (!anchor) { b.classList.remove("visible"); return; }
            try {
              if (anchor.getBoundingClientRect().bottom < 0) b.classList.add("visible");
              else b.classList.remove("visible");
            } catch(e) { b.classList.remove("visible"); }
          }

          // 每次 rerun 都重新启动轮询
          if (window.__float_poll) clearInterval(window.__float_poll);
          window.__float_poll = setInterval(check, 400);
          check();
        })();
        </script>
        """,
        height=0,
    )


def render_line_page() -> None:
    # 页面顶部锚点（浮动按钮滚回此处）
    st.markdown('<div id="line-page-top"></div>', unsafe_allow_html=True)
    st.markdown("#### :material/account_tree: 产品线")
    st.caption("左→右分层 · 实线=强关系 · 虚线=弱关系")

    lines, id2d = list_lines_sorted()
    if not lines:
        st.info("还没有产品线。请先到【后台管理】→【产品线管理】新增产品线。")
        return

    current_line_id = st.session_state.line_id or lines[0]["id"]
    line_map = {f'#{id2d[l["id"]]} {l["name"]}': l["id"] for l in lines}
    keys = list(line_map.keys())
    vals = list(line_map.values())
    idx = vals.index(current_line_id) if current_line_id in vals else 0

    if (
        "line_selectbox" not in st.session_state
        or st.session_state["line_selectbox"] not in keys
    ):
        st.session_state["line_selectbox"] = keys[idx]

    chosen = st.selectbox("选择产品线（下拉）", keys, key="line_selectbox")

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

    from streamlit_agraph import agraph, Config
    config = Config(width="100%", height=520, directed=True, physics=False, hierarchical=False, nodeHighlightBehavior=True)
    with st.container(border=True):
        selected = agraph(nodes=nodes, edges=edges, config=config)
    clicked = get_clicked_node(selected)

    # 判断是否有新的节点点击：比较 agraph 原始返回值与上次记录
    # agraph 返回值变化 = 用户点击了不同节点（或首次点击）
    # agraph 返回值不变 = 只是 rerun 重渲染，不应重复滚动
    raw_selected = str(selected) if selected else None
    prev_selected = st.session_state.get("_prev_agraph_selected")

    if clicked and raw_selected != prev_selected:
        real_code = clicked.split("@@")[0]
        st.session_state.scroll_to = real_code
        st.session_state.needs_top = 0

    st.session_state._prev_agraph_selected = raw_selected

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
                render_glossary_text(p["intro"] or "")

            with c3:
                st.write("")
                st.write("")
                if st.button("查看详情", key=f"btn_detail_{code}"):
                    go("产品详情", product_code=code)

        st.divider()

    # 滚动 + 高亮
    if st.session_state.scroll_to:
        a = f"prod-{safe_dom_id(st.session_state.scroll_to)}"
        scroll_to_anchor(a, offset=250, highlight=True)
        st.session_state.scroll_to = None

    # 浮动返回按钮（纯 JS，无需隐藏 Streamlit 按钮）
    _inject_float_btn()
