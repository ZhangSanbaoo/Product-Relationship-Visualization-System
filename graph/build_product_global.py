from streamlit_agraph import Edge

from graph.nodes import node_for_product
from repo.products import get_product
from repo.relations import global_upstream, global_downstream, global_undirected


def build_product_graph_global(product_code: str):
    """
    生成详情页全局上下游图（跨产品线）。

    层级：
    - 上游 level=0
    - 本体 level=1
    - 下游 level=2
    - 无向尽量 level=1
    """
    p = get_product(product_code)
    if not p:
        return None, [], []

    upstream = global_upstream(product_code)
    downstream = global_downstream(product_code)
    und = global_undirected(product_code)

    nodes_map = {}

    def shadow_id(code: str, line_id: int, strength: str, tag: str) -> str:
        return f"{code}@@{tag}@@L{line_id}@@{strength}"

    def add_node(node_id: str, name: str, img: str | None, level: int, hover: str | None = None):
        if node_id in nodes_map:
            # 同 id 重复出现时保留更靠上的 level
            try:
                old = nodes_map[node_id].level
                if old is None or level < old:
                    nodes_map[node_id].level = level
            except Exception:
                pass
            return
        nodes_map[node_id] = node_for_product(node_id, name, img, level=level, hover_extra=hover)

    # 本体
    add_node(p["code"], p["name"], p["image_path"], 1)

    # 上游影子
    for r in upstream:
        sid = shadow_id(r["from_code"], r["line_id"], r["strength"], "UP")
        add_node(sid, r["from_name"], r["from_img"], 0, r["line_name"])

    # 下游影子
    for r in downstream:
        sid = shadow_id(r["to_code"], r["line_id"], r["strength"], "DN")
        add_node(sid, r["to_name"], r["to_img"], 2, r["line_name"])

    # 无向
    for r in und:
        add_node(r["from_code"], r["a_name"], r["a_img"], 1, r["line_name"])
        add_node(r["to_code"], r["b_name"], r["b_img"], 1, r["line_name"])

    seen = set()
    edges: list[Edge] = []

    def add_edge(src: str, tgt: str, directed: bool, strength: str, label_text: str | None, edge_id: int):
        if directed:
            key = (src, tgt, "D", strength, edge_id)
        else:
            a, b = sorted([src, tgt])
            key = (a, b, "U", strength, edge_id)
        if key in seen:
            return
        seen.add(key)
        edges.append(
            Edge(
                source=src,
                target=tgt,
                directed=directed,
                dashes=(strength == "weak"),
                id=str(edge_id),
                label=label_text if label_text else None,
                title=label_text if label_text else None,
            )
        )


    for r in upstream:
        sid = shadow_id(r["from_code"], r["line_id"], r["strength"], "UP")
        label_text = (r["edge_label"] or "").strip()

        add_edge(sid, p["code"], True, r["strength"], label_text, int(r["id"]))

    for r in downstream:
        sid = shadow_id(r["to_code"], r["line_id"], r["strength"], "DN")
        label_text = (r["edge_label"] or "").strip()

        add_edge(p["code"], sid, True, r["strength"], label_text, int(r["id"]))

    for r in und:
        label_text = (r["edge_label"] or "").strip()

        add_edge(r["from_code"], r["to_code"], False, r["strength"], label_text, int(r["id"]))

    return p, list(nodes_map.values()), edges
