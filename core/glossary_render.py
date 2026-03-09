"""
术语高亮渲染：将文本中匹配的术语替换为带悬停/点击解释浮窗的 HTML。
"""
import re
import html
import streamlit as st

from repo.glossary import glossary_dict

_GLOSSARY_STYLE = """
<style>
.gl-term {
  text-decoration: underline;
  text-decoration-color: #e53935;
  text-decoration-thickness: 2px;
  text-underline-offset: 3px;
  font-weight: 600;
  cursor: help;
  position: relative;
  display: inline;
}
.gl-popup {
  display: none;
  position: absolute;
  bottom: calc(100% + 6px);
  left: 50%;
  transform: translateX(-50%);
  background: #222;
  color: #fff;
  padding: 8px 14px;
  border-radius: 6px;
  font-size: 0.85em;
  font-weight: 400;
  white-space: pre-wrap;
  max-width: min(80vw, 600px);
  min-width: 160px;
  width: max-content;
  box-shadow: 0 2px 12px rgba(0,0,0,0.3);
  z-index: 99999;
  line-height: 1.5;
  text-decoration: none;
}
.gl-popup::after {
  content: '';
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  border: 6px solid transparent;
  border-top-color: #222;
}
.gl-term:hover > .gl-popup { display: block; }
</style>
"""


def render_glossary_text(text: str) -> None:
    """
    渲染文本：自动将已注册术语替换为带浮窗解释的高亮 HTML。
    无术语匹配时退化为普通 st.write。
    """
    if not text:
        return

    terms = glossary_dict()
    if not terms:
        st.write(text)
        return

    escaped = html.escape(text)

    # 按 escaped 后的术语长度降序构建正则，避免短词覆盖长词
    escaped_terms = {html.escape(t): d for t, d in terms.items()}
    pattern = "|".join(re.escape(et) for et in escaped_terms.keys())
    regex = re.compile(f"({pattern})")

    def _replace(m):
        matched = m.group(0)
        defn = escaped_terms.get(matched, "")
        defn_escaped = html.escape(defn)
        return (
            f'<span class="gl-term">{matched}'
            f'<span class="gl-popup">{defn_escaped}</span>'
            f'</span>'
        )

    result = regex.sub(_replace, escaped)

    st.markdown(_GLOSSARY_STYLE + result, unsafe_allow_html=True)
