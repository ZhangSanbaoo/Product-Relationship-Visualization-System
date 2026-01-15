import sqlite3
from core.db import q_all, q_one, exec_sql


def list_products() -> list[sqlite3.Row]:
    """全局产品列表。"""
    return q_all("SELECT * FROM products ORDER BY code")


def get_product(code: str) -> sqlite3.Row | None:
    """按 code 获取产品。"""
    return q_one("SELECT * FROM products WHERE code=?", (code,))


def create_product(code: str, name: str, category: str, intro: str, detail: str, image_path: str | None) -> None:
    """新增产品。"""
    exec_sql(
        "INSERT INTO products(code, name, category, intro, detail, image_path) VALUES (?,?,?,?,?,?)",
        (code, name, category, intro, detail, image_path),
    )


def update_product(code: str, name: str, category: str, intro: str, detail: str, image_path: str | None) -> None:
    """更新产品。"""
    exec_sql(
        """
        UPDATE products
        SET name=?, category=?, intro=?, detail=?, image_path=?
        WHERE code=?
        """,
        (name, category, intro, detail, image_path, code),
    )


from pathlib import Path
from core.settings import BASE_DIR
from core.db import q_one  # 你文件里已有 q_one，就不用重复导入

def delete_product(code: str) -> None:
    """删除产品（级联删除引用记录）。若图片无其他产品引用，则同时删除图片文件。"""
    # 1) 先取出图片路径
    row = q_one("SELECT image_path FROM products WHERE code=?", (code,))
    img = (row["image_path"] if row else None)

    # 2) 删产品（会级联删 line_products / relations）
    exec_sql("DELETE FROM products WHERE code=?", (code,))

    # 3) 无图片就结束
    if not img:
        return

    # 4) 如果还有其他产品引用这张图，就别删文件
    ref = q_one("SELECT 1 FROM products WHERE image_path=? LIMIT 1", (img,))
    if ref is not None:
        return

    # 5) 删除磁盘文件（相对路径按项目根目录 BASE_DIR 解析）
    p = Path(img)
    if not p.is_absolute():
        p = BASE_DIR / p
    try:
        if p.exists() and p.is_file():
            p.unlink()
    except Exception:
        # 不让图片删除失败影响数据库删除
        pass
