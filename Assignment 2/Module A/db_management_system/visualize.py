from graphviz import Digraph


def visualize_bplustree(root, title="B+ Tree", filename="bplustree_visual", view=True):
    """
    Visualize a B+ Tree using graphviz.Digraph.

    Requirements:
      1. Tree Structure     - hierarchy of internal and leaf nodes
      2. Node Relationships - straight parent-child arrows
      3. Leaf Node Linkage  - dashed arrows connecting leaf nodes via .next
    """

    dot = Digraph(
        comment="B+ Tree",
        graph_attr={
            "label":    title,
            "labelloc": "t",
            "fontsize": "20",
            "fontname": "Helvetica-Bold",
            "rankdir":  "TB",
            "splines":  "false",      
            "nodesep":  "1.0",        
            "ranksep":  "1.2",       
            "pad":      "0.8",
            "center":   "true",
            "bgcolor":  "white",
            "dpi":      "200",
        },
        node_attr={
            "fontname": "Helvetica",
            "fontsize": "13",
            "shape":    "none",      
            "margin":   "0",
        },
        edge_attr={
            "fontname":  "Helvetica",
            "fontsize":  "11",
            "arrowsize": "0.7",
            "penwidth":  "1.5",
        },
    )

    leaf_ids = []
    cursor = root
    while not cursor.leaf:
        cursor = cursor.children[0]
    while cursor:
        leaf_ids.append(str(id(cursor)))
        cursor = cursor.next

    #  recursive node builder 
    def add_nodes(node):
        node_id = str(id(node))
        is_root = (node is root)

        if node.leaf:
            colspan = max(len(node.keys), 1)
            key_cells = "".join(
                f"<TD WIDTH='36' HEIGHT='30' CELLPADDING='8'><FONT POINT-SIZE='13'><B>{k}</B></FONT></TD>"
                for k in node.keys
            )
            label = (
                f"<<TABLE BORDER='1' CELLBORDER='0' CELLSPACING='0' CELLPADDING='0'>"
                f"<TR><TD COLSPAN='{colspan}' CELLPADDING='4' BGCOLOR='#F0F0F0'>"
                f"<FONT POINT-SIZE='10'><B>LEAF</B></FONT></TD></TR>"
                f"<TR>{key_cells}</TR>"
                f"</TABLE>>"
            )
            dot.node(node_id, label=label)

        else:
            header  = "ROOT" if is_root else "INTERNAL"
            colspan = max(len(node.keys), 1)
            key_cells = "".join(
                f"<TD WIDTH='36' HEIGHT='30' CELLPADDING='8'><FONT POINT-SIZE='13'><B>{k}</B></FONT></TD>"
                for k in node.keys
            )
            label = (
                f"<<TABLE BORDER='1' CELLBORDER='0' CELLSPACING='0' CELLPADDING='0'>"
                f"<TR><TD COLSPAN='{colspan}' CELLPADDING='4' BGCOLOR='#F0F0F0'>"
                f"<FONT POINT-SIZE='10'><B>{header}</B></FONT></TD></TR>"
                f"<TR>{key_cells}</TR>"
                f"</TABLE>>"
            )
            dot.node(node_id, label=label)

            
            for child in node.children:
                child_id = str(id(child))
                add_nodes(child)
                dot.edge(
                    node_id,
                    child_id,
                    arrowhead="normal",
                    color="#222222",
                )

    add_nodes(root)

    for i in range(len(leaf_ids) - 1):
        dot.edge(
            leaf_ids[i],
            leaf_ids[i + 1],
            style="dashed",
            arrowhead="open",
            color="#999999",
            penwidth="1.2",
            constraint="false",
            label="  next" if i == 0 else "",
            fontcolor="#999999",
        )

    dot.render(filename, format="png", view=view, cleanup=True)
    print(f"[visualize] saved -> {filename}.png")
    return dot


# ── smoke test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.dirname(__file__))
    from database.bplustree import BPlusTree

    tree = BPlusTree(order=4)
    for key in [10, 20, 5, 6, 12, 30, 7, 17, 25, 3, 15, 22]:
        tree.insert(key)

    visualize_bplustree(
        tree.root,
        title="B+ Tree  |  order = 4",
        filename="sample_bplustree",
    )