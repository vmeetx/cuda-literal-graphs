"""Miku walks the graph: route, walker, sprite, camera and keyframe tests.

Run with UPDATE_GOLDEN=1 to accept a deliberate change to the keyframes.
"""

import json
import os
from pathlib import Path

import pytest

from cgviz import draw, presets, show, walk

FIX = Path(__file__).parent / "fixtures/graphs"
GOLDEN = Path(__file__).parent / "golden"
COLS, ROWS = 100, 30


def build(preset, cols=COLS, rows=ROWS, panel=True):
    data = json.loads((FIX / f"{preset}.json").read_text())
    lay, *_ = draw.layout(data, presets.ROLES[preset], cols)
    alay, _, acn, ace = draw.layout(data, presets.ROLES[preset], cols, prefer=(lay.orient,),
                                    node_gap=show.NODE_GAP[lay.orient])
    w = walk.Walk(alay, acn, ace)
    frames = w.frames()
    return w, frames, show.Scene(alay, acn, frames, cols, rows, panel=panel, title=preset)


@pytest.fixture(scope="module", params=["diamond", "decode", "prefill"])
def run(request):
    return request.param, build(request.param)


def test_route_visits_every_node_exactly_once(run):
    _, (w, frames, sc) = run
    assert sorted(w.visits) == sorted(sc.nodes)
    assert len(w.visits) == len(set(w.visits))


def test_visits_respect_execution_order(run):
    _, (w, _, _) = run
    seen = {n: i for i, n in enumerate(w.visits)}
    for u, v in w.edges:
        assert seen[u] < seen[v], (u, v)


def test_walkers_only_stand_on_edge_or_node_cells(run):
    _, (w, _, sc) = run
    allowed = set()
    for _, _, cells in sc.lay.paths:
        allowed |= set(cells)
    for border in sc.border.values():
        allowed |= border
    for wid, pos in w.trace:
        assert pos in allowed, (wid, pos)


def test_walkers_never_enter_a_box_interior(run):
    _, (w, _, sc) = run
    inside = {(x, y) for x0, y0, x1, y1 in sc.lay.boxes.values()
              for x in range(x0 + 1, x1) for y in range(y0 + 1, y1)}
    assert not inside & {p for _, p in w.trace}


def test_split_count_equals_out_degree(run):
    _, (w, _, _) = run
    forks = {u: len(vs) for u, vs in w.succ.items() if len(vs) > 1}
    assert forks, "preset has no fork"
    for u, k in forks.items():
        assert w.splits[u] == k


def test_joins_merge_only_after_all_branches_arrive(run):
    _, (w, _, _) = run
    joins = {v: len(us) for v, us in w.pred.items() if len(us) > 1}
    assert joins
    assert sorted(v for v, _ in w.merges) == sorted(joins)
    for v, arrived in w.merges:
        assert arrived == joins[v]


def test_walker_count_follows_forks_and_joins(run):
    _, (w, frames, _) = run
    assert len(frames[0].walkers) == 1
    assert len(frames[-1].walkers) == 1
    assert max(len(f.walkers) for f in frames) == max(w.splits.values())


def test_ends_in_victory(run):
    _, (w, frames, _) = run
    assert frames[-1].event == "victory"
    assert frames[-1].walkers[0][2] == "victory_1"
    assert frames[-1].walkers[0][1] == w.route[w.final][1]


def _base(sc, i):
    """Frame i composed without walkers (the graph as the camera sees it)."""
    f = sc.frames[i]
    saved = f.walkers
    f.walkers = []
    try:
        return sc.compose(i)
    finally:
        f.walkers = saved


def test_transparent_sprite_pixels_never_overwrite_graph_cells(run):
    _, (w, frames, sc) = run
    for i in range(0, len(frames), max(1, len(frames) // 40)):
        grid, base = sc.compose(i), _base(sc, i)
        opaque = set()
        cx, cy = sc.cams[i]
        for (wid, pos, sprite, facing, dy), (sx, sy, _, _) in zip(frames[i].walkers, sc.rects(i)):
            for j, row in enumerate(show.sprite_cells(sprite, facing, dy)):
                for k, cell in enumerate(row):
                    if cell is not None:
                        opaque.add((sy + j - cy, sx + k - cx))
        for r in range(sc.vh):
            for c in range(sc.vw):
                if (r, c) not in opaque:
                    assert grid[r][c] == base[r][c], (i, r, c)


@pytest.mark.parametrize("size", [(100, 30), (60, 20), (160, 50)])
def test_every_frame_fits_the_viewport_and_keeps_her_in_view(size):
    for preset in ("diamond", "decode"):
        _, frames, sc = build(preset, *size)
        for i in range(len(frames)):
            grid = sc.compose(i)
            assert len(grid) == size[1] and all(len(r) == size[0] for r in grid)
            cx, cy = sc.cams[i]
            rs = sc.rects(i)
            fits_x = max(r[2] for r in rs) - min(r[0] for r in rs) + 1 <= sc.vw
            fits_y = max(r[3] for r in rs) - min(r[1] for r in rs) + 1 <= sc.vh
            for x0, y0, x1, y1 in rs:
                if fits_x and sc.cw > sc.vw:
                    assert cx <= x0 and x1 < cx + sc.vw, (preset, i)
                if fits_y and sc.ch > sc.vh:
                    assert cy <= y0 and y1 < cy + sc.vh, (preset, i)


def test_camera_moves_smoothly():
    _, frames, sc = build("decode")
    for (ax, ay), (bx, by) in zip(sc.cams, sc.cams[1:]):
        assert abs(bx - ax) <= 3 and abs(by - ay) <= 3


def test_diff_redraw_touches_only_changed_cells():
    _, frames, sc = build("diamond")
    a, b = sc.compose(10), sc.compose(11)
    assert show.diff(a, a) == ""
    changed = sum(1 for r in range(len(a)) for c in range(len(a[0])) if a[r][c] != b[r][c])
    full = show.diff(None, b)
    assert len(show.diff(a, b)) < len(full) or changed == len(a) * len(a[0])


def _keyframes(frames):
    idx = {"first": 0}
    split_at = None
    for i, f in enumerate(frames):
        if f.event == "split" and split_at is None:
            split_at = i
        if split_at is not None and "fork" not in idx and len(f.walkers) > 1:
            spread = min(abs(a[1][0] - b[1][0]) + abs(a[1][1] - b[1][1])
                         for a in f.walkers for b in f.walkers if a is not b)
            if spread >= 8:
                idx["fork"] = i
        if f.event == "merge" and "join" not in idx:
            idx["join"] = max(i - 1, 0)
    idx["final"] = len(frames) - 1
    return idx


@pytest.mark.parametrize("preset", ["diamond", "decode"])
def test_keyframe_goldens(preset):
    _, frames, sc = build(preset)
    idx = _keyframes(frames)
    assert set(idx) == {"first", "fork", "join", "final"}
    got = "\n\n".join(f"== {k} (frame {i})\n" + show.grid_text(sc.compose(i))
                      for k, i in idx.items()) + "\n"
    path = GOLDEN / f"anim_{preset}_{COLS}x{ROWS}.txt"
    if os.environ.get("UPDATE_GOLDEN") or not path.exists():
        path.write_text(got, encoding="utf-8")
    assert got == path.read_text(encoding="utf-8")


def test_special_captions():
    _, frames, sc = build("decode")
    caps = {f.caption for f in frames}
    assert any("cuBLAS split this GEMM in two" in c for c in caps)
    assert any("8 tiny kernels squashed into one box" in c for c in caps)
