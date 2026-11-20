"""Miku v2 on the graph walk: the facing rules hold on real graphs at every size and speed, the
walk cycle keeps pace with the ground, and every frame composes in a small terminal."""

import json
from pathlib import Path

import pytest

from cgviz import draw, miku_assets, miku_walk, presets, show

FIX = Path(__file__).parent / "fixtures/graphs"


def run(preset, cols, rows, speed=1.0, size="auto"):
    data = json.loads((FIX / f"{preset}.json").read_text())
    lay0, *_ = draw.layout(data, presets.ROLES[preset], cols)
    lay, cn, frames, sp = miku_walk.walk(data, presets.ROLES[preset], cols, lay0.orient,
                                         cols, rows, speed, size)
    return lay, cn, frames, sp


CASES = [(p, c, r, s) for p in ("diamond", "decode", "prefill")
         for c, r, s in ((80, 24, 1.0), (150, 44, 1.0), (80, 24, 2.5))]


@pytest.fixture(scope="module", params=CASES, ids=lambda c: f"{c[0]}-{c[1]}x{c[2]}-x{c[3]}")
def walked(request):
    p, c, r, s = request.param
    return request.param, run(p, c, r, s)


def test_tier_follows_the_terminal(walked):
    (_, cols, rows, _), (_, _, _, sp) = walked
    assert sp.tier == miku_assets.pick_tier(cols, rows)


def test_keys_are_real_frames(walked):
    _, (_, _, frames, sp) = walked
    for f in frames:
        for _, _, (clip, i, facing), _, _ in f.walkers:
            clip = "turn_to_side" if clip == "victory" else clip
            assert 0 <= i < len(miku_assets.ticks(clip, sp.tier)), (clip, i)
            assert facing in ("front", "left", "right")


def test_facing_rules(walked):
    """She moves only in the walk cycle, faces the way she moves (no moonwalk), never in front
    view while walking, and every change of facing happens on a turn frame."""
    _, (_, _, frames, _) = walked
    last = {}
    for k, f in enumerate(frames):
        for wid, pos, (clip, _, facing), _, _ in f.walkers:
            if wid in last:
                ppos, pclip, pfacing = last[wid]
                if pos != ppos:
                    assert clip == "walk", (k, wid, clip)
                if pos[0] != ppos[0]:
                    assert facing == ("right" if pos[0] > ppos[0] else "left"), (k, wid)
                if facing != pfacing:
                    assert {facing, pfacing} != {"left", "right"}, (k, wid)
                    assert clip.startswith("turn") or pclip.startswith("turn"), (k, wid, pclip, clip)
            if clip == "walk":
                assert facing != "front", (k, wid)
            last[wid] = (pos, clip, facing)


def test_ends_in_victory(walked):
    _, (_, _, frames, _) = walked
    assert frames[-1].event == "victory"
    assert any(k[0] == "victory" for _, _, k, _, _ in frames[-1].walkers)


def test_every_frame_composes_with_her_in_view(walked):
    (_, cols, rows, _), (lay, cn, frames, sp) = walked
    sc = show.Scene(lay, cn, frames, cols, rows, sprites=sp)
    for i in range(0, len(frames), 7):
        g = sc.compose(i)
        assert len(g) == rows and all(len(r) == cols for r in g)
        cx, cy = sc.cams[i]
        # the camera follows the leftmost walker when they don't all fit
        x0, y0, x1, y1 = min(sc.rects(i))
        assert cx <= x0 and x1 < cx + sc.vw, i
        assert cy <= y0 and y1 < cy + sc.vh or any(
            cy <= r[1] and r[3] < cy + sc.vh for r in sc.rects(i)), i


def test_walk_cycle_keeps_pace_with_the_ground():
    """One walk tick per cell walked, at any speed: twice the speed, the same cycle per cell."""
    for speed in (1.0, 2.5):
        _, _, frames, sp = run("diamond", 80, 24, speed)
        dist, last = 0, None
        for f in frames:
            wid, pos, (clip, i, _), _, _ = f.walkers[0]
            if wid != 0:
                break
            if last is not None and clip == "walk":
                dist += max(abs(pos[0] - last[0]), abs(pos[1] - last[1]))
                assert i == miku_walk._at_tick("walk", dist, sp.tier)
            last = pos


@pytest.mark.parametrize("cols, rows, size, want", [
    (80, 24, "auto", "compact"), (150, 44, "auto", "full"), (60, 20, "auto", None),
    (150, 44, "compact", "compact"), (150, 44, "small", None),
])
def test_pick(cols, rows, size, want):
    assert miku_walk.pick(cols, rows, size) == want


def test_small_terminals_fall_back_to_the_v1_sprite():
    lay, cn, frames, sp = run("diamond", 60, 20)
    assert sp is None
    assert {s for f in frames for _, _, s, _, _ in f.walkers} <= {"idle_1", "walk_1", "walk_2",
                                                                  "victory_1"}
    show.Scene(lay, cn, frames, 60, 20).compose(len(frames) // 2)


def test_layers_leave_room_for_her():
    """Consecutive layers sit at least a sprite apart, so she never stands on a box."""
    lay, _, _, sp = run("decode", 80, 24)
    tops = sorted({y0 for _, y0, _, _ in lay.boxes.values()})
    assert min(b - a for a, b in zip(tops, tops[1:])) >= sp.h + 2
