"""Invariant and golden tests for the box-drawing graph renderer (cgviz/draw.py).

Run with UPDATE_GOLDEN=1 to accept a deliberate layout change.
"""

import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
from cgviz import draw as bd  # noqa: E402

FIX = Path(__file__).parent / "fixtures/graphs"
GOLDEN = Path(__file__).parent / "golden"
LAYER = ["Q", "K", "V", "QK", "PV", "out", "gate", "up", "down"]
ROLES = {"diamond": ["gemm1", "gemm2"], "decode": LAYER, "prefill": LAYER}
PRESETS = ["diamond", "decode", "prefill"]
WIDTH = 120


def build(preset, width=WIDTH):
    data = json.loads((FIX / f"{preset}.json").read_text())
    return bd.layout(data, ROLES[preset], width)


@pytest.fixture(scope="module", params=PRESETS)
def built(request):
    return request.param, build(request.param)


def test_golden(built):
    preset, (lay, nodes, cn, _) = built
    got = bd.to_text(lay) + "\n\n" + bd.node_list(nodes, cn, WIDTH) + "\n"
    path = GOLDEN / f"box_{preset}.txt"
    if os.environ.get("UPDATE_GOLDEN") or not path.exists():
        path.write_text(got, encoding="utf-8")
    assert got == path.read_text(encoding="utf-8")


def test_fits_width(built):
    _, (lay, *_rest) = built
    assert lay.width <= WIDTH


def test_boxes_do_not_overlap_and_keep_a_gap(built):
    _, (lay, *_rest) = built
    bs = list(lay.boxes.values())
    for i in range(len(bs)):
        for j in range(i + 1, len(bs)):
            a, b = bs[i], bs[j]
            # inflate a by one cell: no cell of b may fall inside
            sep = (a[2] + 1 < b[0] or b[2] + 1 < a[0] or a[3] + 1 < b[1] or b[3] + 1 < a[1])
            assert sep, (a, b)


def touches(box, xy):
    x0, y0, x1, y1 = box
    x, y = xy
    return (x0 - 1 <= x <= x1 + 1 and y0 <= y <= y1) or (y0 - 1 <= y <= y1 + 1 and x0 <= x <= x1)


def test_every_edge_is_a_connected_path_ending_in_an_arrowhead(built):
    _, (lay, _, cn, ce) = built
    drawn = {(u, v) for u, v, _ in lay.paths}
    assert drawn == set(ce)
    arrow = bd.ARROW[lay.orient]
    for u, v, cells in lay.paths:
        assert cells, (u, v)
        assert touches(lay.boxes[u], cells[0]), (u, v, cells[0])
        assert touches(lay.boxes[v], cells[-1]), (u, v, cells[-1])
        assert lay.cells[cells[-1]][0] == arrow, (u, v)
        for p, q in zip(cells, cells[1:]):
            assert abs(p[0] - q[0]) + abs(p[1] - q[1]) <= 1, (u, v, p, q)


def test_junction_glyphs_match_their_bitmask(built):
    _, (lay, *_rest) = built
    opp = {bd.N: bd.S, bd.S: bd.N, bd.E: bd.W, bd.W: bd.E}
    step = {bd.N: (0, -1), bd.S: (0, 1), bd.E: (1, 0), bd.W: (-1, 0)}
    box_cells = {(x, y) for x0, y0, x1, y1 in lay.boxes.values()
                 for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)}
    for xy, m in lay.mask.items():
        ch = lay.cells[xy][0]
        if ch == bd.ARROW[lay.orient]:
            continue
        assert ch == bd.LINE[m], (xy, ch, m)
        for d in (bd.N, bd.E, bd.S, bd.W):
            if m & d:
                nb = (xy[0] + step[d][0], xy[1] + step[d][1])
                ok = nb in box_cells or (lay.mask.get(nb, 0) & opp[d])
                assert ok, (xy, ch, d)


def test_no_label_is_numeric(built):
    _, (lay, _, cn, _) = built
    for nd in cn.values():
        assert not nd["label"].strip().isdigit(), nd


@pytest.mark.parametrize("width", [60, 80, 120])
def test_node_list_fits_width(width):
    for preset in PRESETS:
        lay, nodes, cn, _ = build(preset, width)
        for line in bd.node_list(nodes, cn, width).splitlines():
            assert bd.dwidth(line) <= width, line


def test_gemms_use_the_heavy_tile(built):
    _, (lay, _, cn, _) = built
    for n, nd in cn.items():
        x0, y0, _, _ = lay.boxes[n]
        heavy = nd["op"] in ("gemm", "splitK")
        assert (lay.cells[(x0, y0)][0] == "┏") == heavy, nd["label"]
