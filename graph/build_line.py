from streamlit_agraph import Edge

from core.settings import X_GAP, Y_GAP, DIAMOND_DX_RATIO, DIAMOND_DY_RATIO
from graph.nodes import node_for_product
from repo.line_content import list_line_members
from repo.relations import list_relations_filtered


def build_line_graph(line_id: int):
    """
    生成产品线页图数据（products + nodes + edges）。

    坐标规则：
    - x = sort_order * X_GAP
    - y = -y_pos * Y_GAP（y_pos=1 显示在上方）
    - 同一 (x,y) 若有多个主线节点：菱形偏移打散
    """
    products = list_line_members(line_id)
    codes = [p["code"] for p in products]
    rels = list_relations_filtered(line_id, codes)

    def x_index(row) -> float:
        try:
            return float(row["sort_order"] or 0.0)
        except Exception:
            return 0.0

    def y_index(row) -> float:
        if row["y_pos"] is not None:
            return float(row["y_pos"])
        return 0.0 if int(row["is_main"]) == 1 else 1.0

    dx = int(X_GAP * DIAMOND_DX_RATIO)
    dy = int(Y_GAP * DIAMOND_DY_RATIO)

    def diamond_offsets(k: int):
        if k <= 1:
            return [(0, 0)]
        offsets = [(0, 0)]
        layer = 1
        while len(offsets) < k:
            ddx = dx * layer
            ddy = dy * layer
            ring = [
                (ddx, 0), (-ddx, 0), (0, ddy), (0, -ddy),
                (ddx, ddy), (-ddx, ddy), (ddx, -ddy), (-ddx, -ddy),
            ]
            for t in ring:
                offsets.append(t)
                if len(offsets) >= k:
                    break
            layer += 1
        return offsets[:k]

    # (x档位, y档位) 的主线分组
    main_groups = {}
    base_xy = {}
    for p in products:
        code = p["code"]
        xk = x_index(p)
        yk = y_index(p)
        base_xy[code] = (xk * X_GAP, -yk * Y_GAP)
        if int(p["is_main"]) == 1:
            main_groups.setdefault((xk, yk), []).append(code)

    main_offsets = {}
    for key, lst in main_groups.items():
        lst.sort()
        offs = diamond_offsets(len(lst))
        for code, (ox, oy) in zip(lst, offs):
            main_offsets[code] = (ox, oy)

    nodes = []
    for p in products:
        code = p["code"]
        bx, by = base_xy[code]
        if int(p["is_main"]) == 1 and code in main_offsets:
            ox, oy = main_offsets[code]
            x, y = bx + ox, by + oy
        else:
            x, y = bx, by

        nodes.append(
            node_for_product(
                code,
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
            label=_edge_text(r) or None,   # ✅ 线上显示
            title=_edge_text(r) or None,   # ✅ hover 提示
        )
        for r in rels
    ]


    return products, nodes, edges
