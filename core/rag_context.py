"""
RAG 上下文构建：从数据库提取信息，组装为 LLM 系统提示词。

分级策略:
  - 在线 API（上下文大）→ 全量模式：所有产品完整信息
  - 本地 GGUF（上下文小）→ 精简模式：产品仅保留摘要，用户提问涉及的产品补充详情
"""
import re

import streamlit as st

from repo.products import list_products, get_product
from repo.lines import list_lines_sorted
from repo.line_content import list_line_members_simple
from repo.relations import list_relations_in_line
from repo.glossary import list_glossary


_ROLE_PROMPT = (
    "你是 PRVS（产品关系可视化系统）的 AI 助手。\n"
    "你必须严格根据下方提供的数据库信息回答用户提问。\n"
    "禁止编造、推测或补充任何数据库中不存在的信息。\n"
    "如果数据库中没有相关内容，请明确回复「数据库中暂无相关信息」。\n"
)


# ── 产品线 + 术语（两种模式共用） ────────────────────────

def _build_lines_section() -> list[str]:
    parts = []
    lines, id2d = list_lines_sorted()
    if lines:
        parts.append("===== 产品线 =====")
        for l in lines:
            parts.append(f"产品线 #{id2d[l['id']]}: {l['name']}")
            if l["description"]:
                parts.append(f"  描述: {l['description']}")

            members = list_line_members_simple(l["id"])
            if members:
                strs = [f"{m['code']}({m['name']})" for m in members]
                parts.append(f"  包含产品: {', '.join(strs)}")

            rels = list_relations_in_line(l["id"])
            if rels:
                parts.append("  关系:")
                for r in rels:
                    arrow = "->" if r["directed"] else "<->"
                    label = f" [{r['edge_label']}]" if r["edge_label"] else ""
                    parts.append(
                        f"    {r['from_code']}({r['from_name']}) "
                        f"{arrow} {r['to_code']}({r['to_name']}) "
                        f"({r['strength']}){label}"
                    )
            parts.append("")
    return parts


def _build_glossary_section() -> list[str]:
    parts = []
    glossary = list_glossary()
    if glossary:
        parts.append("===== 术语表 =====")
        for g in glossary:
            parts.append(f"{g['term']}: {g['definition']}")
        parts.append("")
    return parts


# ── 全量模式（在线 API） ─────────────────────────────────

@st.cache_data(ttl=30)
def build_system_prompt_full() -> str:
    """全量系统提示词：所有产品完整信息。适合大上下文在线模型。"""
    parts = [_ROLE_PROMPT, ""]

    products = list_products()
    if products:
        parts.append("===== 产品库 =====")
        for p in products:
            lines_p = [f"型号: {p['code']}", f"  名称: {p['name']}"]
            if p["category"]:
                lines_p.append(f"  类别: {p['category']}")
            if p["intro"]:
                lines_p.append(f"  简介: {p['intro']}")
            if p["detail"]:
                lines_p.append(f"  详情: {p['detail']}")
            parts.extend(lines_p)
            parts.append("")

    parts.extend(_build_lines_section())
    parts.extend(_build_glossary_section())

    return "\n".join(parts)


# ── 精简模式（本地 GGUF） ────────────────────────────────

INTRO_TRIM = 50  # 精简模式下简介最多保留字符数


@st.cache_data(ttl=30)
def _build_compact_base() -> str:
    """精简基础提示词：产品只保留型号+名称+类别+简介摘要，无详情。"""
    parts = [
        _ROLE_PROMPT,
        "（注意：以下产品信息为摘要，用户询问具体产品时会补充完整详情。）",
        "",
    ]

    products = list_products()
    if products:
        parts.append("===== 产品库（摘要） =====")
        for p in products:
            entry = f"{p['code']} | {p['name']}"
            if p["category"]:
                entry += f" | {p['category']}"
            if p["intro"]:
                intro = p["intro"][:INTRO_TRIM]
                if len(p["intro"]) > INTRO_TRIM:
                    intro += "…"
                entry += f" | {intro}"
            parts.append(entry)
        parts.append("")

    parts.extend(_build_lines_section())
    parts.extend(_build_glossary_section())

    return "\n".join(parts)


@st.cache_data(ttl=30)
def _get_all_product_codes() -> list[str]:
    """获取所有产品型号列表，用于关键词匹配。"""
    products = list_products()
    return [p["code"] for p in products]


def _extract_relevant_codes(user_msg: str, history: list[dict]) -> list[str]:
    """
    从用户当前消息和最近几轮历史中，匹配出涉及的产品型号。
    同时匹配产品名称。
    """
    all_codes = _get_all_product_codes()
    if not all_codes:
        return []

    # 合并文本：当前消息 + 最近 2 轮用户消息
    texts = [user_msg]
    user_msgs = [m["content"] for m in history if m["role"] == "user"]
    texts.extend(user_msgs[-2:])
    combined = " ".join(texts)

    # 匹配型号（不区分大小写）
    matched = set()
    combined_lower = combined.lower()
    for code in all_codes:
        if code.lower() in combined_lower:
            matched.add(code)

    # 也匹配产品名称
    products = list_products()
    for p in products:
        if p["name"] and p["name"] in combined:
            matched.add(p["code"])

    return list(matched)


def _build_product_detail_block(codes: list[str]) -> str:
    """为指定产品型号构建完整详情块。"""
    if not codes:
        return ""

    parts = ["", "===== 相关产品详情 ====="]
    for code in codes:
        p = get_product(code)
        if not p:
            continue
        parts.append(f"型号: {p['code']}")
        parts.append(f"  名称: {p['name']}")
        if p["category"]:
            parts.append(f"  类别: {p['category']}")
        if p["intro"]:
            parts.append(f"  简介: {p['intro']}")
        if p["detail"]:
            parts.append(f"  详情: {p['detail']}")
        parts.append("")

    return "\n".join(parts)


def build_system_prompt_compact(user_msg: str, history: list[dict]) -> str:
    """
    精简系统提示词：基础摘要 + 用户提及产品的完整详情。
    适合上下文较小的本地模型。
    """
    base = _build_compact_base()
    codes = _extract_relevant_codes(user_msg, history)
    detail = _build_product_detail_block(codes)
    return base + detail


# ── 兼容旧接口 ───────────────────────────────────────────

@st.cache_data(ttl=30)
def build_system_prompt() -> str:
    """兼容旧调用，等同于全量模式。"""
    return build_system_prompt_full()
