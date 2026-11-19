"""Dev-only: procedural twin tails (Celeste-style point chains), anchored at the hair tie.

A tail is a chain of points: point 0 is the anchor; each next point follows the previous at a
fixed segment length. The direction of each segment is an angle measured from straight down,
positive = toward her back (`back` = -1 when she faces right, so the tail moves to -x). The
rest shape arcs back and down from the tie (`splay` at the tie, `curl` bringing it toward
vertical); `lag` adds trailing that grows toward the tip, `swing` a small sway, so the tips
trail motion by one or two ticks when the caller feeds the previous tick's state.
Drawn as overlapping discs that taper and flare again at the tip, shaded with the hair ramp
(highlight band, base, inner shadow) or one step darker for the far tail, then outlined.
"""

from __future__ import annotations

import math


def chain(anchor, n=17, seg=2.85, lag=0.0, swing=0.0, back=-1, curl=0.8, splay=0.9):
    """Points of one tail, arcing backward and down from the anchor."""
    x, y = anchor
    pts = [(x, y)]
    for i in range(1, n):
        t = i / n
        theta = splay - curl * t + 0.18 * lag * t + swing * math.sin(t * 3.0)
        theta = max(-0.15, min(theta, 1.35))       # never forward of vertical by more than a hair
        x += back * seg * math.sin(theta)           # back=-1: toward -x (behind her)
        y += seg * math.cos(theta)                  # always downward
        pts.append((x, y))
    return pts


def radius(i, n, r0=6.0, r1=2.8):
    t = i / max(n - 1, 1)
    bulge = math.sin(min(t * 1.6, 1.0) * math.pi / 2)        # swell just below the tie
    r = r1 + (r0 - r1) * (1 - t) * (0.75 + 0.25 * bulge)
    if t > 0.66:                                              # the tip flares out a little
        r += 1.2 * math.sin((t - 0.66) / 0.34 * math.pi / 2)
    return r


def kink(i):
    """A 1 px step on the back edge every few points: no ruler-straight outline."""
    return 0.9 if (i // 2) % 2 else 0.0


NEAR_SHADES = {"hi": "G", "base": "A", "shadow": "C"}
FAR_SHADES = {"hi": "A", "base": "C", "shadow": "C"}     # one step darker on the hair ramp


def draw(canvas, pts, light_dir=1, far=False):
    """Paint the tail into transparent pixels only (so call order sets draw order), outline it,
    and return the chain points. canvas.tail_cells collects every painted cell."""
    shades = FAR_SHADES if far else NEAR_SHADES
    n = len(pts)
    mask = {}
    for i, (px, py) in enumerate(pts):
        r = radius(i, n)
        px = px - light_dir * kink(i)
        for yy in range(int(py - r) - 1, int(py + r) + 2):
            for xx in range(int(px - r) - 1, int(px + r) + 2):
                d = math.hypot(xx - px, yy - py)
                if d <= r:
                    side = (xx - px) * light_dir / max(r, 1e-6)       # -1 back .. +1 front
                    shade = (shades["shadow"] if side < -0.35 else
                             shades["hi"] if 0.25 < side < 0.6 and i < n - 2 else shades["base"])
                    prev = mask.get((xx, yy))
                    if prev is None or shade == shades["base"]:
                        mask[(xx, yy)] = shade
    if mask:   # split the flared tip into strands: notch the last rows
        bottom = max(y for _, y in mask)
        xs_b = [x for x, y in mask if y >= bottom - 4]
        if xs_b:
            lo, hi = min(xs_b), max(xs_b)
            for k in range(1, 3):
                nx = lo + (hi - lo) * k // 3
                for dy in range(0, 4 - k):
                    mask.pop((nx, bottom - dy), None)
    painted = []
    for (xx, yy), c in mask.items():
        if canvas.get(xx, yy) == ".":
            canvas.set(xx, yy, c)
            painted.append((xx, yy))
    for xx, yy in list(painted):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = xx + dx, yy + dy
            if (nx, ny) not in mask and canvas.get(nx, ny) == ".":
                canvas.set(nx, ny, "B")
                painted.append((nx, ny))
    cells = getattr(canvas, "tail_cells", set())
    cells.update(painted)
    canvas.tail_cells = cells
    return [(round(x, 1), round(y, 1)) for x, y in pts]
