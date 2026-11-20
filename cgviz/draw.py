"""Draw a laid-out CUDA graph with Unicode box-drawing tiles. Standard library only.

Tile set (the style anchor, see findings/graph_fix/style_sheet.png on the spike branch):
  GEMM-type kernel   heavy box  ┏━┓┃┗━┛   strong cyan, bold label
  other kernel       light box  ┌─┐│└─┘   muted grey-teal
  memset/memcpy      dashed     ╭┄╮┆╰┄╯   amber
  event              dashed     ╭┄╮┆╰┄╯   magenta
  edges              ─ │ ┌ ┐ └ ┘ ├ ┤ ┬ ┴ ┼ by 4-bit N/E/S/W mask, arrowheads ▶ ▼
"""

from __future__ import annotations

import re
from collections.abc import Hashable

from cgviz import graphdata as gd
from cgviz.layout import Layout, cut, dims, dwidth, plan

# ---------------------------------------------------------------- tiles

N, E, S, W = 1, 2, 4, 8
LINE = {0: " ", N: "╵", E: "╶", S: "╷", W: "╴", N | S: "│", E | W: "─", E | S: "┌", S | W: "┐",
        N | E: "└", N | W: "┘", N | E | S: "├", N | S | W: "┤", E | S | W: "┬", N | E | W: "┴",
        N | E | S | W: "┼"}
GLYPH_MASK = {v: k for k, v in LINE.items()}
ARROW = {"LR": "▶", "TB": "▼"}

BOX = {  # tl, tr, bl, br, horizontal, vertical, tee-out-right, tee-out-bottom
    "heavy": ("┏", "┓", "┗", "┛", "━", "┃", "┠", "┯"),
    "light": ("┌", "┐", "└", "┘", "─", "│", "├", "┬"),
    "round": ("╭", "╮", "╰", "╯", "┄", "┆", "├", "┬"),
}
COL = {"gemm": (80, 220, 255), "kernel": (150, 190, 196), "mem": (235, 185, 70),
       "event": (220, 110, 220), "edge": (112, 116, 128), "arrow": (210, 214, 222),
       "lane": (140, 225, 120), "dim": (140, 144, 150), "text": (225, 228, 232),
       "gemm_text": (255, 255, 255)}


def style_of(nd):
    if nd["kind"] in ("mem", "event"):
        return "round", COL[nd["kind"]]
    if nd["op"] in ("gemm", "splitK"):
        return "heavy", COL["gemm"]
    return "light", COL["kernel"]


# ---------------------------------------------------------------- labels

FAMILY = [("splitK", re.compile(r"splitkreduce", re.I)), ("gemv", re.compile(r"gemv", re.I)),
          ("gemm", re.compile(r"gemm", re.I)), ("softmax", re.compile(r"softmax", re.I)),
          ("cat", re.compile(r"catarray", re.I)), ("reduce", re.compile(r"reduce_kernel", re.I)),
          ("copy", re.compile(r"copy", re.I))]


def family(raw):
    for name, pat in FAMILY:
        if pat.search(raw or ""):
            return name
    return "ew"


def label_nodes(nodes, cn, roles):
    """Label pipeline: (1) preset table for GEMMs, (2) family classifier, (3) runs = family xN."""
    out = {}
    gi = 0
    for r in sorted(cn):
        nd = cn[r]
        if len(nd["members"]) > 1:
            ops = {nodes[m]["op"] for m in nd["members"]}
            fam = next((w for w in ("norm", "silu", "gelu") if w in ops), "ew")
            lab = f"{fam} x{len(nd['members'])}"
        elif nd["kind"] == "mem":
            lab = "memset" if "memset" in nd["full"].lower() else "memcpy"
        elif nd["kind"] == "event":
            lab = "event"
        elif nd["op"] == "gemm":
            lab = roles[gi] if roles and gi < len(roles) else family(nd["full"])
            gi += 1
        else:
            fam = family(nd["full"])
            lab = {"ew": nd["op"] if nd["op"] in gd.SMALL else "ew"}.get(fam, fam)
        nd["label"] = lab
        out[r] = lab
    return out


GENERIC = ("Kernel2", "Kernel", "kernel", "device_kernel")


def short_name(full):
    """Demangled name minus return type, template arguments, lambdas and parameters,
    plus the op it applies (e.g. 'vectorized_elementwise_kernel [add]')."""
    s = re.sub(r"^(void|std::enable_if<.*?>::type)\s+", "", full)
    s = s.replace("(anonymous namespace)", "anon")
    flat = gd_strip(s).split("(")[0].strip()
    parts = flat.split("::")
    base = parts[-1] or flat
    if base in GENERIC:
        mm = re.match(r"[\w:]+?<(\w+)", s)
        if mm and mm.group(1) not in ("int", "float", "void", "unsigned", "bool", "long"):
            return mm.group(1)
        return "::".join(parts[-2:]) if len(parts) > 1 else base
    if "elementwise" in base or base == "reduce_kernel":
        hint = op_hint(s)
        if hint:
            return f"{base} [{hint}]"
    return base


def op_hint(s):
    """The operation an ATen elementwise/reduce kernel applies, from its template arguments."""
    m = re.search(r"CUDAFunctor(?:OnSelf)?_([a-z0-9]+)", s)
    if m:
        return m.group(1)
    m = re.search(r"([A-Z][a-z]+)CUDAKernelImpl", s)
    if m:
        return m.group(1).lower()
    m = re.search(r"([a-z0-9]+(?:_[a-z0-9]+)*?)_kernel(?:_cuda|_impl)", s)
    if m and m.group(1) != "gpu":
        return m.group(1)
    m = re.search(r"launch_([a-z0-9]+(?:_[a-z0-9]+)*?)_scalar", s)
    if m:
        return m.group(1)
    for m in re.finditer(r"::([A-Za-z0-9]+)(?:Functor|Ops)[<:]", s):
        if m.group(1) not in ("Binary", "AUnary", "Unary"):
            return m.group(1).lower()
    m = re.search(r"internal::([A-Za-z]+)Functor<", s)
    return m.group(1).lower() if m else ""


def gd_strip(s):
    out, depth = [], 0
    for ch in s:
        if ch in "<{":
            depth += 1
        elif ch in ">}":
            depth = max(depth - 1, 0)
        elif depth == 0:
            out.append(ch)
    return "".join(out)


def draw_plan(nodes, p, orient):
    Wd, Ht = dims(p, orient)
    lay = Layout(orient, Wd, Ht)

    def phys(a, c):
        return (a, c) if orient == "LR" else (c, a)

    def bit_toward(d_a, d_c):
        if orient == "LR":
            return {(1, 0): E, (-1, 0): W, (0, 1): S, (0, -1): N}[(d_a, d_c)]
        return {(1, 0): S, (-1, 0): N, (0, 1): E, (0, -1): W}[(d_a, d_c)]

    def seg_line(a0, c0, a1, c1, cells):
        """Axis-aligned run in abstract coords; sets connection bits on every cell."""
        da = (a1 > a0) - (a1 < a0)
        dc = (c1 > c0) - (c1 < c0)
        a, c = a0, c0
        while True:
            cells.append(phys(a, c))
            if (a, c) == (a1, c1):
                break
            na, nc = a + da, c + dc
            lay.mask[phys(a, c)] = lay.mask.get(phys(a, c), 0) | bit_toward(da, dc)
            lay.mask[phys(na, nc)] = lay.mask.get(phys(na, nc), 0) | bit_toward(-da, -dc)
            a, c = na, nc

    Ld, C, lc, A, maxla = p["Ld"], p["C"], p["lc"], p["A"], p["maxla"]
    layer_of = {n: i for i, layer in enumerate(Ld) for n in layer}
    port = p["gaps"][0][2] if p["gaps"] else {n: C[n] + lc[n] // 2 for n in Ld[0]}
    port = {n: C[n] + lc[n] // 2 for layer in Ld for n in layer}
    arrows, tees = [], []
    # dummy bodies
    body = {}
    for n, i in layer_of.items():
        if n < 0:
            cells = []
            seg_line(A[i], port[n], A[i] + maxla[i] - 1, port[n], cells)
            body[n] = cells
    # segments in each gap
    seg_paths = {}
    for i, (T, assign, _) in enumerate(p["gaps"]):
        start_a = A[i] + maxla[i]
        arrow_a = A[i + 1] - 1
        for key, (t, ges) in assign.items():
            if t is None:
                track_a = start_a
            elif p.get("late_tracks"):
                track_a = arrow_a - T + t
            else:
                track_a = start_a + 1 + t
            for u, v in ges:
                cells = []
                ua = A[i] + (p["size"](u)[0] if u > 0 else maxla[i])  # first cell after u
                if u < 0:
                    ua = A[i] + maxla[i] - 1
                    seg_line(ua, port[u], track_a, port[u], cells)
                else:
                    seg_line(ua, port[u], track_a, port[u], cells)
                    # connect into the source border
                    lay.mask[phys(ua, port[u])] = (lay.mask.get(phys(ua, port[u]), 0)
                                                   | bit_toward(-1, 0))
                    tees.append((u, phys(ua - 1, port[u])))
                seg_line(track_a, port[u], track_a, port[v], cells)
                end_a = arrow_a if v > 0 else A[i + 1]
                seg_line(track_a, port[v], end_a, port[v], cells)
                if v > 0:
                    arrows.append(phys(arrow_a, port[v]))
                seg_paths[(u, v)] = cells
    # stitch chain segments into one path per real edge
    for (u, v), chain in sorted(p["chains"].items()):
        cells = []
        for x, y in zip(chain, chain[1:]):
            seg = seg_paths[(x, y)]
            if x < 0:
                cells += body[x][1:]
                seg = seg[1:] if seg and cells and seg[0] == cells[-1] else seg
            # drop duplicate joints between consecutive runs
            cells += [c for k, c in enumerate(seg) if not (k == 0 and cells and c == cells[-1])]
        lay.paths.append((u, v, cells))
    # line glyphs
    for xy, m in lay.mask.items():
        lay.cells[xy] = (LINE[m], COL["edge"], False)
    for xy in arrows:
        lay.cells[xy] = (ARROW[orient], COL["arrow"], False)
    # boxes
    for n, i in layer_of.items():
        if n < 0:
            continue
        nd = nodes[n]
        la, lcn = p["size"](n)
        a0, c0 = A[i], C[n]
        x0, y0 = phys(a0, c0)
        x1, y1 = (x0 + la - 1, y0 + lcn - 1) if orient == "LR" else (x0 + lcn - 1, y0 + la - 1)
        lay.boxes[n] = (x0, y0, x1, y1)
        st, col = style_of(nd)
        tl, tr, bl, br, hz, vt, _, _ = BOX[st]
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                lay.cells[(x, y)] = (" ", col, False)
        for x in range(x0 + 1, x1):
            lay.cells[(x, y0)] = (hz, col, False)
            lay.cells[(x, y1)] = (hz, col, False)
        for y in range(y0 + 1, y1):
            lay.cells[(x0, y)] = (vt, col, False)
            lay.cells[(x1, y)] = (vt, col, False)
        lay.cells[(x0, y0)] = (tl, col, False)
        lay.cells[(x1, y0)] = (tr, col, False)
        lay.cells[(x0, y1)] = (bl, col, False)
        lay.cells[(x1, y1)] = (br, col, False)
        lab = nd["label"]
        heavy = st == "heavy"
        tx = x0 + (x1 - x0 + 1 - dwidth(lab)) // 2
        for k, ch in enumerate(lab):
            lay.cells[(tx + k, y0 + 1)] = (ch, COL["gemm_text"] if heavy else COL["text"], heavy)
    for u, xy in tees:
        st, col = style_of(nodes[u])
        lay.cells[xy] = (BOX[st][6] if orient == "LR" else BOX[st][7], col, False)
    return lay


def stream_tags(nodes, edges, lay):
    """Write s1, s2, s3 into the top border of each branch of every fork."""
    succ = gd.succ(edges)
    for u in sorted(nodes):
        ks = [v for v in succ.get(u, ()) if v in lay.boxes]
        if len(ks) < 2:
            continue
        key = (lambda v: lay.boxes[v][1]) if lay.orient == "LR" else (lambda v: lay.boxes[v][0])
        preds = {}
        for a, b in edges:
            preds.setdefault(b, []).append(a)
        for i, v in enumerate(sorted(ks, key=key)):
            tag = f"s{i + 1}"
            # tag every node of the branch, down to the join
            w = v
            while True:
                x0, y0, x1, _ = lay.boxes[w]
                if x1 - x0 - 1 >= len(tag) + 2:
                    for k, ch in enumerate(tag):
                        lay.cells[(x0 + 2 + k, y0)] = (ch, COL["lane"], True)
                nxt = list(succ.get(w, ()))
                if len(nxt) != 1 or len(preds.get(nxt[0], ())) != 1:
                    break
                w = nxt[0]


LEGEND = [("┃GEMM┃", "", "gemm"), ("│kernel│", "", "kernel"), ("┆memset/memcpy┆", "", "mem"),
          ("┆event┆", "", "event"), ("s1", "stream branch", "lane")]


def legend(present):
    row = []
    for sym, txt, k in LEGEND:
        if k not in present:
            continue
        row += [(ch, COL[k], k in ("gemm", "lane")) for ch in sym]
        row += [(ch, COL["dim"], False) for ch in (" " + txt if txt else "") + "   "]
    return row


WRAP_TOP = 2      # rows above the columns: the track carrying an edge into the next column
WRAP_GUTTER = 4   # columns between wrapped columns


def _cuts(cn, ce):
    """Layer boundaries where the graph can be cut into columns: one node above, one node
    below, and the single edge between them is the only edge crossing the boundary."""
    from cgviz.layout import layers_of

    L, depth = layers_of(cn, ce)
    out = {}
    for i in range(len(L) - 1):
        if len(L[i]) == 1 and len(L[i + 1]) == 1:
            cross = [(u, v) for u, v in ce if depth[u] <= i < depth[v]]
            if cross == [(L[i][0], L[i + 1][0])]:
                out[i] = cross[0]
    return L, out


def _connect(lay, cells):
    for a, b in zip(cells, cells[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        lay.mask[a] = lay.mask.get(a, 0) | {(1, 0): E, (-1, 0): W, (0, 1): S, (0, -1): N}[(dx, dy)]
        lay.mask[b] = lay.mask.get(b, 0) | {(1, 0): W, (-1, 0): E, (0, 1): N, (0, -1): S}[(dx, dy)]


def wrap(cn, ce, node_gap, rank_gap, max_h):
    """Top-to-bottom layout folded into side-by-side columns no taller than max_h rows
    (where the graph has places to cut), like newspaper columns. The edge from the bottom of
    one column runs right along the row under it, up the gutter, along the top track and down
    into the first box of the next column. Returns None when the graph has no cut points."""
    from cgviz.layout import _line_cells

    L, cuts = _cuts(cn, ce)
    if not cuts:
        return None

    def band_plan(lo, hi):
        ids = {n for layer in L[lo:hi + 1] for n in layer}
        sub = {n: cn[n] for n in ids}
        return plan(sub, {(u, v) for u, v in ce if u in ids and v in ids}, "TB", node_gap,
                    rank_gap), sub

    bands, lo = [], 0
    while lo < len(L):
        hi = len(L) - 1
        if dims(band_plan(lo, hi)[0], "TB")[1] > max_h:
            ok = [i for i in sorted(cuts) if i >= lo and
                  dims(band_plan(lo, i)[0], "TB")[1] <= max_h]
            later = [i for i in sorted(cuts) if i >= lo]
            hi = ok[-1] if ok else (later[0] if later else hi)
        bands.append((lo, hi))
        lo = hi + 1
    if len(bands) == 1:
        return None
    drawn = []
    for lo, hi in bands:
        p, sub = band_plan(lo, hi)
        drawn.append(draw_plan(sub, p, "TB"))
    W = sum(b.width for b in drawn) + WRAP_GUTTER * (len(drawn) - 1)
    H = WRAP_TOP + max(b.height for b in drawn) + 1
    lay = Layout("TB", W, H)
    x = 0
    for b in drawn:
        for (cx, cy), m in b.mask.items():
            lay.mask[(cx + x, cy + WRAP_TOP)] = m
        for (cx, cy), c in b.cells.items():
            lay.cells[(cx + x, cy + WRAP_TOP)] = c
        for n, (x0, y0, x1, y1) in b.boxes.items():
            lay.boxes[n] = (x0 + x, y0 + WRAP_TOP, x1 + x, y1 + WRAP_TOP)
        for u, v, cells in b.paths:
            lay.paths.append((u, v, [(cx + x, cy + WRAP_TOP) for cx, cy in cells]))
        x += b.width + WRAP_GUTTER
    # the edges between columns
    x = 0
    for k, b in enumerate(drawn[:-1]):
        u, v = cuts[bands[k][1]]
        ux0, _, ux1, uy1 = lay.boxes[u]
        vx0, vy0, vx1, _ = lay.boxes[v]
        pu, pv, gx = (ux0 + ux1) // 2, (vx0 + vx1) // 2, x + b.width + WRAP_GUTTER // 2 - 1
        x += b.width + WRAP_GUTTER
        corners = [(pu, uy1 + 1), (gx, uy1 + 1), (gx, 0), (pv, 0), (pv, vy0 - 1)]
        cells = [corners[0]]
        for a, c in zip(corners, corners[1:]):
            cells += _line_cells(a, c)[1:]
        _connect(lay, cells)
        lay.mask[cells[0]] |= N                       # joined to the source box's border
        lay.paths.append((u, v, cells))
        st, col = style_of(cn[u])
        lay.cells[(pu, uy1)] = (BOX[st][7], col, False)
        for xy in cells:
            lay.cells[xy] = (LINE[lay.mask[xy]], COL["edge"], False)
        lay.cells[cells[-1]] = (ARROW["TB"], COL["arrow"], False)
    lay.columns = len(drawn)
    return lay


def layout(data, roles=None, width=120, prefer=("LR", "TB"), node_gap=None, rank_gap=0,
           height=None):
    """Lay the graph out. node_gap may be a number or {orient: number}. With `height`, the
    first orientation that fits width x height wins; if none does, the top-to-bottom layout
    is folded into columns (see `wrap`) so the whole graph stays in view."""
    nodes, edges = gd.load(data, roles)
    cn, ce = gd.collapse(nodes, edges)
    label_nodes(nodes, cn, roles)

    def gap(o):
        return node_gap.get(o) if isinstance(node_gap, dict) else node_gap

    tried = []
    for orient in prefer:
        p = plan(cn, ce, orient, gap(orient), rank_gap)
        w, h = dims(p, orient)
        tried.append((orient, w, h))
        if w <= width and (height is None or h <= height):
            break
    else:
        if height is not None:
            lay = wrap(cn, ce, gap("TB"), rank_gap, height)
            if lay is not None:
                return _finish(lay, nodes, cn, ce, tried, width)
        if not prefer:                    # asked for columns, but the graph can't be folded
            orient = "TB"
            p = plan(cn, ce, orient, gap(orient), rank_gap)
    lay = draw_plan(cn, p, orient)
    return _finish(lay, nodes, cn, ce, tried, width)


def _finish(lay, nodes, cn, ce, tried, width):
    stream_tags(cn, ce, lay)
    present = {("gemm" if style_of(nd)[0] == "heavy" else nd["kind"]) for nd in cn.values()}
    forks = any(len(v) > 1 for v in gd.succ(ce).values())
    lay.legend = legend(present | ({"lane"} if forks else set()))
    lay.tried = tried
    lay.fits = lay.width <= width
    return lay, nodes, cn, ce


def rows_of(lay):
    out = []
    for y in range(lay.height):
        out.append([lay.cells.get((x, y), (" ", None, False)) for x in range(lay.width)])
    out.append([(" ", None, False)])
    out.append(lay.legend)
    return out


def to_text(lay):
    return "\n".join("".join(c[0] for c in r).rstrip() for r in rows_of(lay))


def to_ansi(lay):
    out = []
    for r in rows_of(lay):
        s, cur = [], None
        for ch, col, bold in r:
            st = (col, bold) if ch != " " else (None, False)
            if st != cur:
                s.append("\x1b[0m" + ("\x1b[1m" if bold else "") +
                         ("\x1b[38;2;%d;%d;%dm" % col if col else ""))
                cur = st
            s.append(ch)
        out.append("".join(s).rstrip() + "\x1b[0m")
    return "\n".join(out)


def node_list(nodes, cn, width=120, full=False):
    lab = {m: nd["label"] for nd in cn.values() for m in nd["members"]}
    lw = max(dwidth(v) for v in lab.values())
    lines = []
    for n in sorted(nodes):
        name = nodes[n]["full"] if full else short_name(nodes[n]["full"])
        kind = "gemm" if nodes[n]["op"] in ("gemm", "splitK") else nodes[n]["kind"]
        head = f"{n:>3}  {kind:<6}  {lab[n]:<{lw}}  "
        line = head + name
        lines.append(line if full else cut(line, width))
    return "\n".join(lines)


def draw_graph(g, pos: dict[Hashable, tuple[float, float]]):
    """Takes: a DiGraph with `kind`/`name` attributes and node positions.
    Gives: a matplotlib Figure with thick shapes, numbered nodes and no small text.
    Raises: KeyError if a node has no position.
    (Scaffold API; the terminal drawing above is what the CLI uses.)"""
    raise NotImplementedError("TODO(veer)")
