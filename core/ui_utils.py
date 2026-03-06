def get_clicked_node(selected):
    """
    兼容 agraph 版本差异：提取点击的 node id。
    """
    if not selected:
        return None
    if isinstance(selected, str):
        return selected
    if isinstance(selected, dict):
        if selected.get("node"):
            return selected["node"]
        nodes = selected.get("nodes")
        if isinstance(nodes, list) and nodes:
            return nodes[0]
        s = selected.get("selected")
        if isinstance(s, dict):
            nodes2 = s.get("nodes")
            if isinstance(nodes2, list) and nodes2:
                return nodes2[0]
    return None
