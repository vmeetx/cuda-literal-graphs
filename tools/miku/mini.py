"""Dev-only: the mini tier is the approved compact Miku halved again (18 x 18 px, 9 terminal
rows, about two graph boxes), by the same method that made compact from full:

- even offsets: each compact drawing's body bob is undone before halving, so every drawing
  halves on the same pixel pairs and the head doesn't shimmer (the feet stay in the same mini
  row: compact rows 32-33 are one mini row);
- halving by vote (halve.half): a 2x2 block keeps its most common colour, outline wins where a
  line crosses it, the thin leek survives;
- lone specks removed and the silhouette closed with outline (halve.despeckle, close_outline);
- hand-set fixes after halving (see FIXES), reviewed at a gate.

    python tools/miku/mini.py            # writes cgviz/assets/miku/mini/*.json
    python tools/miku/mini.py --show     # prints every drawing instead
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import halve  # noqa: E402

SRC = HERE.parents[1] / "cgviz/assets/miku/compact"
OUT = HERE.parents[1] / "cgviz/assets/miku/mini"


def rest(rows, cb):
    """Undo a downward body bob of cb compact pixels."""
    w = len(rows[0])
    return list(rows[cb:]) + ["." * w] * cb if cb > 0 else list(rows)


def fixes(g, meta):
    """Hand-set fixes after halving."""
    return g


def mini(rows, meta):
    cb = max(0, meta.get("bob", 0) // 2)
    g = halve.half(rest(rows, cb))
    halve.despeckle(g)
    halve.close_outline(g)
    g = fixes(g, meta)
    return ["".join(r) for r in g]


def build(show=False):
    OUT.mkdir(exist_ok=True)
    for src in sorted(SRC.glob("*.json")):
        d = json.loads(src.read_text(encoding="utf-8"))
        for f in d["frames"]:
            a = f["anchors"]
            f["grid"] = mini(f["grid"], a)
            f["anchors"] = dict(a, tier="mini")
            if "hem_outline" in a:
                f["anchors"]["hem_outline"] = [[x // 2, y // 2] for x, y in a["hem_outline"]]
        d["baseline"] = d["baseline"] // 2
        if show:
            print(f"== {d['clip']}")
            for k in range(len(d["frames"][0]["grid"])):
                print("  ".join(f["grid"][k] for f in d["frames"]))
        else:
            (OUT / src.name).write_text(json.dumps(d, indent=1), encoding="utf-8")


if __name__ == "__main__":
    build(show="--show" in sys.argv)
