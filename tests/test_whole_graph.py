"""The default view: the tiny sprite, with the whole graph in the terminal (folded into
columns when it is too tall), on all five workloads. Checks that the walk follows the captured
dependencies, and that the folded layout is still a well-formed drawing."""

import json
from pathlib import Path

import pytest

from cgviz import draw as bd
from cgviz import graphdata as gd
from cgviz import miku_walk, presets, show, walk

FIX = Path(__file__).parent / "fixtures/graphs"
WORKLOADS = ("diamond", "decode", "prefill", "mlp", "experts")
SIZES = {"diamond": (80, 24), "decode": (120, 40), "prefill": (120, 42), "mlp": (100, 24),
         "experts": (100, 36)}


def data(name):
    return json.loads((FIX / f"{name}.json").read_text())


def run(name, size="tiny", speed=1.0):
    cols, rows = SIZES[name]
    lay, cn, frames, sp = miku_walk.walk(data(name), presets.ROLES[name], cols, "TB", cols, rows,
                                         speed, size)
    return lay, cn, frames, sp


@pytest.fixture(scope="module", params=[(w, s) for w in WORKLOADS for s in ("tiny", "small")],
                ids=lambda p: f"{p[0]}-{p[1]}")
def walked(request):
    name, size = request.param
    return name, size, run(name, size)


def captured_edges(name):
    nodes, edges = gd.load(data(name), presets.ROLES[name])
    return gd.collapse(nodes, edges)


def spans(frames):
    """node -> (first frame highlighted, last frame highlighted)."""
    out = {}
    for i, f in enumerate(frames):
        for n in f.highlight:
            a, _ = out.get(n, (i, i))
            out[n] = (a, i)
    return out


def test_every_node_is_visited(walked):
    name, _, (_, cn, frames, _) = walked
    assert set(spans(frames)) == set(cn)


def test_no_node_starts_before_everything_it_depends_on_has_finished(walked):
    """The walk order is the captured dependency order: a kernel's box lights up only after
    the boxes of all the kernels it waits on have been left."""
    name, _, (_, cn, frames, _) = walked
    cn2, ce = captured_edges(name)
    sp = spans(frames)
    for u, v in ce:
        assert sp[u][1] < sp[v][0], (name, u, v)


def test_one_walker_per_branch_and_joins_wait_for_all(walked):
    name, _, (_, cn, frames, _) = walked
    _, ce = captured_edges(name)
    succ, pred = gd.succ(ce), {}
    for u, v in ce:
        pred.setdefault(v, set()).add(u)
    widest = max(len(vs) for vs in succ.values())
    assert max(len(f.walkers) for f in frames) == widest
    assert len(frames[0].walkers) == 1 and len(frames[-1].walkers) == 1
    assert frames[-1].event == "victory"


def test_the_whole_graph_stays_in_view(walked):
    """Tiny: every frame shows the whole graph, with no camera movement."""
    name, size, (lay, cn, frames, sp) = walked
    if size != "tiny":
        pytest.skip("only the tiny default promises the whole graph")
    cols, rows = SIZES[name]
    sc = show.Scene(lay, cn, frames, cols, rows, panel=False, sprites=sp)
    assert sc.cw <= cols and sc.ch <= sc.vh, (name, sc.cw, sc.ch)
    assert len(set(sc.cams)) == 1


@pytest.mark.parametrize("name", WORKLOADS)
def test_single_stream_is_a_chain_and_streams_make_forks(name):
    _, ce = captured_edges(name)
    forks = [u for u, vs in gd.succ(ce).items() if len(vs) > 1]
    assert bool(forks) == (name != "mlp")


@pytest.mark.parametrize("name", ("decode", "prefill"))
def test_folded_columns_are_a_well_formed_drawing(name):
    lay, cn, _, _ = run(name)
    assert getattr(lay, "columns", 1) > 1
    _, ce = captured_edges(name)
    assert {(u, v) for u, v, _ in lay.paths} == set(ce)
    boxes = list(lay.boxes.values())
    inside = {(x, y) for x0, y0, x1, y1 in boxes for x in range(x0, x1 + 1)
              for y in range(y0, y1 + 1)}
    for i, a in enumerate(boxes):
        for b in boxes[i + 1:]:
            assert a[2] + 1 < b[0] or b[2] + 1 < a[0] or a[3] + 1 < b[1] or b[3] + 1 < a[1]
    for u, v, cells in lay.paths:
        assert lay.cells[cells[-1]][0] == bd.ARROW["TB"], (u, v)
        assert not set(cells) & inside, (u, v)
        for p, q in zip(cells, cells[1:]):
            assert abs(p[0] - q[0]) + abs(p[1] - q[1]) <= 1, (u, v, p, q)
    for xy, m in lay.mask.items():
        if lay.cells[xy][0] != bd.ARROW["TB"]:
            assert lay.cells[xy][0] == bd.LINE[m], xy


def test_speed_changes_pace_not_what_she_visits():
    """Faster is shorter. Which of two independent branches lights up first is not part of the
    captured graph (it has no time axis), so only the dependency order is checked above."""
    a = run("experts", speed=1.0)[2]
    b = run("experts", speed=2.5)[2]
    assert set(spans(a)) == set(spans(b))
    assert len(b) < len(a)


def test_tiny_sprite_is_about_one_box():
    sp = show.TinySprites()
    assert sp.w <= 11 and sp.h <= 6
    for name in ("idle_1", "walk_1", "walk_2", "victory_1"):
        assert len(sp.cells(name)) == sp.h and len(sp.cells(name)[0]) == sp.w


def test_walk_module_keeps_the_fork_caption_honest():
    assert walk.FORK_NOTE == "independent: neither waits for the other"


@pytest.mark.parametrize("name", ("diamond", "decode", "experts"))
def test_tiny_branches_leave_a_fork_together(name):
    """Every branch of a fork is ready the moment the fork node is done: with the tiny sprite
    all its walkers start on the same frame."""
    _, _, frames, _ = run(name)
    seen, born = set(), {}
    for i, f in enumerate(frames):
        for wid, pos, *_ in f.walkers:
            if wid not in seen:
                seen.add(wid)
                born[wid] = i
    moved = {}
    last = {}
    for i, f in enumerate(frames):
        for wid, pos, *_ in f.walkers:
            if wid in last and last[wid] != pos and wid not in moved:
                moved[wid] = i
            last[wid] = pos
    for wid, b in born.items():
        if wid == 0:
            continue
        assert moved.get(wid) is None or moved[wid] - b <= 1, (name, wid, b, moved.get(wid))
