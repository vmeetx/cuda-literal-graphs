"""Miku v2: sprite data loading, exposure-sheet ticks, and facing rules."""

import sys
from pathlib import Path

import pytest

from cgviz import miku_assets, miku_motion

ROOT = Path(__file__).resolve().parents[1]
CLIPS = ["walk", "walk_tired", "turn_to_side", "turn_to_front"]


@pytest.mark.parametrize("clip", CLIPS)
def test_clip_loads_with_consistent_frames(clip):
    d = miku_assets.load(clip)
    sizes = {(len(f["grid"][0]), len(f["grid"])) for f in d["frames"]}
    assert len(sizes) == 1
    pal = set(d["palette"]) | {"."}
    for f in d["frames"]:
        assert set("".join(f["grid"])) <= pal
        assert f["ticks"] >= 1


def _xsheet_ticks(name):
    sys.path.insert(0, str(ROOT / "tools/miku"))
    import xsheet

    return [f["ticks"] for f in xsheet.load(name)["frames"]]


@pytest.mark.parametrize("clip", CLIPS)
def test_clip_ticks_match_exposure_sheet(clip):
    assert miku_assets.ticks(clip) == _xsheet_ticks(clip)


def test_walk_is_one_second():
    assert sum(miku_assets.ticks("walk")) == 12


def test_left_is_mirror_of_right():
    r = miku_assets.frame_grid("walk", 0, "right")
    l = miku_assets.frame_grid("walk", 0, "left")
    assert l == [row[::-1] for row in r]


def test_walk_head_only_bobs():
    """Region-diff intent: above the shoulders, every walk frame equals frame 0 shifted by its bob
    (tails excluded: they are procedural)."""
    d = miku_assets.load("walk")
    f0 = d["frames"][0]
    def head(f):
        b = f["anchors"]["bob"]
        return [r[40:58] for r in f["grid"][2 + b:30 + b]]   # face, fringe, crown front: tails never reach it
    h0 = head(f0)
    for f in d["frames"][1:]:
        assert head(f) == h0, f["drawing"]


def test_plan_obeys_facing_rules():
    ticks = miku_motion.plan([("walk", 40), ("stop", None), ("walk", 5), ("stop", None),
                              ("walk", 30)], x0=10)
    assert miku_motion.violations(ticks) == []


def test_reversal_goes_through_front():
    ticks = miku_motion.plan([("walk", 20), ("walk", 0)], x0=10)
    facings = [t.facing for t in ticks]
    i = facings.index("left")
    assert "front" in facings[facings.index("right"):i]
    assert miku_motion.violations(ticks) == []


def test_stop_turns_to_front_and_leaving_turns_toward_target():
    ticks = miku_motion.plan([("walk", 20), ("stop", None), ("walk", 0)], x0=10)
    stops = [k for k, t in enumerate(ticks) if t.clip == "idle" and k > 12]
    assert ticks[stops[0]].facing == "front"
    k = stops[-1] + 1
    assert ticks[k].clip == "turn_to_side"
    while ticks[k].clip == "turn_to_side":
        k += 1
    assert ticks[k - 1].facing == "left"          # the turn ends facing the target
    assert ticks[k].clip == "walk" and ticks[k].moving == -1


def test_violations_detects_moonwalk_and_profile_flip():
    T = miku_motion.Tick
    bad = miku_motion.violations([T("walk", 0, "right", 5, -1)])
    assert any("moonwalk" in m for _, m in bad)
    bad = miku_motion.violations([T("walk", 0, "right", 5, 1), T("walk", 0, "left", 4, -1)])
    assert any("profile to profile" in m for _, m in bad)
    bad = miku_motion.violations([T("walk", 0, "front", 5, 0)])
    assert any("front view" in m for _, m in bad)
