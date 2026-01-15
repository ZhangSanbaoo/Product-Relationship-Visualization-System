from core.db import q_all, exec_sql, conn


def ensure_schema_migrations() -> None:
    """
    轻量迁移：兼容旧库缺字段/类型不一致。

    覆盖范围：
    - line_products：补 is_main / y_pos
    - product_lines：补 display_order 并初始化
    - line_products.sort_order / y_pos：若不是 REAL，采用“重建表迁移”方式修正类型
    """

    def _rebuild_line_products_to_real():
        # SQLite 不支持 ALTER COLUMN TYPE：用重建表迁移
        with conn() as c:
            c.executescript(
                """
                PRAGMA foreign_keys=OFF;

                ALTER TABLE line_products RENAME TO line_products_old;

                CREATE TABLE line_products (
                  line_id INTEGER NOT NULL,
                  product_code TEXT NOT NULL,
                  sort_order REAL DEFAULT 0,
                  y_pos REAL,
                  is_main INTEGER NOT NULL DEFAULT 0 CHECK(is_main IN (0,1)),
                  PRIMARY KEY(line_id, product_code),
                  FOREIGN KEY(line_id) REFERENCES product_lines(id) ON DELETE CASCADE,
                  FOREIGN KEY(product_code) REFERENCES products(code) ON DELETE CASCADE
                );

                INSERT INTO line_products(line_id, product_code, sort_order, y_pos, is_main)
                SELECT line_id, product_code, sort_order, y_pos, is_main
                FROM line_products_old;

                DROP TABLE line_products_old;

                PRAGMA foreign_keys=ON;
                """
            )
            c.commit()

    # ---- line_products 补列
    cols = q_all("PRAGMA table_info(line_products)")
    col_names = {c["name"] for c in cols}

    if "is_main" not in col_names:
        exec_sql("ALTER TABLE line_products ADD COLUMN is_main INTEGER NOT NULL DEFAULT 0")

    if "y_pos" not in col_names:
        exec_sql("ALTER TABLE line_products ADD COLUMN y_pos REAL")

    # ---- product_lines 补 display_order
    cols2 = q_all("PRAGMA table_info(product_lines)")
    col2_names = {c["name"] for c in cols2}

    if "display_order" not in col2_names:
        exec_sql("ALTER TABLE product_lines ADD COLUMN display_order INTEGER")
        rows = q_all("SELECT id FROM product_lines ORDER BY id")
        for i, r in enumerate(rows, start=1):
            exec_sql("UPDATE product_lines SET display_order=? WHERE id=?", (i, r["id"]))

    exec_sql("UPDATE product_lines SET display_order=id WHERE display_order IS NULL")

    # -----------------------
    # 迁移：relations.edge_label（旧库补列）
    # -----------------------
    cols_rel = q_all("PRAGMA table_info(relations)")
    rel_names = {c["name"] for c in cols_rel}
    if "edge_label" not in rel_names:
        exec_sql("ALTER TABLE relations ADD COLUMN edge_label TEXT")

    # ---- 类型检查：sort_order / y_pos 是否 REAL
    cols3 = q_all("PRAGMA table_info(line_products)")
    types = {c["name"]: (c["type"] or "").upper() for c in cols3}
    so_type = types.get("sort_order", "")
    y_type = types.get("y_pos", "")

    if "REAL" not in so_type or "REAL" not in y_type:
        _rebuild_line_products_to_real()
