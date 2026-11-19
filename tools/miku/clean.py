"""Dev-only: turn the raw study grid into the cleaned front idle frame.

Automatic steps (hand corrections are applied afterwards, in fix_front.py):
1. Background = '.' cells connected to the image border (4-neighbour flood fill).
   Any other '.' cell is enclosed by her outline: it is the white top / eye white -> 'W'.
2. Drop detached components that aren't part of her (the stray squares and the bar).
3. Crop to her bounding box (shadow included) with a 1-cell margin.
"""

from __future__ import annotations

import json
import sys
from collections import deque
from pathlib import Path


def components(grid):
    h, w = len(grid), len(grid[0])
    seen = [[False] * w for _ in range(h)]
    comps = []
    for y in range(h):
        for x in range(w):
            if grid[y][x] == "." or seen[y][x]:
                continue
            q, comp = deque([(x, y)]), []
            seen[y][x] = True
            while q:
                cx, cy = q.popleft()
                comp.append((cx, cy))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < w and 0 <= ny < h and not seen[ny][nx] and grid[ny][nx] != ".":
                        seen[ny][nx] = True
                        q.append((nx, ny))
            comps.append(comp)
    return comps


def main(study_dir, out_dir):
    study, out = Path(study_dir), Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    grid = [list(r) for r in (study / "grid.txt").read_text().split()]
    pal = {k: v["hex"] for k, v in json.loads((study / "palette.json").read_text()).items()}
    h, w = len(grid), len(grid[0])
    # 1. background flood fill from the border
    bg = [[False] * w for _ in range(h)]
    q = deque((x, y) for y in range(h) for x in range(w)
              if (x in (0, w - 1) or y in (0, h - 1)) and grid[y][x] == ".")
    for x, y in q:
        bg[y][x] = True
    while q:
        cx, cy = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < w and 0 <= ny < h and not bg[ny][nx] and grid[ny][nx] == ".":
                bg[ny][nx] = True
                q.append((nx, ny))
    # enclosed pockets: small ones are whites inside her (eyes, top); big ones are background
    # gaps closed off by a tail or the leek
    pockets = [c for c in components([["x" if (grid[y][x] == "." and not bg[y][x]) else "."
                                       for x in range(w)] for y in range(h)])]
    enclosed = 0
    for c in pockets:
        if len(c) < 30:
            for x, y in c:
                grid[y][x] = "W"
                enclosed += len(c) and 1
    # 2. keep the big components (her body and her ground shadow)
    comps = sorted(components(grid), key=len, reverse=True)
    keep = [c for c in comps if len(c) >= 40]
    dropped = [c for c in comps if len(c) < 40]
    kept = {p for c in keep for p in c}
    for c in dropped:
        for x, y in c:
            grid[y][x] = "."
    # 3. crop
    xs = [x for x, _ in kept]
    ys = [y for _, y in kept]
    x0, x1, y0, y1 = min(xs) - 1, max(xs) + 1, min(ys) - 1, max(ys) + 1
    rows = ["".join(grid[y][x0:x1 + 1]) for y in range(y0, y1 + 1)]
    pal["W"] = "#f4f7f9"
    (out / "front_auto.txt").write_text("\n".join(rows) + "\n")
    (out / "palette_auto.json").write_text(json.dumps(pal, indent=1))
    print(f"enclosed whites {enclosed}, dropped {len(dropped)} components "
          f"({sum(map(len, dropped))} cells), crop x {x0}-{x1} y {y0}-{y1} "
          f"-> {len(rows[0])} x {len(rows)}")
    for i, r in enumerate(rows):
        print(f"{i:2d} {r}")


if __name__ == "__main__":
    main(*sys.argv[1:])
