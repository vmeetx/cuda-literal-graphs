"""Design-time: draw a fixture graph and save text + PNG.  usage: graph_png.py PRESET OUT_STEM"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "spike"), str(ROOT / "tools")]

import graphdraw  # noqa: E402
import render_term  # noqa: E402

LAYER = ["Q", "K", "V", "QK", "PV", "O", "gate", "up", "down"]


def main(preset, stem, cols=100, rows=30):
    data = json.loads((ROOT / "tests/fixtures/graphs" / f"{preset}.json").read_text())
    stats = {}
    cells, nodes, cn = graphdraw.draw(data, cols, rows, roles=LAYER, stats=stats)
    pic = graphdraw.to_ansi(cells)
    lst = graphdraw.node_list(nodes, cn)
    Path(stem + ".txt").write_text(graphdraw.to_text(cells) + "\n\n" + lst + "\n", encoding="utf-8")
    render_term.render(pic, stem + ".png")
    print(graphdraw.to_text(cells))
    print(stats)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], *map(int, sys.argv[3:]))
