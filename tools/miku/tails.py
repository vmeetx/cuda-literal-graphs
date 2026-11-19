"""Dev-only: procedural twin tails (Celeste-style point chains), anchored at the hair tie.

A tail is a chain of points: point 0 is the anchor; each next point follows the previous at
a fixed segment length. Rest shape hangs down with a slight backward curve; `lag` pushes the
chain back (opposite to the walking direction) and `swing` adds a sideways sway, so the tail
trails motion by one or two ticks when the caller feeds it the previous frame's velocity.
Drawn as overlapping discs shrinking along the chain, shaded with the hair ramp (highlight
band, base, inner shadow), then outlined. Anchors and all chain points are returned so every
frame can store them as metadata.
"""

from __future__ import annotations

import math


def chain(anchor, n=17, seg=2.85, lag=0.0, swing=0.0, back=-1, curl=0.18):
    """Points of one tail. back=-1 trails to the left (she faces right)."""
    x, y = anchor
    pts = [(x, y)]
    ang = math.pi / 2 + back * (0.16 + 0.10 * lag)   # radians from +x; pi/2 = straight down
    for i in range(1, n):
        t = i / n
        a = ang - back * (curl * t) + back * 0.05 * lag * (1 - t) + swing * math.sin(t * 3.0)
        x += seg * math.cos(a)
        y += seg * math.sin(a)
        pts.append((x, y))
    return pts


def radius(i, n, r0=6.6, r1=3.0):
    t = i / max(n - 1, 1)
    bulge = math.sin(min(t * 1.6, 1.0) * math.pi / 2)        # swell just below the tie
    r = r1 + (r0 - r1) * (1 - t) * (0.75 + 0.25 * bulge)
    if t > 0.66:                                              # the tip flares out again
        r += 2.2 * math.sin((t - 0.66) / 0.34 * math.pi / 2)
    return r


def kink(i):
    """A 1 px outward step on the back edge every few points: no ruler-straight outline."""
    return 0.9 if (i // 2) % 2 else 0.0


def draw(canvas, pts, light_dir=1):
    """Discs along the chain: A base, C on the inner/back side, G highlight band near the front
    edge; then a navy outline around the whole tail. Only paints transparent pixels inside the
    tail's own mask, so call it before or after the body to set draw order."""
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
                    shade = "C" if side < -0.35 else ("G" if 0.25 < side < 0.6 and i < n - 2 else "A")
                    prev = mask.get((xx, yy))
                    if prev is None or shade == "A" or (prev == "C" and shade == "G"):
                        mask[(xx, yy)] = shade
    # split the flared tip into strands: notch the last rows
    if mask:
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
    ps = set(painted)
    for xx, yy in painted:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = xx + dx, yy + dy
            if (nx, ny) not in mask and canvas.get(nx, ny) == ".":
                canvas.set(nx, ny, "B")
    return [(round(x, 1), round(y, 1)) for x, y in pts]
