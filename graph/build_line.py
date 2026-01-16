from streamlit_agraph import Edge

from core.settings import X_GAP, Y_GAP
from graph.nodes import node_for_product
from repo.line_content import list_line_members
from repo.relations import list_relations_filtered


def build_line_graph(line_id: int):
    """
    生成产品线页图数据（products + nodes + edges）。

    坐标规则（纯手动档位）：
    - x = sort_order * X_GAP
    - y = -y_pos * Y_GAP（y_pos=1 显示在上方）
    """
    products = list_line_members(line_id)
    codes = [p["code"] for p in products]
    rels = list_relations_filtered(line_id, codes)

    def _x(row) -> float:
        try:
            return float(row["sort_order"] or 0.0)
        except Exception:
            return 0.0

    def _y(row) -> float:
        if row["y_pos"] is not None:
            return float(row["y_pos"])
        return 0.0 if int(row["is_main"]) == 1 else 1.0

    nodes = []
    for p in products:
        x = _x(p) * X_GAP
        y = -_y(p) * Y_GAP

        nodes.append(
            node_for_product(
                p["code"],
                p["name"],
                p["image_path"],
                x=int(x),
                y=float(y),
                fixed=True,
            )
        )

    def _edge_text(row) -> str:
        return (row["edge_label"] or "").strip()

    edges = [
        Edge(
            source=r["from_code"],
            target=r["to_code"],
            directed=bool(r["directed"]),
            dashes=(r["strength"] == "weak"),
            label=_edge_text(r) or None,
            title=_edge_text(r) or None,
        )
        for r in rels
    ]

    return products, nodes, edges
