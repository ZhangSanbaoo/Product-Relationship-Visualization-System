import sqlite3
import pandas as pd
import streamlit as st
from streamlit_agraph import agraph, Config

from core.settings import IMG_DIR
from graph.nodes import save_product_image_overwrite
from graph.build_line import build_line_graph

from repo.products import (
    list_products, get_product, create_product, update_product, delete_product
)
from repo.lines import (
    list_lines_sorted, get_line, create_line, update_line, delete_line,
    normalize_display_order, move_line_rank
)
from repo.line_content import (
    list_line_members, list_line_members_simple, line_has_product,
    add_product_to_line, update_line_member, remove_product_from_line
)
from repo.relations import (
    list_relations_in_line, create_relation, update_relation, delete_relation,
    delete_relations_of_product_in_line
)


# ── helpers ──────────────────────────────────────────────

MODULES = [
    ("产品库",       ":material/inventory_2:"),
    ("产品线",       ":material/linear_scale:"),
    ("产品线内容",   ":material/tune:"),
]

SUB_TABS = [
    ("线内产品", ":material/view_list:"),
    ("线内关系", ":material/cable:"),
]


def _product_df(rows) -> pd.DataFrame:
    """产品列表 → 精简 DataFrame（隐藏大文本字段）。"""
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(
        [{"型号": r["code"], "名称": r["name"], "类别": r["category"] or "", "图片": r["image_path"] or ""} for r in rows]
    )


def _line_df(lines, id2d) -> pd.DataFrame:
    if not lines:
        return pd.DataFrame()
    return pd.DataFrame(
        [{"#": id2d[l["id"]], "名称": l["name"], "描述": l["description"] or ""} for l in lines]
    )


def _member_df(rows) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(
        [{"型号": r["code"], "名称": r["name"], "X": r["sort_order"], "Y": r["y_pos"],
          "主线": "是" if r["is_main"] else ""} for r in rows]
    )


def _relation_df(rows) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(
        [{"ID": r["id"],
          "起点": f'{r["from_code"]} {r["from_name"]}',
          "终点": f'{r["to_code"]} {r["to_name"]}',
          "强弱": r["strength"],
          "有向": "→" if r["directed"] else "↔",
          "标签": r["edge_label"] or ""} for r in rows]
    )


# ── main render ──────────────────────────────────────────

def render_admin_page() -> None:
    st.markdown("#### :material/settings: 后台管理")

    # ── 模块切换按钮 ──
    cols = st.columns(len(MODULES))
    for col, (name, icon) in zip(cols, MODULES):
        with col:
            btn_type = "primary" if st.session_state.admin_module == name else "secondary"
            if st.button(name, key=f"adm_{name}", icon=icon, use_container_width=True, type=btn_type):
                if st.session_state.admin_module != name:
                    st.session_state.admin_module = name
                    st.rerun()

    st.divider()

    module = st.session_state.admin_module
    prods = list_products()
    lines_now, id2d = list_lines_sorted()

    if module == "产品库":
        _render_products(prods)
    elif module == "产品线":
        _render_lines(lines_now, id2d)
    else:
        _render_line_content(prods, lines_now, id2d)


# ── 产品库 ───────────────────────────────────────────────

def _render_products(prods):
    # 新增（折叠）
    with st.expander(":material/add_circle: 新增产品", expanded=False):
        fid = st.session_state.form_product_id
        with st.form(f"create_product_{fid}", clear_on_submit=False):
            c1, c2 = st.columns(2)
            with c1:
                code = st.text_input("型号 code *", key=f"new_p_code_{fid}")
                category = st.text_input("类别", key=f"new_p_cat_{fid}")
            with c2:
                name = st.text_input("产品名 *", key=f"new_p_name_{fid}")
                img = st.file_uploader("图片", type=["png", "jpg", "jpeg", "webp"], key=f"new_p_img_{fid}")
            intro = st.text_area("简介（产品线页展示）", key=f"new_p_intro_{fid}", height=80)
            detail = st.text_area("详情（详情页展示）", key=f"new_p_detail_{fid}", height=80)
            ok = st.form_submit_button("新增", icon=":material/add:")

        if ok:
            if not code.strip() or not name.strip():
                st.error("code 和产品名不能为空")
            else:
                image_path = None
                if img is not None:
                    image_path = save_product_image_overwrite(code.strip(), name.strip(), img, IMG_DIR)
                try:
                    create_product(code.strip(), name.strip(), category, intro, detail, image_path)
                    st.success("已新增")
                    st.session_state.form_product_id += 1
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("该 code 已存在，请换一个或在下方修改。")

    # 列表
    rows = list_products()
    st.dataframe(_product_df(rows), use_container_width=True, hide_index=True)

    if not rows:
        st.info("暂无产品。")
        return

    # 编辑 / 删除
    st.markdown("##### 编辑产品")
    labels = [f'{p["code"]} | {p["name"]}' for p in rows]
    pick = st.selectbox("选择产品", labels, key="admin_pick_product", label_visibility="collapsed")
    code0 = pick.split(" | ")[0].strip()
    p = get_product(code0)

    with st.form("edit_product"):
        c1, c2 = st.columns(2)
        with c1:
            name2 = st.text_input("产品名", p["name"])
            category2 = st.text_input("类别", p["category"] or "")
        with c2:
            img2 = st.file_uploader("替换图片", type=["png", "jpg", "jpeg", "webp"], key=f"edit_p_img_{code0}")
            clear_img = st.checkbox("清空图片", value=False)
        intro2 = st.text_area("简介", p["intro"] or "", height=80)
        detail2 = st.text_area("详情", p["detail"] or "", height=80)

        fc1, fc2 = st.columns([3, 1])
        with fc1:
            ok2 = st.form_submit_button("保存修改", icon=":material/save:")
        with fc2:
            do_del = st.form_submit_button("删除该产品", icon=":material/delete:", type="secondary")

    if ok2:
        image_path = p["image_path"]
        if clear_img:
            image_path = None
        elif img2 is not None:
            image_path = save_product_image_overwrite(code0, name2.strip(), img2, IMG_DIR)
        update_product(code0, name2.strip(), category2, intro2, detail2, image_path)
        st.success("已保存")
        st.rerun()

    if do_del:
        delete_product(code0)
        st.success("已删除")
        st.rerun()


# ── 产品线管理 ───────────────────────────────────────────

def _render_lines(lines_now, id2d):
    # 新增（折叠）
    with st.expander(":material/add_circle: 新增产品线", expanded=False):
        fid = st.session_state.form_line_id
        with st.form(f"create_line_{fid}", clear_on_submit=False):
            name = st.text_input("产品线名 *", key=f"new_line_name_{fid}")
            desc = st.text_area("描述", key=f"new_line_desc_{fid}", height=80)
            ok = st.form_submit_button("新增", icon=":material/add:")

        if ok:
            if not name.strip():
                st.error("产品线名不能为空")
            else:
                try:
                    create_line(name.strip(), desc)
                    st.success("已新增")
                    st.session_state.form_line_id += 1
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("该产品线名已存在。")

    # 列表
    lines_now, id2d = list_lines_sorted()
    st.dataframe(_line_df(lines_now, id2d), use_container_width=True, hide_index=True)

    if not lines_now:
        st.info("暂无产品线。")
        return

    # 选择
    line_map = {f'#{id2d[l["id"]]} {l["name"]}': l["id"] for l in lines_now}
    opts = list(line_map.keys())
    chosen_line = st.selectbox("选择产品线", opts, key="admin_line_pick_for_edit", label_visibility="collapsed")
    lid = line_map[chosen_line]
    line = get_line(int(lid))

    # 编辑 + 排序 + 删除放在两栏
    left, right = st.columns([2, 1], gap="large")

    with left:
        st.markdown("##### 编辑")
        with st.form("edit_line"):
            name2 = st.text_input("产品线名", line["name"])
            desc2 = st.text_area("描述", line["description"] or "", height=80)
            ok2 = st.form_submit_button("保存修改", icon=":material/save:")
        if ok2:
            update_line(int(lid), name2.strip(), desc2)
            st.success("已保存")
            st.rerun()

    with right:
        st.markdown("##### 排序 & 操作")
        cur_rank = int(id2d.get(lid, 1))
        new_rank = st.number_input(
            f"显示位置（1‥{len(lines_now)}）",
            min_value=1, max_value=max(1, len(lines_now)), step=1,
            value=cur_rank, key=f"line_new_rank_{lid}",
        )
        c1, c2 = st.columns(2)
        with c1:
            if st.button("保存排序", key="btn_save_line_order", icon=":material/swap_vert:", use_container_width=True):
                move_line_rank(int(lid), int(new_rank))
                st.success("已更新")
                st.rerun()
        with c2:
            if st.button("规范化 1‥n", key="btn_reindex", icon=":material/format_list_numbered:", use_container_width=True):
                normalize_display_order()
                st.success("已规范化")
                st.rerun()

        st.divider()
        if st.button("删除该产品线", key="admin_del_line", icon=":material/delete:", type="secondary", use_container_width=True):
            delete_line(int(lid))
            st.success("已删除")
            st.rerun()


# ── 产品线内容管理 ───────────────────────────────────────

def _render_line_content(prods, lines_now, id2d):
    if not lines_now:
        st.info("还没有产品线，请先到【产品线】模块新增。")
        return

    current_line_id = st.session_state.admin_selected_line or st.session_state.line_id or lines_now[0]["id"]
    lines_now, id2d = list_lines_sorted()
    lmap = {f'#{id2d[l["id"]]} {l["name"]}': l["id"] for l in lines_now}
    keys = list(lmap.keys())
    vals = list(lmap.values())
    idx = vals.index(current_line_id) if current_line_id in vals else 0

    chosen_line = st.selectbox("选择产品线", keys, index=idx, key="admin_manage_line")
    lid = int(lmap[chosen_line])
    st.session_state.admin_selected_line = lid

    # 子模块按钮
    sc1, sc2 = st.columns(2)
    with sc1:
        btn_type = "primary" if st.session_state.admin_line_sub == "该线包含的产品" else "secondary"
        if st.button("线内产品", key="sub_prod", icon=":material/view_list:", use_container_width=True, type=btn_type):
            if st.session_state.admin_line_sub != "该线包含的产品":
                st.session_state.admin_line_sub = "该线包含的产品"
                st.rerun()
    with sc2:
        btn_type = "primary" if st.session_state.admin_line_sub == "该线产品关系" else "secondary"
        if st.button("线内关系", key="sub_rel", icon=":material/cable:", use_container_width=True, type=btn_type):
            if st.session_state.admin_line_sub != "该线产品关系":
                st.session_state.admin_line_sub = "该线产品关系"
                st.rerun()

    st.divider()

    if st.session_state.admin_line_sub == "该线包含的产品":
        _render_line_members(prods, lid)
    else:
        _render_line_relations(lid)


def _render_line_members(prods, lid):
    if not prods:
        st.info("产品库为空，请先到【产品库】新增产品。")
        return

    # 添加（折叠）
    with st.expander(":material/add_circle: 添加产品到该线", expanded=False):
        labels = [f'{p["code"]} | {p["name"]}' for p in prods]
        code_map = {lab: lab.split(" | ")[0].strip() for lab in labels}

        fid = st.session_state.form_lp_id
        with st.form(f"add_lp_{fid}", clear_on_submit=False):
            pcode = code_map[st.selectbox("选择产品", labels, key=f"lp_prod_{fid}")]
            c1, c2, c3 = st.columns(3)
            with c1:
                sort_order = st.number_input("X (sort_order)", step=0.25, value=0.0, key=f"lp_sort_{fid}")
            with c2:
                y_pos = st.number_input("Y (y_pos)", step=0.25, value=0.0, key=f"lp_y_{fid}")
            with c3:
                is_main = st.checkbox("主线节点", value=False, key=f"lp_main_{fid}")
            ok = st.form_submit_button("添加", icon=":material/add:")

        if ok:
            if line_has_product(lid, pcode):
                st.warning("该产品已在线内，请在下方修改。")
            else:
                add_product_to_line(lid, pcode, float(sort_order), float(y_pos), int(is_main))
                st.success("已添加")
                st.session_state.form_lp_id += 1
                st.rerun()

    # 成员列表
    rows = list_line_members(lid)
    st.dataframe(_member_df(rows), use_container_width=True, hide_index=True)

    if not rows:
        return

    # 编辑成员
    st.markdown("##### 编辑成员")
    code_list = [r["code"] for r in rows]
    code_to_row = {r["code"]: r for r in rows}

    st.session_state.setdefault("lp_selected_code", code_list[0])
    if st.session_state.lp_selected_code not in code_list:
        st.session_state.lp_selected_code = code_list[0]

    code_sel = st.selectbox(
        "选择成员", options=code_list,
        index=code_list.index(st.session_state.lp_selected_code),
        key="lp_edit_pick_code", label_visibility="collapsed",
        format_func=lambda c: f'{c} | {code_to_row[c]["name"]}  (X={code_to_row[c]["sort_order"]}, Y={code_to_row[c]["y_pos"]})',
    )
    st.session_state.lp_selected_code = code_sel
    r = code_to_row[code_sel]

    c1, c2, c3 = st.columns(3)
    with c1:
        new_sort = st.number_input("X", step=0.25, value=float(r["sort_order"] or 0), key=f"lp_new_sort_{lid}_{code_sel}")
    with c2:
        new_y = st.number_input("Y", step=0.25, value=float(r["y_pos"] or 0), key=f"lp_new_y_{lid}_{code_sel}")
    with c3:
        new_main = st.checkbox("主线节点", value=bool(r["is_main"]), key=f"lp_new_main_{lid}_{code_sel}")

    bc1, bc2 = st.columns(2)
    with bc1:
        if st.button("保存修改", key="lp_save_sort", icon=":material/save:", use_container_width=True):
            update_line_member(lid, code_sel, float(new_sort), float(new_y), int(new_main))
            st.success("已保存")
            st.rerun()
    with bc2:
        if st.button("移除该产品", key="lp_remove", icon=":material/person_remove:", use_container_width=True, type="secondary"):
            delete_relations_of_product_in_line(lid, code_sel)
            remove_product_from_line(lid, code_sel)
            st.success("已移除")
            st.rerun()

    # 预览图
    with st.expander(":material/preview: 产品线关系图预览", expanded=True):
        _p, nodes_pv, edges_pv = build_line_graph(lid)
        if nodes_pv:
            config_pv = Config(width="100%", height=260, directed=True, physics=False, hierarchical=False, nodeHighlightBehavior=True)
            agraph(nodes=nodes_pv, edges=edges_pv, config=config_pv)


def _render_line_relations(lid):
    members = list_line_members_simple(lid)
    if not members:
        st.info("该线还没有产品，请先添加产品。")
        return

    code_to_name = {m["code"]: m["name"] for m in members}
    codes = list(code_to_name.keys())

    # 新增（折叠）
    with st.expander(":material/add_circle: 新增关系", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            from_code = st.selectbox("起点 (from)", options=codes, key=f"rel_from_{lid}",
                                     format_func=lambda c: f"{c} | {code_to_name.get(c, '')}")
        with c2:
            to_code = st.selectbox("终点 (to)", options=codes, key=f"rel_to_{lid}",
                                   format_func=lambda c: f"{c} | {code_to_name.get(c, '')}")
        c3, c4 = st.columns(2)
        with c3:
            strength = st.selectbox("强弱", ["strong", "weak"], key=f"rel_strength_{lid}")
        with c4:
            directed = st.selectbox("方向", [1, 0], key=f"rel_directed_{lid}",
                                    format_func=lambda x: "有向 →" if x == 1 else "无向 ↔")
        c5, c6 = st.columns(2)
        with c5:
            rtype = st.text_input("关系类型", "compatible", key=f"rel_type_{lid}")
        with c6:
            edge_label = st.text_input("边标签", "", key=f"rel_edge_label_{lid}")

        if st.button("新增关系", key=f"rel_add_btn_{lid}", icon=":material/add:"):
            if from_code == to_code:
                st.error("起点和终点不能相同。")
            else:
                create_relation(lid, from_code, to_code, strength, int(directed), rtype, edge_label.strip() or None)
                st.success(f"已新增：{from_code} → {to_code}")
                st.rerun()

    # 关系列表
    rows = list_relations_in_line(lid)
    st.dataframe(_relation_df(rows), use_container_width=True, hide_index=True)

    if not rows:
        return

    # 编辑 / 删除
    st.markdown("##### 编辑关系")
    options = [
        f'#{r["id"]}  {r["from_code"]} {"→" if r["directed"] else "↔"} {r["to_code"]}  ({r["strength"]})'
        for r in rows
    ]
    pick = st.selectbox("选择关系", options, key="rel_pick", label_visibility="collapsed")
    r = rows[options.index(pick)]

    with st.form("edit_rel"):
        c1, c2 = st.columns(2)
        with c1:
            strength2 = st.selectbox("强弱", ["strong", "weak"], index=0 if r["strength"] == "strong" else 1)
            rtype2 = st.text_input("关系类型", r["relation_type"] or "compatible")
        with c2:
            directed2 = st.selectbox("方向", [1, 0], index=0 if r["directed"] == 1 else 1,
                                     format_func=lambda x: "有向 →" if x == 1 else "无向 ↔")
            edge_label2 = st.text_input("边标签", (r["edge_label"] or "") if ("edge_label" in r.keys()) else "")

        fc1, fc2 = st.columns([3, 1])
        with fc1:
            ok2 = st.form_submit_button("保存修改", icon=":material/save:")
        with fc2:
            do_del = st.form_submit_button("删除该关系", icon=":material/delete:", type="secondary")

    if ok2:
        update_relation(int(r["id"]), strength2, int(directed2), rtype2, edge_label2.strip() or None)
        st.success("已保存")
        st.rerun()

    if do_del:
        delete_relation(int(r["id"]))
        st.success("已删除")
        st.rerun()
