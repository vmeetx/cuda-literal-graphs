"""Dev demo: Miku v2 walks across one box top and back, with turns (facing rules from
cgviz.miku_motion, rendering with cgviz.halfblock and cgviz.show's diff redraw).

    python tools/miku/demo_walk.py [--tired | --rest] [--cols C --rows R] [--speed 1.5]

The size defaults to the terminal's own; --speed scales the tick rate (12 ticks/s at 1).
"""
import argparse
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from cgviz import halfblock, miku_assets, miku_motion, show, term  # noqa: E402

BOX = (80, 220, 255)


def sprite_top(top, tier="full"):
    """Terminal row of the sprite's first cell, so her feet stand on the box at row `top`."""
    return top - miku_assets.tier_cells(tier)[1] + 1


def scene(cols, rows, tick, label, bg=None, top=37, tier="full"):
    """One frame: a graph box and Miku over it. `bg` is the scene background (None = the
    terminal's own). A sprite cell with a transparent half keeps the background of the cell it
    covers, never black or the terminal default. `tier` is the sprite size (miku_assets.TIERS)."""
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
        rowsg = miku_assets.load("turn_to_side", tier)["frames"][0]["grid"]   # front
    elif tick.clip == "idle_tired":
        rowsg = miku_assets.load("turn_to_front_tired", tier)["frames"][-1]["grid"]   # tired front
    else:
        rowsg = miku_assets.frame_grid(clip, tick.frame,
                                       "left" if tick.facing == "left" else "right", tier)
    rowsg = miku_assets.terminal_variant(rowsg)
    pal = miku_assets.load("walk", tier)["rgb"]
    cells = halfblock.cells(rowsg, pal)
    sx, sy = tick.x, sprite_top(top, tier)
    for j, row in enumerate(cells):
        for i, c in enumerate(row):
            if c is None:
                continue
            yy, xx = j + sy, sx + i
            if 0 <= yy < rows and 0 <= xx < cols:
                ch, fg, cbg = c
                grid[yy][xx] = (ch, fg, cbg if cbg else grid[yy][xx][2], False)
    text = f"{label}   clip: {tick.clip}   facing: {tick.facing}"
    for i, ch in enumerate(text[:max(0, cols - 3)]):
        grid[rows - 2][i + 2] = (ch, (180, 184, 190), bg, False)
    return grid


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--tired", action="store_true")
    a.add_argument("--rest", action="store_true")
    a.add_argument("--cols", type=int)
    a.add_argument("--rows", type=int)
    a.add_argument("--speed", type=float, default=1.0, help="animation speed multiplier")
    a.add_argument("--tier", choices=list(miku_assets.TIERS),
                   help="sprite size (default: the largest that fits the terminal)")
    o = a.parse_args()
    size = shutil.get_terminal_size((150, 44))
    o.cols, o.rows = o.cols or size.columns, o.rows or size.lines
    rate = 12 * max(0.1, o.speed)
    tier = o.tier or miku_assets.pick_tier(o.cols, o.rows)
    if tier is None:
        sys.exit(f"terminal {o.cols}x{o.rows} is too small for Miku "
                 f"(the smallest size needs {miku_assets.tier_cells('compact')[0] + 16}x"
                 f"{miku_assets.tier_cells('compact')[1] + 6})")
    top = o.rows - 7
    span = o.cols - miku_assets.tier_cells(tier)[0] - 8
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
    term.enable_vt(out)
    depth = term.color_depth()
    out.write("\x1b[?1049h\x1b[?25l\x1b[2J")
    restore_input = term.raw_input()
    prev = None
    t0 = time.monotonic()
    try:
        for k, t in enumerate(ticks):
            g = scene(o.cols, o.rows, t, f"{label}   [{tier}]", top=top, tier=tier)
            out.write(term.SYNC_BEGIN + show.diff(prev, g, depth) + term.SYNC_END)
            out.flush()
            prev = g
            d = t0 + (k + 1) / rate - time.monotonic()
            if d > 0:
                time.sleep(d)
        time.sleep(0.8)
    finally:
        out.write(term.SYNC_END + "\x1b[0m\x1b[?25h\x1b[?1049l")
        out.flush()
        restore_input()


if __name__ == "__main__":
    main()
