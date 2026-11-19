"""Dev-only: split the 3x2 pose sheet's study grid into six pose grids and measure them.

    python tools/miku/split_poses.py findings/miku_v2/study_poses

Each pose is the largest connected non-background component inside its sheet cell
(plus pieces within 3 cells of it, e.g. a leek leaf touching the edge). Prints bounding box,
width and height per pose.
"""

from __future__ import annotations

import json
import sys
from collections import deque
from pathlib import Path


def comps(grid, x0, x1, y0, y1):
    seen = set()
    out = []
    for y in range(y0, y1):
        for x in range(x0, x1):
            if grid[y][x] == "." or (x, y) in seen:
                continue
            q, c = deque([(x, y)]), []
            seen.add((x, y))
            while q:
                cx, cy = q.popleft()
                c.append((cx, cy))
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        nx, ny = cx + dx, cy + dy
                        if x0 <= nx < x1 and y0 <= ny < y1 and (nx, ny) not in seen \
                                and grid[ny][nx] != ".":
                            seen.add((nx, ny))
                            q.append((nx, ny))
            out.append(c)
    return sorted(out, key=len, reverse=True)


def main(study, out=None):
    study = Path(study)
    grid = (study / "grid.txt").read_text().split()
    h, w = len(grid), len(grid[0])
    res = {}
    for k in range(6):
        cx, cy = k % 3, k // 3
        x0, x1 = cx * w // 3, (cx + 1) * w // 3
        y0, y1 = cy * h // 2, (cy + 1) * h // 2
        cs = comps(grid, x0, x1, y0, y1)
        main_c = set(cs[0])
        xs = [p[0] for p in main_c]
        ys = [p[1] for p in main_c]
        bx0, bx1, by0, by1 = min(xs), max(xs), min(ys), max(ys)
        for c in cs[1:]:
            if len(c) >= 4 and any(bx0 - 3 <= x <= bx1 + 3 and by0 - 3 <= y <= by1 + 3 for x, y in c):
                main_c |= set(c)
        xs = [p[0] for p in main_c]
        ys = [p[1] for p in main_c]
        bx0, bx1, by0, by1 = min(xs), max(xs), min(ys), max(ys)
        rows = ["".join(grid[y][x] if (x, y) in main_c else "." for x in range(bx0, bx1 + 1))
                for y in range(by0, by1 + 1)]
        res[f"P{k + 1}"] = rows
        print(f"P{k + 1}: box x {bx0}-{bx1} y {by0}-{by1}  ->  {bx1 - bx0 + 1} x {by1 - by0 + 1}")
    if out:
        Path(out).write_text(json.dumps(res, indent=0))


if __name__ == "__main__":
    main(*sys.argv[1:])
