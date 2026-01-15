import sqlite3
import pandas as pd
import streamlit as st
from streamlit_agraph import agraph, Config

from core.settings import IMG_DIR
from core.scroll import go
from graph.nodes import save_product_image_overwrite
from graph.build_line import build_line_graph

from repo.products import (
    list_products, get_product, create_product, update_product, delete_product
)
from repo.lines import (
    list_lines_sorted, get_line, create_line, update_line, delete_line,
    set_line_display_order, normalize_display_order, move_line_rank
)
from repo.line_content import (
    list_line_members, list_line_members_simple, line_has_product,
    add_product_to_line, update_line_member, remove_product_from_line
)
from repo.relations import (
    list_relations_in_line, create_relation, update_relation, delete_relation,
    delete_relations_of_product_in_line
)


def render_admin_page() -> None:
    """
    后台管理页：
    - 产品库（全局）
    - 产品线管理
    - 产品线内容管理（线内产品 / 线内关系）
    """
    st.subheader("后台管理（3 个模块）")

    module = st.radio(
        "后台模块",
        ["产品库（全局）", "产品线管理", "产品线内容管理"],
        index=["产品库（全局）", "产品线管理", "产品线内容管理"].index(st.session_state.admin_module),
        horizontal=True,
        key="admin_module_radio",
    )
    st.session_state.admin_module = module

    prods = list_products()
    lines_now, id2d = list_lines_sorted()

    # -------------------- 产品库（全局） --------------------
    if module == "产品库（全局）":
        st.markdown("## 产品库（全局）")

        st.markdown("### 新增产品（图片同型号覆盖）")
        fid = st.session_state.form_product_id

        with st.form(f"create_product_{fid}", clear_on_submit=False):
            code = st.text_input("型号/代号 code*", key=f"new_p_code_{fid}")
            name = st.text_input("产品名*", key=f"new_p_name_{fid}")
            category = st.text_input("类别", key=f"new_p_cat_{fid}")
            intro = st.text_area("简介（用于产品线页）", key=f"new_p_intro_{fid}")
            detail = st.text_area("详情（用于产品详情页）", key=f"new_p_detail_{fid}")
            img = st.file_uploader("图片（可选；同型号覆盖）", type=["png", "jpg", "jpeg", "webp"], key=f"new_p_img_{fid}")
            ok = st.form_submit_button("新增")

        if ok:
            if not code.strip() or not name.strip():
                st.error("code 和 产品名 都不能为空")
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
                    st.error("该 code 已存在。请在下方修改，或换一个 code。")

        st.markdown("### 产品列表")
        rows = list_products()
        st.dataframe(pd.DataFrame([dict(r) for r in rows]) if rows else pd.DataFrame(), width="stretch")

        st.markdown("### 修改 / 删除产品")
        if not rows:
            st.info("暂无产品。")
            return

        labels = [f'{p["code"]} | {p["name"]}' for p in rows]
        pick = st.selectbox("选择产品", labels, key="admin_pick_product")
        code0 = pick.split(" | ")[0].strip()
        p = get_product(code0)

        colA, colB = st.columns([2, 1], gap="large")
        with colA:
            with st.form("edit_product"):
                name2 = st.text_input("产品名", p["name"])
                category2 = st.text_input("类别", p["category"] or "")
                intro2 = st.text_area("简介", p["intro"] or "")
                detail2 = st.text_area("详情", p["detail"] or "")
                img2 = st.file_uploader("替换图片（可选；同型号覆盖）", type=["png", "jpg", "jpeg", "webp"])
                clear_img = st.checkbox("清空图片（变成无图片）", value=False)
                ok2 = st.form_submit_button("保存修改")

            if ok2:
                image_path = p["image_path"]
                if clear_img:
                    image_path = None
                elif img2 is not None:
                    image_path = save_product_image_overwrite(code0, name2.strip(), img2, IMG_DIR)

                update_product(code0, name2.strip(), category2, intro2, detail2, image_path)
                st.success("已保存")
                st.rerun()

        with colB:
            if st.button("删除该产品（级联删除）", key="admin_del_product"):
                delete_product(code0)
                st.success("已删除")
                st.rerun()

    # -------------------- 产品线管理 --------------------
    elif module == "产品线管理":
        st.markdown("## 产品线管理")

        st.markdown("### 新增产品线")
        fid = st.session_state.form_line_id
        with st.form(f"create_line_{fid}", clear_on_submit=False):
            name = st.text_input("产品线名*", key=f"new_line_name_{fid}")
            desc = st.text_area("描述", key=f"new_line_desc_{fid}")
            ok = st.form_submit_button("新增产品线")

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
                    st.error("该产品线名已存在，请换个名字。")

        st.markdown("### 产品线列表")
        lines_now, id2d = list_lines_sorted()
        st.dataframe(pd.DataFrame([dict(r) for r in lines_now]) if lines_now else pd.DataFrame(), width="stretch")

        if not lines_now:
            st.info("暂无产品线。")
            return

        opts = [f'#{id2d[l["id"]]} {l["name"]}' for l in lines_now]
        chosen_line = st.selectbox("选择要修改/删除的产品线", opts, key="admin_line_pick_for_edit")
        lid = int(chosen_line.split(" ")[0].replace("#", "").strip())
        # 由于 display 编号不是 id，这里用 name 查回 id 更稳：
        name_part = chosen_line.split(" ", 1)[1]
        lid = next(l["id"] for l in lines_now if l["name"] == name_part)

        line = get_line(int(lid))

        st.markdown("### 修改 / 删除该产品线")
        colA, colB = st.columns([2, 1], gap="large")
        with colA:
            with st.form("edit_line"):
                name2 = st.text_input("产品线名", line["name"])
                desc2 = st.text_area("描述", line["description"] or "")
                ok2 = st.form_submit_button("保存修改")
            if ok2:
                update_line(int(lid), name2.strip(), desc2)
                st.success("已保存")
                st.rerun()

        with colB:
            if st.button("删除该产品线（级联删除）", key="admin_del_line"):
                delete_line(int(lid))
                st.success("已删除")
                st.rerun()

        st.markdown("### 调整显示编号（下拉顺序）")
        lines_now, id2d = list_lines_sorted()
        opts2 = [f'#{id2d[l["id"]]} {l["name"]}' for l in lines_now]
        pick2 = st.selectbox("选择要调整顺序的产品线", opts2, key="line_reorder_pick")
        name2 = pick2.split(" ", 1)[1]
        lid2 = next(l["id"] for l in lines_now if l["name"] == name2)

        cur_rank = int(id2d.get(lid2, 1))
        new_rank = st.number_input(
            f"新的显示编号（1..{len(lines_now)}，越小越靠前）",
            min_value=1,
            max_value=max(1, len(lines_now)),
            step=1,
            value=cur_rank,
            key=f"line_new_rank_{lid2}",
        )

        c1, c2 = st.columns(2)
        with c1:
            if st.button("保存显示顺序", key="btn_save_line_order"):
                move_line_rank(int(lid2), int(new_rank))
                st.success("已更新显示顺序")
                st.rerun()

        with c2:
            if st.button("重新规范化为 1..n", key="btn_reindex_line_order"):
                normalize_display_order()
                st.success("已规范化为连续编号 1..n")
                st.rerun()

        st.markdown("#### 当前下拉顺序对照（显示编号 / display_order / 产品线名）")
        lines_now2, id2d2 = list_lines_sorted()
        rows = [
            {"显示编号": id2d2[l["id"]], "display_order": l["display_order"], "产品线名": l["name"]}
            for l in lines_now2
        ]
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)



    # -------------------- 产品线内容管理 --------------------
    else:
        st.markdown("## 产品线内容管理（先选产品线，再管该线的产品与关系）")

        if not lines_now:
            st.info("还没有产品线。请先到【产品线管理】新增产品线。")
            return

        current_line_id = st.session_state.admin_selected_line or st.session_state.line_id or lines_now[0]["id"]
        lines_now, id2d = list_lines_sorted()
        lmap = {f'#{id2d[l["id"]]} {l["name"]}': l["id"] for l in lines_now}

        keys = list(lmap.keys())
        vals = list(lmap.values())
        idx = vals.index(current_line_id) if current_line_id in vals else 0

        chosen_line = st.selectbox("选择要管理的产品线", keys, index=idx, key="admin_manage_line")
        lid = int(lmap[chosen_line])
        st.session_state.admin_selected_line = lid

        sub = st.radio(
            "管理内容",
            ["该线包含的产品", "该线产品关系"],
            index=["该线包含的产品", "该线产品关系"].index(st.session_state.admin_line_sub),
            horizontal=True,
            key="admin_line_sub_radio",
        )
        st.session_state.admin_line_sub = sub

        # ---- 线内产品 ----
        if sub == "该线包含的产品":
            if not prods:
                st.info("产品库里还没有产品。请先到【产品库（全局）】新增产品。")
                return

            st.markdown("### 添加产品到该产品线（X/Y 为档位；Main 控制主线）")
            labels = [f'{p["code"]} | {p["name"]}' for p in prods]
            code_map = {lab: lab.split(" | ")[0].strip() for lab in labels}

            fid = st.session_state.form_lp_id
            with st.form(f"add_lp_{fid}", clear_on_submit=False):
                pcode = code_map[st.selectbox("选择产品", labels, key=f"lp_prod_{fid}")]
                sort_order = st.number_input("X：sort_order（档位；支持 0.25/0.5）", step=0.25, value=0.0, key=f"lp_sort_{fid}")
                y_pos = st.number_input("Y：y_pos（档位；0=主线；1=上；-1=下）", step=0.25, value=0.0, key=f"lp_y_{fid}")
                is_main = st.checkbox("主线节点（Main）", value=False, key=f"lp_main_{fid}")
                ok = st.form_submit_button("添加（不覆盖）")

            if ok:
                if line_has_product(lid, pcode):
                    st.warning("该产品已在该产品线中：不会覆盖。请在下方修改 X/Y/Main。")
                else:
                    add_product_to_line(lid, pcode, float(sort_order), float(y_pos), int(is_main))
                    st.success("已添加")
                    st.session_state.form_lp_id += 1
                    st.rerun()

            st.markdown("### 当前该线包含的产品（可修改/移除）")
            rows = list_line_members(lid)
            st.dataframe(pd.DataFrame([dict(r) for r in rows]) if rows else pd.DataFrame(), width="stretch")

            if rows:
                code_list = [r["code"] for r in rows]
                code_to_row = {r["code"]: r for r in rows}

                st.session_state.setdefault("lp_selected_code", code_list[0])
                if st.session_state.lp_selected_code not in code_list:
                    st.session_state.lp_selected_code = code_list[0]

                code_sel = st.selectbox(
                    "选择要修改/移除的项",
                    options=code_list,
                    index=code_list.index(st.session_state.lp_selected_code),
                    key="lp_edit_pick_code",
                    format_func=lambda c: (
                        f'{c} | {code_to_row[c]["name"]} '
                        f'(X={code_to_row[c]["sort_order"]}, Y={code_to_row[c]["y_pos"]}, main={code_to_row[c]["is_main"]})'
                    ),
                )
                st.session_state.lp_selected_code = code_sel
                r = code_to_row[code_sel]

                new_sort = st.number_input("新的 X：sort_order", step=0.25, value=float(r["sort_order"] or 0), key=f"lp_new_sort_{lid}_{code_sel}")
                new_y = st.number_input("新的 Y：y_pos", step=0.25, value=float(r["y_pos"] or 0), key=f"lp_new_y_{lid}_{code_sel}")
                new_main = st.checkbox("主线节点（Main）", value=bool(r["is_main"]), key=f"lp_new_main_{lid}_{code_sel}")

                c1, c2 = st.columns(2)
                with c1:
                    if st.button("保存修改", key="lp_save_sort"):
                        update_line_member(lid, code_sel, float(new_sort), float(new_y), int(new_main))
                        st.success("已保存")
                        st.rerun()

                with c2:
                    if st.button("从该产品线移除该产品（并删除相关关系）", key="lp_remove"):
                        delete_relations_of_product_in_line(lid, code_sel)
                        remove_product_from_line(lid, code_sel)
                        st.success("已移除，并删除相关关系")
                        st.rerun()

                st.markdown("### 小预览（该产品线关系图）")
                _p, nodes_pv, edges_pv = build_line_graph(lid)
                config_pv = Config(width="100%", height=260, directed=True, physics=False, hierarchical=False, nodeHighlightBehavior=True)
                agraph(nodes=nodes_pv, edges=edges_pv, config=config_pv)

        # ---- 线内关系 ----
        else:
            members = list_line_members_simple(lid)
            if not members:
                st.info("该产品线还没有产品。请先把产品加入该线，然后再配置关系。")
                return

            code_to_name = {m["code"]: m["name"] for m in members}
            codes = list(code_to_name.keys())

            st.markdown("### 新增关系（提交时校验）")
            from_code = st.selectbox("from（上游/起点）", options=codes, key=f"rel_from_{lid}", format_func=lambda c: f"{c} | {code_to_name.get(c,'')}")
            to_code = st.selectbox("to（下游/终点）", options=codes, key=f"rel_to_{lid}", format_func=lambda c: f"{c} | {code_to_name.get(c,'')}")
            strength = st.selectbox("强弱", ["strong", "weak"], key=f"rel_strength_{lid}")
            directed = st.selectbox("有向？", [1, 0], key=f"rel_directed_{lid}", format_func=lambda x: "有向(from->to)" if x == 1 else "无向互连")
            rtype = st.text_input("relation_type", "compatible", key=f"rel_type_{lid}")
            edge_label = st.text_input("edge_label（线上的文字）", "", key=f"rel_edge_label_{lid}")


            if st.button("新增关系", key=f"rel_add_btn_{lid}"):
                if from_code == to_code:
                    st.error("from 和 to 不能是同一个产品。")
                else:
                    create_relation(lid, from_code, to_code, strength, int(directed), rtype, edge_label.strip() or None)
                    st.success(f"已新增：{from_code} -> {to_code}")
                    st.rerun()

            st.markdown("### 该产品线内的关系（可修改/删除）")
            rows = list_relations_in_line(lid)
            st.dataframe(pd.DataFrame([dict(r) for r in rows]) if rows else pd.DataFrame(), width="stretch")

            if rows:
                options = [
                    f'#{r["id"]}  {r["from_code"]} | {r["from_name"]}  ->  {r["to_code"]} | {r["to_name"]}   '
                    f'({r["strength"]}, directed={r["directed"]})'
                    for r in rows
                ]
                pick = st.selectbox("选择要修改/删除的关系", options, key="rel_pick")
                r = rows[options.index(pick)]

                with st.form("edit_rel"):
                    strength2 = st.selectbox("强弱", ["strong", "weak"], index=0 if r["strength"] == "strong" else 1)
                    directed2 = st.selectbox("有向？", [1, 0], index=0 if r["directed"] == 1 else 1,
                                            format_func=lambda x: "有向(from->to)" if x == 1 else "无向互连")
                    rtype2 = st.text_input("relation_type", r["relation_type"] or "compatible")
                    edge_label2 = st.text_input("edge_label（线上的文字）", (r["edge_label"] or "") if ("edge_label" in r.keys()) else "")
                    ok2 = st.form_submit_button("保存修改")

                if ok2:
                    update_relation(rel_id, strength2, int(directed2), rtype2, edge_label2.strip() or None)
                    st.success("已保存")
                    st.rerun()

                if st.button("删除该关系", key="rel_del_btn"):
                    delete_relation(int(r["id"]))
                    st.success("已删除")
                    st.rerun()
