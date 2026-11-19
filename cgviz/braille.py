"""Legacy braille drawer (spike v2), kept for comparison and its golden tests.
Standard library only."""

from __future__ import annotations

from cgviz.graphdata import SMALL, collapse, load, succ  # noqa: F401
from cgviz.layout import crossings, layers_of, reduce_crossings, with_dummies

# ---------------------------------------------------------------- braille raster

BR = [[0x01, 0x08], [0x02, 0x10], [0x04, 0x20], [0x40, 0x80]]


class Raster:
    def __init__(self, cols, rows):
        self.cols, self.rows = cols, rows
        self.bits = [[0] * cols for _ in range(rows)]
        self.col = [[None] * cols for _ in range(rows)]
        self.text = [[None] * cols for _ in range(rows)]

    def dot(self, x, y, rgb):
        cx, cy = x // 2, y // 4
        if 0 <= cx < self.cols and 0 <= cy < self.rows and x >= 0 and y >= 0:
            self.bits[cy][cx] |= BR[y % 4][x % 2]
            self.col[cy][cx] = rgb

    def hline(self, x0, x1, y, rgb, dash=False):
        for x in range(min(x0, x1), max(x0, x1) + 1):
            if not dash or x % 2 == 0 or x == max(x0, x1):
                self.dot(x, y, rgb)

    def vline(self, x, y0, y1, rgb, dash=False):
        for y in range(min(y0, y1), max(y0, y1) + 1):
            if not dash or y % 2 == 0 or y == max(y0, y1):
                self.dot(x, y, rgb)

    def put(self, cx, cy, s, rgb, only_blank=False):
        for i, ch in enumerate(s):
            x = cx + i
            if 0 <= x < self.cols and 0 <= cy < self.rows:
                if only_blank and (self.bits[cy][x] or self.text[cy][x]):
                    return False
        for i, ch in enumerate(s):
            x = cx + i
            if 0 <= x < self.cols and 0 <= cy < self.rows:
                self.text[cy][x] = ch
                self.bits[cy][x] = 0
                self.col[cy][x] = rgb
        return True

    def cells(self):
        out = []
        for y in range(self.rows):
            row = []
            for x in range(self.cols):
                t = self.text[y][x]
                if t is not None:
                    row.append((t, self.col[y][x]))
                elif self.bits[y][x]:
                    row.append((chr(0x2800 + self.bits[y][x]), self.col[y][x]))
                else:
                    row.append((" ", None))
            out.append(row)
        return out


# ---------------------------------------------------------------- draw

COL = {"kernel": (80, 220, 230), "gemm": (80, 220, 230), "mem": (240, 200, 80),
       "event": (230, 110, 220), "other": (200, 200, 200), "edge": (130, 140, 150),
       "lane": (150, 230, 140), "link": (240, 160, 90), "dim": (150, 150, 150)}

BOX_H = 3   # rows per box (top border, label, bottom border)
GAP = 1     # rows between layers


def split_columns(L, per_col, nodes):
    """Break layers into screen columns, preferring breaks just after 1-wide layers."""
    n = len(L)
    ncol = max(1, -(-n // per_col))
    target = -(-n // ncol)
    cuts, start = [], 0
    while n - start > per_col:
        best = None
        for k in range(start + max(2, target - 2), min(start + per_col, n - 1) + 1):
            real = [x for x in L[k - 1] if x > 0]
            score = (len(L[k - 1]) != 1, abs(k - start - target))
            if real and (best is None or score < best[0]):
                best = (score, k)
        k = best[1] if best else start + per_col
        cuts.append(k)
        start = k
    bounds = [0] + cuts + [n]
    return [(bounds[i], bounds[i + 1]) for i in range(len(bounds) - 1)]


ALL = frozenset({"xred", "kinds", "labels", "lanes", "legend"})


def render(nodes, edges, cols=100, rows=29, stats=None, feat=ALL):
    L, depth = layers_of(nodes, edges)
    if stats is not None:
        seg0 = [[] for _ in L]
        Ld, seg0, _, _ = with_dummies(nodes, edges, depth, L)
        stats["crossings_before"] = crossings(Ld, seg0)
    per_col = max(1, (rows - 1) // (BOX_H + GAP))
    colspans = split_columns(L, per_col, nodes)
    colw = cols // len(colspans)
    colof = {}
    for ci, (a, b) in enumerate(colspans):
        for d in range(a, b):
            for n in L[d]:
                colof[n] = ci
    # edges crossing a screen column become off-column links (letters)
    local = {(u, v) for u, v in edges if colof[u] == colof[v]}
    links = sorted(edges - local, key=lambda e: (e[0], e[1]))
    Ld, seg, dummies, chains = with_dummies(nodes, local, depth, L)
    Ld, cr = reduce_crossings(Ld, seg) if "xred" in feat else (Ld, crossings(Ld, seg))
    if stats is not None:
        stats["crossings_after"] = cr
        stats["columns"] = len(colspans)
    # place: slot centres in braille dots
    pos = {}
    widest = {ci: max(len(Ld[d]) for d in range(a, b)) for ci, (a, b) in enumerate(colspans)}
    for ci, (a, b) in enumerate(colspans):
        pitch = colw // max(widest[ci], 1)
        need = 4 + max(len(nodes[n]["label"]) if "labels" in feat else 3
                       for d in range(a, b) for n in Ld[d] if n > 0)
        bw = max(5, min(pitch - 2, need, 14))
        for d in range(a, b):
            row = 1 + (d - a) * (BOX_H + GAP)
            m = len(Ld[d])
            for k, n in enumerate(Ld[d]):
                cx = ci * colw + colw // 2 + int(round((k - (m - 1) / 2) * pitch))
                pos[n] = (cx, row, bw)
    R = Raster(cols, rows)

    def top_y(n):
        return pos[n][1] * 4 + 1

    def bot_y(n):
        return (pos[n][1] + BOX_H - 1) * 4 + 2

    def xdot(n):
        return pos[n][0] * 2

    ec = COL["edge"]
    for (u, v), path in sorted(chains.items()):
        for a, b in zip(path, path[1:]):
            xa, xb = xdot(a), xdot(b)
            ya = bot_y(a) if a > 0 else top_y(a)
            if a < 0:
                ya = top_y(a)
            yb = top_y(b)
            if a < 0:  # dummy: straight vertical through its layer
                R.vline(xa, top_y(a), bot_y(a), ec)
                ya = bot_y(a)
            mid = ya + 2
            R.vline(xa, ya + 1, mid, ec)
            R.hline(xa, xb, mid, ec)
            R.vline(xb, mid, yb - 1, ec)
            if b > 0:  # arrowhead
                for k in (1, 2):
                    R.dot(xb - k, yb - 1 - k, ec)
                    R.dot(xb + k, yb - 1 - k, ec)
        if path[-2] < 0:
            pass
    for n, (cx, row, bw) in pos.items():
        if n < 0:
            continue
        nd = nodes[n]
        c = COL.get(nd["kind"], COL["other"]) if "kinds" in feat else COL["other"]
        x0, x1 = (cx - bw // 2) * 2, (cx - bw // 2 + bw - 1) * 2 + 1
        y0, y1 = top_y(n), bot_y(n)
        if nd["kind"] == "event":
            R.put(cx, row + 1, "◆", c)
        else:
            dash = nd["kind"] == "mem" and "kinds" in feat
            R.hline(x0, x1, y0, c, dash)
            R.hline(x0, x1, y1, c, dash)
            R.vline(x0, y0, y1, c, dash)
            R.vline(x1, y0, y1, c, dash)
        lab = nd["label"] if "labels" in feat else str(n)
        inner = bw - 2
        if len(lab) > inner:
            lab = str(n) if len(str(n)) <= inner else lab[:inner]
        R.put(cx - bw // 2 + 1 + (inner - len(lab)) // 2, row + 1, lab,
              (255, 255, 255) if nd["op"] in ("gemm", "splitK") else (170, 180, 185))
    # stream lanes: label branches of each fork s1, s2, s3 in the gap above each child
    s = succ(edges)

    def first_hop(u, v):
        return chains[(u, v)][1] if (u, v) in chains else v

    for u in (sorted(nodes) if "lanes" in feat else ()):
        ks = sorted(s.get(u, ()), key=lambda v: pos[first_hop(u, v)][0])
        if len(ks) < 2:
            continue
        for i, v in enumerate(ks):
            first = first_hop(u, v)
            if first < 0:
                continue
            cx, row, bw = pos[first]
            R.put(cx - bw // 2 + 1, row, f"s{i + 1}", COL["lane"])  # tag in the top border
    # off-column links
    srcs = sorted({u for u, _ in links})
    for u, v in links:
        tag = chr(ord("A") + srcs.index(u))
        cu, ru, bwu = pos[u]
        cv, rv, bwv = pos[v]
        R.vline(xdot(u), bot_y(u) + 1, bot_y(u) + 2, COL["link"])
        R.put(cu + 1, ru + BOX_H, f"{tag}", COL["link"])
        R.put(cv - 1, rv - 1, f"{tag}", COL["link"])
        R.vline(xdot(v), top_y(v) - 3, top_y(v) - 1, COL["link"])
        R.dot(xdot(v) - 1, top_y(v) - 2, COL["link"])
        R.dot(xdot(v) + 1, top_y(v) - 2, COL["link"])
    return R.cells()


LEGEND = [("▭", "kernel", "kernel"), ("┄", "memset/memcpy", "mem"), ("◆", "event", "event"),
          ("sN", "stream branch", "lane"), ("A", "link across columns", "link")]


def legend_cells(width, present=None):
    row = []
    for sym, txt, k in LEGEND:
        if present is not None and k not in present:
            continue
        for ch in sym:
            row.append((ch, COL[k]))
        for ch in " " + txt + "   ":
            row.append((ch, COL["dim"]))
    row = row[:width]
    return row + [(" ", None)] * (width - len(row))


def draw(data, cols=100, rows=30, roles=None, stats=None, feat=ALL):
    nodes, edges = load(data, roles)
    cn, ce = collapse(nodes, edges)
    cells = render(cn, ce, cols, rows - 1, stats, feat)
    while cells and all(ch == " " for ch, _ in cells[-1]):
        cells.pop()
    if "legend" in feat:
        present = {nd["kind"] for nd in cn.values()} | {"lane", "link"}
        cells.append(legend_cells(cols, present))
    return cells, nodes, cn


def to_text(cells):
    return "\n".join("".join(ch for ch, _ in row).rstrip() for row in cells)


def to_ansi(cells):
    out = []
    for row in cells:
        s, cur = [], None
        for ch, c in row:
            if c != cur:
                s.append("\x1b[0m" if c is None else "\x1b[38;2;%d;%d;%dm" % c)
                cur = c
            s.append(ch)
        out.append("".join(s).rstrip() + "\x1b[0m")
    return "\n".join(out)


def node_list(nodes, cn):
    lab = {}
    for r, nd in cn.items():
        for m in nd["members"]:
            lab[m] = nd["label"]
    w = max(len(v) for v in lab.values())
    return "\n".join(f"{n:>3}  {lab[n]:<{w}}  {nodes[n]['kind']:<6}  {nodes[n]['full']}"
                     for n in sorted(nodes))
