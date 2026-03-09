import streamlit as st

from core.scroll import go
from core.glossary_render import render_glossary_text
from graph.nodes import img_path_or_none, show_image_with_zoom
from repo.products import list_categories, list_products_by_category


def render_category_page() -> None:
    """
    产品分类页：按类别浏览产品，展示简介（intro）。
    """
    st.markdown("#### :material/category: 产品分类")

    categories = list_categories()
    if not categories:
        st.info("还没有带类别的产品。请先到【后台管理】→【产品库（全局）】为产品设置类别。")
        return

    chosen = st.selectbox("选择类别", categories, key="category_selectbox")

    products = list_products_by_category(chosen)
    if not products:
        st.info("该类别下暂无产品。")
        return

    st.caption(f"共 {len(products)} 个产品")

    for p in products:
        code = p["code"]
        with st.container():
            c1, c2, c3 = st.columns([1.2, 3.8, 1.2], gap="large")
            with c1:
                imgp = img_path_or_none(p["image_path"])
                if imgp:
                    show_image_with_zoom(imgp)
                else:
                    st.info("无图片")

            with c2:
                st.markdown(f"### {p['code']} / {p['name']}")
                render_glossary_text(p["intro"] or "")

            with c3:
                st.write("")
                st.write("")
                if st.button("查看详情", key=f"cat_detail_{code}"):
                    go("产品详情", product_code=code)

        st.divider()
