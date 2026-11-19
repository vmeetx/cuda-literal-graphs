"""Design-time: render decode/prefill at every improvement stage into findings/graph_before_after/."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "spike"), str(ROOT / "tools")]

import graphdraw as gd  # noqa: E402
import render_term  # noqa: E402

OUT = ROOT / "findings/graph_before_after"
ROLES = ["Q", "K", "V", "QK", "PV", "O", "gate", "up", "down"]
STAGES = [
    ("2_layout", {"xred"}),
    ("3_kinds", {"xred", "kinds"}),
    ("4_labels", {"xred", "kinds", "labels"}),
    ("5_lanes", {"xred", "kinds", "labels", "lanes"}),
    ("6_legend", set(gd.ALL)),
]


def stage1(data):
    """Old lab.draw, fed the graph after the new collapse rule (needs networkx + plotille)."""
    import networkx as nx
    import lab
    nodes, edges = gd.load(data, ROLES)
    cn, ce = gd.collapse(nodes, edges)
    g = nx.DiGraph()
    g.add_nodes_from(cn)
    g.add_edges_from(ce)
    pic, _ = lab.draw(g, cols=100, rows=30, thick=2, collapse=False)
    return lab.trim(pic)


def main():
    for p in ("decode", "prefill"):
        data = json.loads((ROOT / "tests/fixtures/graphs" / f"{p}.json").read_text())
        try:
            t = stage1(data)
            (OUT / f"{p}_1_collapse.txt").write_text(t + "\n", encoding="utf-8")
            render_term.render(t, str(OUT / f"{p}_1_collapse.png"))
        except Exception as e:  # torch import etc.
            print("stage1 skipped:", e)
        for name, feat in STAGES:
            st = {}
            cells, nodes, cn = gd.draw(data, 100, 30, roles=ROLES, stats=st, feat=frozenset(feat))
            (OUT / f"{p}_{name}.txt").write_text(gd.to_text(cells) + "\n", encoding="utf-8")
            render_term.render(gd.to_ansi(cells), str(OUT / f"{p}_{name}.png"))
            print(p, name, st)


if __name__ == "__main__":
    main()
