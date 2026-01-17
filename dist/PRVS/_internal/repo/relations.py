import sqlite3
from core.db import q_all, exec_sql


def list_relations_in_line(line_id: int) -> list[sqlite3.Row]:
    """列出某产品线内所有关系（带 from/to 名称）。"""
    return q_all(
        """
        SELECT r.*,
               a.name AS from_name,
               b.name AS to_name
        FROM relations r
        JOIN products a ON a.code=r.from_code
        JOIN products b ON b.code=r.to_code
        WHERE r.line_id=?
        ORDER BY r.id DESC
        """,
        (line_id,),
    )


def list_relations_filtered(line_id: int, codes: list[str]) -> list[sqlite3.Row]:
    """
    读取线内关系，但只保留 from/to 都在 codes 内的边（用于产品线页作图）。
    """
    if not codes:
        return []
    ph = ",".join(["?"] * len(codes))
    return q_all(
        f"""
        SELECT *
        FROM relations
        WHERE line_id=?
          AND from_code IN ({ph})
          AND to_code IN ({ph})
        """,
        tuple([line_id] + codes + codes),
    )


def create_relation(
    line_id: int,
    from_code: str,
    to_code: str,
    strength: str,
    directed: int,
    relation_type: str,
    edge_label: str | None,
) -> None:
    """新增关系。"""
    exec_sql(
        """
        INSERT INTO relations(line_id, from_code, to_code, strength, directed, relation_type, edge_label)
        VALUES (?,?,?,?,?,?,?)
        """,
        (line_id, from_code, to_code, strength, directed, relation_type, edge_label),
    )


def update_relation(
    rel_id: int,
    strength: str,
    directed: int,
    relation_type: str,
    edge_label: str | None,
) -> None:
    """更新关系。"""
    exec_sql(
        "UPDATE relations SET strength=?, directed=?, relation_type=?, edge_label=? WHERE id=?",
        (strength, directed, relation_type, edge_label, rel_id),
    )


def delete_relation(rel_id: int) -> None:
    """删除关系。"""
    exec_sql("DELETE FROM relations WHERE id=?", (rel_id,))


def delete_relations_of_product_in_line(line_id: int, product_code: str) -> None:
    """删除某产品在线内的所有相关边（用于移除成员前清理）。"""
    exec_sql(
        """
        DELETE FROM relations
        WHERE line_id=?
          AND (from_code=? OR to_code=?)
        """,
        (line_id, product_code, product_code),
    )


def global_upstream(product_code: str) -> list[sqlite3.Row]:
    """跨线：directed=1 且 to_code=本体。"""
    return q_all(
        """
        SELECT r.id, r.line_id, pl.name AS line_name,
               r.from_code, r.to_code, r.strength, r.directed, r.relation_type, r.edge_label,
               a.name AS from_name, a.image_path AS from_img
        FROM relations r
        JOIN products a ON a.code=r.from_code
        JOIN product_lines pl ON pl.id=r.line_id
        WHERE r.to_code=? AND r.directed=1
        """,
        (product_code,),
    )


def global_downstream(product_code: str) -> list[sqlite3.Row]:
    """跨线：directed=1 且 from_code=本体。"""
    return q_all(
        """
        SELECT r.id, r.line_id, pl.name AS line_name,
               r.from_code, r.to_code, r.strength, r.directed, r.relation_type, r.edge_label,
               b.name AS to_name, b.image_path AS to_img
        FROM relations r
        JOIN products b ON b.code=r.to_code
        JOIN product_lines pl ON pl.id=r.line_id
        WHERE r.from_code=? AND r.directed=1
        """,
        (product_code,),
    )


def global_undirected(product_code: str) -> list[sqlite3.Row]:
    """跨线：directed=0 且本体参与其中。"""
    return q_all(
        """
        SELECT r.id, r.line_id, pl.name AS line_name,
               r.from_code, r.to_code, r.strength, r.directed, r.relation_type, r.edge_label,
               a.name AS a_name, b.name AS b_name,
               a.image_path AS a_img, b.image_path AS b_img
        FROM relations r
        JOIN products a ON a.code=r.from_code
        JOIN products b ON b.code=r.to_code
        JOIN product_lines pl ON pl.id=r.line_id
        WHERE r.directed=0 AND (r.from_code=? OR r.to_code=?)
        """,
        (product_code, product_code),
    )
