import sqlite3
from core.db import q_all, q_one, exec_sql


def list_line_members(line_id: int) -> list[sqlite3.Row]:
    """列出某产品线成员（含产品信息 + X/Y/Main）。"""
    return q_all(
        """
        SELECT p.*, lp.sort_order, lp.y_pos, lp.is_main
        FROM line_products lp
        JOIN products p ON p.code=lp.product_code
        WHERE lp.line_id=?
        ORDER BY lp.sort_order, lp.is_main DESC, p.code
        """,
        (line_id,),
    )


def list_line_members_simple(line_id: int) -> list[sqlite3.Row]:
    """列出某产品线成员（仅 code/name，用于关系配置下拉）。"""
    return q_all(
        """
        SELECT p.code, p.name
        FROM line_products lp
        JOIN products p ON p.code=lp.product_code
        WHERE lp.line_id=?
        ORDER BY lp.sort_order, p.code
        """,
        (line_id,),
    )


def line_has_product(line_id: int, product_code: str) -> bool:
    """判断某产品是否已在该产品线中。"""
    return q_one(
        "SELECT 1 FROM line_products WHERE line_id=? AND product_code=?",
        (line_id, product_code),
    ) is not None


def add_product_to_line(line_id: int, product_code: str, sort_order: float, y_pos: float, is_main: int) -> None:
    """把产品加入产品线（不覆盖）。"""
    exec_sql(
        """
        INSERT INTO line_products(line_id, product_code, sort_order, y_pos, is_main)
        VALUES (?,?,?,?,?)
        """,
        (line_id, product_code, sort_order, y_pos, is_main),
    )


def update_line_member(line_id: int, product_code: str, sort_order: float, y_pos: float, is_main: int) -> None:
    """更新线内成员属性（X/Y/Main）。"""
    exec_sql(
        """
        UPDATE line_products
        SET sort_order=?, y_pos=?, is_main=?
        WHERE line_id=? AND product_code=?
        """,
        (sort_order, y_pos, is_main, line_id, product_code),
    )


def remove_product_from_line(line_id: int, product_code: str) -> None:
    """
    从产品线移除产品。

    注意：
    - 建议先删 relations（避免图里出现引用残留的边）
    """
    exec_sql(
        "DELETE FROM line_products WHERE line_id=? AND product_code=?",
        (line_id, product_code),
    )


def list_lines_for_product(product_code: str) -> list[sqlite3.Row]:
    """列出包含该产品的产品线（用于详情页右侧快捷返回）。"""
    return q_all(
        """
        SELECT pl.*
        FROM line_products lp
        JOIN product_lines pl ON pl.id=lp.line_id
        WHERE lp.product_code=?
        ORDER BY COALESCE(pl.display_order, 999999), pl.id
        """,
        (product_code,),
    )
