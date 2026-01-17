import sqlite3
from core.db import q_all, q_one, exec_sql


def list_lines_sorted() -> tuple[list[sqlite3.Row], dict[int, int]]:
    """
    返回按 display_order 排序后的产品线列表 + 显示编号映射（1..n）。
    """
    rows = q_all(
        """
        SELECT *
        FROM product_lines
        ORDER BY COALESCE(display_order, 999999), id
        """
    )
    id2d = {r["id"]: i for i, r in enumerate(rows, start=1)}
    return rows, id2d


def get_line(line_id: int) -> sqlite3.Row | None:
    """按 id 获取产品线。"""
    return q_one("SELECT * FROM product_lines WHERE id=?", (line_id,))


def create_line(name: str, description: str) -> None:
    """新增产品线（display_order 自动追加到末尾）。"""
    maxo = q_one("SELECT COALESCE(MAX(display_order), 0) AS m FROM product_lines")
    m = int(maxo["m"] or 0)
    exec_sql(
        "INSERT INTO product_lines(name, description, display_order) VALUES (?,?,?)",
        (name, description, m + 1),
    )


def update_line(line_id: int, name: str, description: str) -> None:
    """更新产品线。"""
    exec_sql("UPDATE product_lines SET name=?, description=? WHERE id=?", (name, description, line_id))


def delete_line(line_id: int) -> None:
    """删除产品线（级联删除 line_products / relations）。"""
    exec_sql("DELETE FROM product_lines WHERE id=?", (line_id,))


def set_line_display_order(line_id: int, display_order: int) -> None:
    """设置 display_order。"""
    exec_sql("UPDATE product_lines SET display_order=? WHERE id=?", (display_order, line_id))


def normalize_display_order() -> None:
    """将 display_order 规范化为 1..n。"""
    rows = q_all("SELECT id FROM product_lines ORDER BY COALESCE(display_order, 999999), id")
    for i, r in enumerate(rows, start=1):
        exec_sql("UPDATE product_lines SET display_order=? WHERE id=?", (i, r["id"]))

def move_line_rank(line_id: int, new_rank: int) -> None:
    """
    将某条产品线移动到第 new_rank 位（1..n），并把 display_order 重新规范化为 1..n。
    """
    rows = q_all("SELECT id FROM product_lines ORDER BY COALESCE(display_order, 999999), id")
    ids = [r["id"] for r in rows]
    if line_id not in ids:
        return

    n = len(ids)
    new_rank = max(1, min(int(new_rank), n))

    ids.remove(line_id)
    ids.insert(new_rank - 1, line_id)

    for i, lid in enumerate(ids, start=1):
        exec_sql("UPDATE product_lines SET display_order=? WHERE id=?", (i, lid))
