import sqlite3
from core.db import q_all, q_one, exec_sql


def list_glossary() -> list[sqlite3.Row]:
    """返回所有术语（按 term 排序）。"""
    return q_all("SELECT * FROM glossary ORDER BY term")


def get_glossary_term(term_id: int) -> sqlite3.Row | None:
    return q_one("SELECT * FROM glossary WHERE id=?", (term_id,))


def create_glossary_term(term: str, definition: str) -> None:
    exec_sql("INSERT INTO glossary(term, definition) VALUES (?,?)", (term, definition))


def update_glossary_term(term_id: int, term: str, definition: str) -> None:
    exec_sql("UPDATE glossary SET term=?, definition=? WHERE id=?", (term, definition, term_id))


def delete_glossary_term(term_id: int) -> None:
    exec_sql("DELETE FROM glossary WHERE id=?", (term_id,))


def glossary_dict() -> dict[str, str]:
    """返回 {term: definition} 映射，用于文本渲染。"""
    rows = q_all("SELECT term, definition FROM glossary ORDER BY length(term) DESC")
    return {r["term"]: r["definition"] for r in rows}


def check_term_usage() -> dict[str, list[str]]:
    """
    检查每个术语在产品文本中的使用情况。
    返回 {term: [引用该术语的产品code列表]}。
    """
    terms = q_all("SELECT term FROM glossary")
    products = q_all("SELECT code, name, intro, detail FROM products")

    usage: dict[str, list[str]] = {}
    for t in terms:
        term = t["term"]
        refs = []
        for p in products:
            text = " ".join(filter(None, [p["intro"], p["detail"]]))
            if term in text:
                refs.append(p["code"])
        usage[term] = refs
    return usage
