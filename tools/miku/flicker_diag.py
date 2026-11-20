"""Dev-only: find where dark pixels in the hair come from, layer by layer.

    python tools/miku/flicker_diag.py [clip ...]

1. Sprite data: outline-coloured pixels (B) inside the hair region that are surrounded by hair
   colours, per frame.
2. Compositing: pixels in the head region that differ from the head layer alone (bob-shifted),
   i.e. another layer (tail, tie, leek, arm) drawn over or poking through the head.
3. Terminal variant: outline pixels whose class (inner navy B vs outer slate O) changes between
   frames once the bob is undone - a colour flip on a pixel that does not move.
4. Half-block cells: the same comparison after packing into terminal cells, so a 1 px bob that
   re-pairs top/bottom halves shows up.
"""

import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "tools/miku")]

from cgviz import halfblock, miku_assets  # noqa: E402

HAIR = set("AGC")


def hair_box(frame):
    a = frame["anchors"]
    b = a.get("bob", 0)
    x0, x1 = a.get("head_cols", [22, 53])
    return x0, x1, 0 + b, 18 + b      # crown and fringe: top of the head


def lint_inner_outline(rows, box):
    x0, x1, y0, y1 = box
    hits = []
    for y in range(max(y0, 1), min(y1, len(rows) - 1)):
        for x in range(max(x0, 1), min(x1, len(rows[0]) - 1)):
            if rows[y][x] != "B":
                continue
            nb = [rows[y + dy][x + dx] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
            if all(c in HAIR for c in nb):
                hits.append((x, y))
    return hits


def unbob(rows, bob):
    return halfblock.shift(rows, -bob) if bob else rows


def main(clips):
    for clip in clips:
        d = miku_assets.load(clip)
        frames = d["frames"]
        print(f"== {clip}")
        base = None
        flips = Counter()
        for k, f in enumerate(frames):
            rows = f["grid"]
            box = hair_box(f)
            inner = lint_inner_outline(rows, box)
            tv = miku_assets.terminal_variant(rows)
            u = unbob(tv, f["anchors"].get("bob", 0))
            x0, x1 = box[0], box[1]
            region = [r[x0:x1] for r in u[0:18]]
            if base is None:
                base = region
            diff = [(x0 + x, y, base[y][x], region[y][x]) for y in range(18)
                    for x in range(x1 - x0) if base[y][x] != region[y][x]]
            for _, _, a, b in diff:
                flips[(a, b)] += 1
            print(f"  {f['drawing']:10s} bob {f['anchors'].get('bob', 0):+d}  inner-outline {len(inner):2d}"
                  f"  head-top pixels differing from frame 0 (bob undone): {len(diff):3d} {diff[:6]}")
        print("  colour flips (frame0 -> frame):", dict(flips.most_common(8)))


if __name__ == "__main__":
    main(sys.argv[1:] or ["walk"])
