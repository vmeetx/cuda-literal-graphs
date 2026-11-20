"""Dev demo: Miku v2 walks across one box top and back, with turns (facing rules from
cgviz.miku_motion, rendering with cgviz.halfblock and cgviz.show's diff redraw).

    python tools/miku/demo_walk.py [--tired | --rest] [--cols 150] [--rows 44]
"""
import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from cgviz import halfblock, miku_assets, miku_motion, show  # noqa: E402

BOX = (80, 220, 255)


def scene(cols, rows, tick, label, bg=None, top=37):
    """One frame: a graph box and Miku over it. `bg` is the scene background (None = the
    terminal's own). A sprite cell with a transparent half keeps the background of the cell it
    covers, never black or the terminal default."""
    blank = (" ", None, bg, False)
    grid = [[blank] * cols for _ in range(rows)]
    x0, x1 = 4, cols - 5
    for x in range(x0, x1 + 1):
        grid[top][x] = ("━", BOX, bg, False)
        grid[top + 2][x] = ("━", BOX, bg, False)
    for y, (a, b) in ((top, ("┏", "┓")), (top + 2, ("┗", "┛"))):
        grid[y][x0] = (a, BOX, bg, False)
        grid[y][x1] = (b, BOX, bg, False)
    grid[top + 1][x0] = grid[top + 1][x1] = ("┃", BOX, bg, False)
    for i, ch in enumerate(" gemm1 · out "):
        grid[top + 1][(cols - 13) // 2 + i] = (ch, (255, 255, 255), bg, True)
    clip = tick.clip
    if tick.clip == "idle":
        rowsg = miku_assets.load("turn_to_side")["frames"][0]["grid"]   # front (P1)
    elif tick.clip == "idle_tired":
        rowsg = miku_assets.load("turn_to_front_tired")["frames"][-1]["grid"]   # tired front
    else:
        rowsg = miku_assets.frame_grid(clip, tick.frame, "left" if tick.facing == "left" else "right")
    rowsg = miku_assets.terminal_variant(rowsg)
    pal = miku_assets.load("walk")["rgb"]
    cells = halfblock.cells(rowsg, pal)
    sx = tick.x
    for j, row in enumerate(cells):
        for i, c in enumerate(row):
            if c is None:
                continue
            yy, xx = j + 2, sx + i
            if 0 <= yy < rows and 0 <= xx < cols:
                ch, fg, cbg = c
                grid[yy][xx] = (ch, fg, cbg if cbg else grid[yy][xx][2], False)
    text = f"{label}   clip: {tick.clip}   facing: {tick.facing}"
    for i, ch in enumerate(text[:cols]):
        grid[rows - 2][i + 2] = (ch, (180, 184, 190), bg, False)
    return grid


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--tired", action="store_true")
    a.add_argument("--rest", action="store_true")
    a.add_argument("--cols", type=int, default=150)
    a.add_argument("--rows", type=int, default=44)
    o = a.parse_args()
    span = o.cols - 74 - 8
    if o.rest:
        moves = [("walk", 4 + span), ("stop", None), ("walk", 4), ("stop", None)]
        ticks = miku_motion.plan(moves, x0=4, idle_ticks=14, tired={0})
        label = "cheerful -> tired on the way to a rest, tired turns, rest, then walking it off"
    elif o.tired:
        moves = [("walk", 4 + span), ("stop", None)]
        ticks = miku_motion.plan(moves, x0=4, idle_ticks=10, tired={0})
        label = "walk_tired: dragging the leek before a rest"
    else:
        moves = [("walk", 4 + span), ("stop", None), ("walk", 4), ("stop", None)]
        ticks = miku_motion.plan(moves, x0=4, idle_ticks=10)
        label = "3/4 walk across one box top, both directions, with turns"
    assert not miku_motion.violations(ticks)
    out = sys.stdout
    out.write("\x1b[?1049h\x1b[?25l\x1b[2J")
    prev = None
    t0 = time.monotonic()
    try:
        for k, t in enumerate(ticks):
            g = scene(o.cols, o.rows, t, label)
            out.write(show.diff(prev, g))
            out.flush()
            prev = g
            d = t0 + (k + 1) / 12 - time.monotonic()
            if d > 0:
                time.sleep(d)
        time.sleep(0.8)
    finally:
        out.write("\x1b[0m\x1b[?25h\x1b[?1049l")
        out.flush()


if __name__ == "__main__":
    main()
