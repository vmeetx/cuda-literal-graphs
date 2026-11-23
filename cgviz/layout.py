"""Layered (Sugiyama-style) layout for small DAGs, in terminal cells.

Longest-path layers, dummy points on long edges, barycentre crossing reduction, then grid
placement with per-gap routing tracks. Standard library only.
"""

from __future__ import annotations

import unicodedata
from collections.abc import Hashable

# ---------------------------------------------------------------- layout


def layers_of(nodes, edges):
    p = {}
    for u, v in edges:
        p.setdefault(v, []).append(u)
    depth = {}
    for n in sorted(nodes):  # ids are topological
        depth[n] = max((depth[u] + 1 for u in p.get(n, ())), default=0)
    L = [[] for _ in range(max(depth.values()) + 1)]
    for n in sorted(nodes):
        L[depth[n]].append(n)
    return L, depth


def crossings(L, edges_by_layer):
    tot = 0
    for i in range(len(L) - 1):
        pos_a = {n: k for k, n in enumerate(L[i])}
        pos_b = {n: k for k, n in enumerate(L[i + 1])}
        es = [(pos_a[u], pos_b[v]) for u, v in edges_by_layer[i]]
        for a in range(len(es)):
            for b in range(a + 1, len(es)):
                if (es[a][0] - es[b][0]) * (es[a][1] - es[b][1]) < 0:
                    tot += 1
    return tot


def with_dummies(nodes, edges, depth, L):
    """Split edges longer than one layer into chains through dummy points."""
    L = [list(x) for x in L]
    seg = [[] for _ in range(len(L))]  # seg[i]: edges between layer i and i+1
    dummies = {}
    nid = -1
    chains = {}
    for u, v in sorted(edges):
        a, b = depth[u], depth[v]
        prev = u
        path = [u]
        for d in range(a + 1, b):
            dummies[nid] = d
            L[d].append(nid)
            seg[d - 1].append((prev, nid))
            path.append(nid)
            prev = nid
            nid -= 1
        seg[b - 1].append((prev, v))
        path.append(v)
        chains[(u, v)] = path
    return L, seg, dummies, chains


def reduce_crossings(L, seg, sweeps=6):
    L = [list(x) for x in L]
    best, best_c = [list(x) for x in L], crossings(L, seg)
    for it in range(sweeps):
        down = it % 2 == 0
        rng = range(1, len(L)) if down else range(len(L) - 2, -1, -1)
        for i in rng:
            ref = L[i - 1] if down else L[i + 1]
            rp = {n: k for k, n in enumerate(ref)}
            es = seg[i - 1] if down else seg[i]
            nb = {}
            for u, v in es:
                me, other = (v, u) if down else (u, v)
                nb.setdefault(me, []).append(rp[other])
            cur = {n: k for k, n in enumerate(L[i])}
            L[i].sort(key=lambda n: (sum(nb[n]) / len(nb[n]) if n in nb else cur[n], cur[n]))
        c = crossings(L, seg)
        if c < best_c:
            best, best_c = [list(x) for x in L], c
    return best, best_c


# ---------------------------------------------------------------- display width


def dwidth(s):
    w = 0
    for ch in s:
        if unicodedata.combining(ch):
            continue
        w += 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
    return w


def cut(s, width):
    if dwidth(s) <= width:
        return s
    out, w = [], 0
    for ch in s:
        cw = dwidth(ch)
        if w + cw > width - 1:
            break
        out.append(ch)
        w += cw
    return "".join(out) + "…"


# ---------------------------------------------------------------- layout


def _line_cells(a, b):
    """Cells from a to b inclusive, along one axis."""
    (x0, y0), (x1, y1) = a, b
    dx, dy = (x1 > x0) - (x1 < x0), (y1 > y0) - (y1 < y0)
    out, x, y = [(x0, y0)], x0, y0
    while (x, y) != (x1, y1):
        x, y = x + dx, y + dy
        out.append((x, y))
    return out


class Layout:
    """Holds the drawn grid plus the geometry the invariant tests check."""

    def __init__(self, orient, width, height):
        self.orient, self.width, self.height = orient, width, height
        self.boxes = {}     # node id -> (x0, y0, x1, y1) inclusive
        self.paths = []     # (u, v, [cells from first line cell to arrow cell])
        self.mask = {}      # (x, y) -> bits
        self.cells = {}     # (x, y) -> (char, rgb, bold)


def _layers(nodes, edges):
    L, depth = layers_of(nodes, edges)
    Ld, seg, dummies, chains = with_dummies(nodes, edges, depth, L)
    Ld, _ = reduce_crossings(Ld, seg)
    return Ld, seg, chains, depth


BOX = (7, 3)    # least box size (width, height) in cells; draw.layout(box=...) raises it


def plan(nodes, edges, orient, node_gap=None, rank_gap=0):
    """Grid geometry in abstract axes: a = along the flow, c = across it. rank_gap: the
    least distance between consecutive layers (room for a big sprite between them)."""
    Ld, seg, chains, depth = _layers(nodes, edges)
    node_gap = node_gap if node_gap is not None else (1 if orient == "LR" else 2)

    def size(n):  # (la, lc)
        if n < 0:
            return None
        w = max(dwidth(nodes[n]["label"]) + 4, BOX[0])  # >=7: room for a stream tag
        w += 1 - w % 2  # odd width: a single centre column, so straight edges stay straight
        h = BOX[1] + 1 - BOX[1] % 2                     # odd height: a single middle row
        return (w, h) if orient == "LR" else (h, w)

    maxla = [max((size(n)[0] for n in layer if n > 0), default=1) for layer in Ld]
    # cross positions: barycentre-guided packing, a few down/up passes
    C = {}
    lc = {n: (size(n)[1] if n > 0 else 1) for layer in Ld for n in layer}
    preds, succs = {}, {}
    for i, es in enumerate(seg):
        for u, v in es:
            preds.setdefault(v, []).append(u)
            succs.setdefault(u, []).append(v)

    def centre(n):
        return C[n] + lc[n] / 2

    def pack(layer, want):
        pos, prev = {}, None
        for n in layer:
            x = want[n] - lc[n] / 2
            if prev is not None:
                x = max(x, pos[prev] + lc[prev] + node_gap)
            pos[n] = x
            prev = n
        # centre the packed block on the mean desired centre
        shift = (sum(want.values()) / len(want)) - (
            sum(pos[n] + lc[n] / 2 for n in layer) / len(layer))
        # only shift if it doesn't break ordering constraints (it can't: uniform shift)
        return {n: pos[n] + shift for n in layer}

    for n in Ld[0]:
        pass
    C.update(pack(Ld[0], {n: 0 for n in Ld[0]}) if len(Ld[0]) == 1 else
             pack(Ld[0], {n: k * 100 for k, n in enumerate(Ld[0])}))
    for _ in range(4):
        for i in range(1, len(Ld)):
            want = {n: (sum(centre(p) for p in preds.get(n, [])) / len(preds[n]))
                    if preds.get(n) else 0 for n in Ld[i]}
            C.update(pack(Ld[i], want))
        for i in range(len(Ld) - 2, -1, -1):
            want = {n: (sum(centre(s) for s in succs.get(n, [])) / len(succs[n]))
                    if succs.get(n) else centre(n) for n in Ld[i]}
            C.update(pack(Ld[i], want))
    lo = min(C.values())
    C = {n: int(round(c + lc[n] / 2 - lo)) - lc[n] // 2 for n, c in C.items()}
    lo = min(C.values())
    C = {n: c - lo for n, c in C.items()}
    # re-pack after rounding to guarantee gaps
    for layer in Ld:
        prev = None
        for n in layer:
            if prev is not None:
                C[n] = max(C[n], C[prev] + lc[prev] + node_gap)
            prev = n
    # alignment pass: nudge each layer (by up to 2 cells) so as many ports as possible line up
    # with the ports of the previous layer; off-by-one ports make doubled junctions (┴┬)
    for i in range(1, len(Ld)):
        prev = {C[n] + lc[n] // 2 for n in Ld[i - 1]}
        best = max(range(-2, 3), key=lambda d: (
            sum((C[n] + d + lc[n] // 2) in prev for n in Ld[i]), -abs(d)))
        for n in Ld[i]:
            C[n] += best
        # per-node snap: a node fed by exactly one producer moves under that producer's port
        # when it can do so without breaking the order or the sibling gap
        for k, n in enumerate(Ld[i]):
            ps = preds.get(n, [])
            if len(ps) != 1:
                continue
            want = C[ps[0]] + lc[ps[0]] // 2 - lc[n] // 2
            lo_ok = (C[Ld[i][k - 1]] + lc[Ld[i][k - 1]] + node_gap) if k > 0 else -10**9
            hi_ok = (C[Ld[i][k + 1]] - node_gap - lc[n]) if k + 1 < len(Ld[i]) else 10**9
            if lo_ok <= want <= hi_ok:
                C[n] = want
    lo = min(C.values())
    C = {n: c - lo for n, c in C.items()}
    # tracks per gap
    gaps = []
    for i, es in enumerate(seg[:len(Ld) - 1]):
        indeg = {}
        for u, v in es:
            indeg[v] = indeg.get(v, 0) + 1
        groups = {}
        for u, v in es:
            key = ("in", v) if indeg[v] > 1 else ("out", u)
            groups.setdefault(key, []).append((u, v))
        port = {n: C[n] + lc[n] // 2 for layer in Ld for n in layer}
        ivs = []
        for key, ges in groups.items():
            cs = [port[u] for u, _ in ges] + [port[v] for _, v in ges]
            ivs.append((min(cs), max(cs), key, ges))
        ivs.sort(key=lambda t: (t[0], t[1]))
        tracks = []  # list of last end
        assign = {}
        for lo_, hi_, key, ges in ivs:
            if lo_ == hi_:
                assign[key] = (None, ges)
                continue
            for t, end in enumerate(tracks):
                if lo_ > end + 1:
                    tracks[t] = hi_
                    break
            else:
                tracks.append(hi_)
                t = len(tracks) - 1
            assign[key] = (t, ges)
        gaps.append((len(tracks), assign, port))
    A, a = [], 0
    for i in range(len(Ld)):
        A.append(a)
        a += maxla[i] + (max(gaps[i][0] + 2, rank_gap) if i < len(gaps) else 0)
    total_a = a
    total_c = max(C[n] + lc[n] for layer in Ld for n in layer)
    # with a rank gap the routing tracks sit at the far end of each gap, next to the targets,
    # so a big sprite walking a track has open space behind it instead of the source box
    return dict(Ld=Ld, seg=seg, chains=chains, C=C, lc=lc, A=A, maxla=maxla, gaps=gaps,
                size=size, total_a=total_a, total_c=total_c, late_tracks=rank_gap > 0)


def dims(p, orient):
    return (p["total_a"], p["total_c"]) if orient == "LR" else (p["total_c"], p["total_a"])


def layered_layout(g) -> dict[Hashable, tuple[float, float]]:
    """Takes: a networkx DAG.
    Gives: node -> (x, y), layered top-to-bottom by dependency depth (larger y is higher),
    deterministic (nodes sorted by id).
    Raises: ValueError if the graph has a cycle."""
    import networkx as nx

    if not nx.is_directed_acyclic_graph(g):
        raise ValueError("graph has a cycle")
    nodes = {n: None for n in sorted(g.nodes)}
    edges = set(g.edges)
    L, depth = layers_of(nodes, edges)
    pos = {}
    for d, layer in enumerate(L):
        for i, n in enumerate(layer):
            pos[n] = (float(i - (len(layer) - 1) / 2), float(len(L) - 1 - d))
    return pos
