"""Dev-only: the compact tier is the approved Miku at half size (37 x 36 px, 18 terminal rows),
so she looks the same at every size. Each approved drawing is rendered with even-pixel offsets
(q_walk even=True), reduced 2:1, then cleaned by hand-set rules:

- a 2x2 block keeps its most common colour; outline wins where a line crosses the block, so
  lines survive; it is transparent only when mostly empty;
- the outer silhouette is closed with outline;
- lone pixels (no same-colour neighbour, inside a solid area) take their surroundings' colour;
- the eyes are replaced with hand-drawn half-size eyes for each face (open, "^ ^", half-lidded,
  closed line), placed from the head's position.
"""

from __future__ import annotations

from collections import Counter

W, H, BASELINE = 37, 36, 33
KEEP = set("bIXSVUZ")      # small accents a fill vote must not wipe out


def half(rows):
    out = []
    for y in range(0, len(rows) - 1, 2):
        s = []
        for x in range(0, len(rows[0]) - 1, 2):
            px = [rows[y + j][x + i] for j in (0, 1) for i in (0, 1)]
            c = Counter(px)
            empty = c.pop(".", 0)
            if empty >= 3 or not c:
                s.append(".")
                continue
            b = c.get("B", 0) + c.get("O", 0)
            acc = [p for p in px if p in KEEP and p != "Z"]
            leek = [p for p in px if p in "bIX"]
            if len(leek) >= 2 or (leek and b <= 2 and empty == 0):
                s.append(Counter(leek).most_common(1)[0][0])   # the thin leek survives
            elif b >= 2 or (b == 1 and empty >= 1):
                s.append("B")
            elif acc and Counter(acc).most_common(1)[0][1] >= 2:
                s.append(Counter(acc).most_common(1)[0][0])
            else:
                c.pop("B", None)
                s.append(c.most_common(1)[0][0] if c else "B")
        out.append(s)
    return out


def close_outline(g):
    """A coloured pixel on the silhouette edge (touching transparency) becomes outline, except
    thin accents (leek, ground shadow) that would vanish."""
    h, w = len(g), len(g[0])
    edge = []
    for y in range(h):
        for x in range(w):
            c = g[y][x]
            if c in ".BZ" or c in "bIX":
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                xx, yy = x + dx, y + dy
                if not (0 <= xx < w and 0 <= yy < h) or g[yy][xx] == ".":
                    edge.append((x, y))
                    break
    # only close where the outline is actually broken: a fill pixel touching transparency
    # whose diagonal neighbours outside are not already outline
    for x, y in edge:
        g[y][x] = "B"


def despeckle(g):
    h, w = len(g), len(g[0])
    src = [r[:] for r in g]
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            c = src[y][x]
            if c in ".BZ" or c in KEEP:
                continue
            nb = [src[y + dy][x + dx] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
            if c in nb or "." in nb:
                continue
            m = Counter(n for n in nb if n != "B").most_common(1)
            if m and m[0][1] >= 3:
                g[y][x] = m[0][0]


# hand-drawn half-size eyes, placed at each eye's top-left; '.' is skin, ' ' keeps what's there.
# 3/4 view: the near eye is wide, the far eye narrower toward the far cheek.
EYES = {
    "open":       [["BBB", "FCG", "CAC"], ["BBB", "FCG", "CAC"]],      # front view
    "line_front": [["...", "BBB", "..."], ["...", "BBB", "..."]],
    "cheery":     [[".BBB.", "B...B"], [".B.", "B.B"]],
    "half":       [["BBBBB", ".FCF."], ["BBB", "FCF"]],
    "line":       [[".....", "BBBBB"], ["...", "BBB"]],
}
FRONT_EYES = [(13, 10), (21, 10)]
DIAG_EYES = [(14, 10), (22, 10)]         # with the head at its rest position


def put(g, x0, y0, rows):
    for j, r in enumerate(rows):
        for i, c in enumerate(r):
            if c != " " and 0 <= y0 + j < len(g) and 0 <= x0 + i < len(g[0]):
                g[y0 + j][x0 + i] = "E" if c == "." else c


def eyes_for(meta):
    """(face, eye spots) for a full-size drawing's metadata."""
    if meta.get("view") == "front":
        return ("line_front" if meta.get("drawing") == "front_tired" else "open"), FRONT_EYES
    dx = (meta["head_cols"][0] - 26) // 2
    dy = (meta["bob"] + meta["head_dy"]) // 2
    return meta["face"], [(x + dx, y + dy) for x, y in DIAG_EYES]


def compact(full_rows, eyes=None):
    """eyes = (face, [(x, y) of each eye's top-left in compact pixels]) or None."""
    g = half(full_rows)
    despeckle(g)
    close_outline(g)
    if eyes:
        face, spots = eyes
        for (x, y), rows in zip(spots, EYES[face]):
            put(g, x, y, rows)
    return ["".join(r) for r in g]


def clip_frames(name):
    """A compact clip from the same exposure sheet and drawings as the full one."""
    import q_walk
    import xsheet

    xs = xsheet.load(name)
    order = [f["drawing"] for f in xs["frames"]]
    out, t = [], 0
    for k, f in enumerate(xs["frames"]):
        d, u = f["drawing"], f.get("u", 0.0)
        if d == "front":
            rows, meta = q_walk.p1(), {"view": "front", "facing": "front", "drawing": d}
        elif d == "front_tired":
            rows, meta = q_walk.tired_front(), {"view": "front", "facing": "front", "drawing": d}
        elif d.startswith("stand"):
            rows, meta = q_walk.pose(d, u=u, even=True)
        else:
            hem = q_walk.hem_for(order, k, 1 if u < 0.5 else 2)
            rows, meta = q_walk.pose(d, t, xs["ticks"], u=u, hem=hem, k=k, even=True)
        small = compact(rows, eyes_for(meta))
        meta = dict(meta, tier="compact")
        if "hem_outline" in meta:
            meta["hem_outline"] = [[x // 2, y // 2] for x, y in meta["hem_outline"]]
        out.append({"drawing": d, "ticks": f["ticks"], "key": f.get("key", False),
                    "grid": small, "anchors": meta})
        t += f["ticks"]
    return xs, out
