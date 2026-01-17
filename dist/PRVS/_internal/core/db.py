import sqlite3
from typing import Optional

from core.settings import DB_PATH


def conn() -> sqlite3.Connection:
    """
    创建并返回 SQLite 连接（带 row_factory + foreign_keys）。

    约定：
    - 所有 SQL 使用 ? 参数，占位避免注入
    - foreign_keys 必须每连接开启一次（SQLite 特性）
    """
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON;")
    return c


def q_all(sql: str, params: tuple = ()) -> list[sqlite3.Row]:
    """查询多行。"""
    with conn() as c:
        return c.execute(sql, params).fetchall()


def q_one(sql: str, params: tuple = ()) -> Optional[sqlite3.Row]:
    """查询单行，查不到返回 None。"""
    with conn() as c:
        return c.execute(sql, params).fetchone()


def exec_sql(sql: str, params: tuple = ()) -> int:
    """
    执行写操作并提交。

    Returns:
        lastrowid（INSERT 时有意义）
    """
    with conn() as c:
        cur = c.execute(sql, params)
        c.commit()
        return cur.lastrowid


def init_db() -> None:
    """
    初始化表结构（只负责 CREATE IF NOT EXISTS，不做迁移）。

    注意：
    - SQL 注释只用 -- 或 /* ... */
    """
    with conn() as c:
        c.executescript(
            """
            PRAGMA foreign_keys=ON;

            -- -------------------------
            -- 全局产品库
            -- -------------------------
            CREATE TABLE IF NOT EXISTS products (
              code TEXT PRIMARY KEY,
              name TEXT NOT NULL,
              category TEXT,
              intro TEXT,
              detail TEXT,
              image_path TEXT
            );

            -- -------------------------
            -- 产品线表
            -- -------------------------
            CREATE TABLE IF NOT EXISTS product_lines (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT NOT NULL UNIQUE,
              description TEXT,
              display_order INTEGER
            );

            -- -------------------------
            -- 产品线成员
            -- -------------------------
            CREATE TABLE IF NOT EXISTS line_products (
              line_id INTEGER NOT NULL,
              product_code TEXT NOT NULL,
              sort_order REAL DEFAULT 0,
              y_pos REAL,
              is_main INTEGER NOT NULL DEFAULT 0 CHECK(is_main IN (0,1)),
              PRIMARY KEY(line_id, product_code),
              FOREIGN KEY(line_id) REFERENCES product_lines(id) ON DELETE CASCADE,
              FOREIGN KEY(product_code) REFERENCES products(code) ON DELETE CASCADE
            );

            -- -------------------------
            -- 关系表（按 line_id 隔离）
            -- -------------------------
            CREATE TABLE IF NOT EXISTS relations (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              line_id INTEGER NOT NULL,
              from_code TEXT NOT NULL,
              to_code TEXT NOT NULL,
              strength TEXT NOT NULL CHECK(strength IN ('strong','weak')),
              directed INTEGER NOT NULL DEFAULT 1 CHECK(directed IN (0,1)),
              relation_type TEXT DEFAULT 'compatible',
              edge_label TEXT,  -- 边上显示的文字（例如 RS485/24V/水路）
              FOREIGN KEY(line_id) REFERENCES product_lines(id) ON DELETE CASCADE,
              FOREIGN KEY(from_code) REFERENCES products(code) ON DELETE CASCADE,
              FOREIGN KEY(to_code) REFERENCES products(code) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_rel_line ON relations(line_id);
            CREATE INDEX IF NOT EXISTS idx_rel_from ON relations(from_code);
            CREATE INDEX IF NOT EXISTS idx_rel_to ON relations(to_code);
            CREATE INDEX IF NOT EXISTS idx_lp_line ON line_products(line_id);
            """
        )
        c.commit()
