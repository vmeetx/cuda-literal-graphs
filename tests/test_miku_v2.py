"""Miku v2: sprite data loading, exposure-sheet ticks, and facing rules."""

import sys
from pathlib import Path

import pytest

from cgviz import miku_assets, miku_motion

ROOT = Path(__file__).resolve().parents[1]
CLIPS = ["walk", "walk_side", "walk_tired", "turn_to_side", "turn_to_front", "turn_to_side_tired",
         "turn_to_front_tired"]


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
        x0, x1 = f["anchors"].get("head_cols", [40, 55])     # face, fringe, crown: no tail or leek
        return [r[x0:x1] for r in f["grid"][2 + b:30 + b]]
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


@pytest.mark.parametrize("clip", CLIPS)
def test_no_tail_pixel_ahead_of_the_body(clip):
    """In every profile frame (facing right) both tails trail behind: no tail pixel is further
    forward than the body's leading edge."""
    for f in miku_assets.load(clip)["frames"]:
        a = f["anchors"]
        if a.get("view") not in ("side", "three_quarter"):
            continue
        assert a["tail_front_x"] < a["body_front_x"], (clip, f["drawing"], a["tail_front_x"],
                                                      a["body_front_x"])


def _lum(hx):
    r, g, b = (int(hx[i:i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def test_far_side_never_lighter_than_near_side():
    sys.path.insert(0, str(ROOT / "tools/miku"))
    import side_body
    import tails

    pal = miku_assets.load("walk")["palette"]
    pairs = []
    for k in side_body.NEAR:                                   # legs: sock, band, boot, outline
        pairs.append((side_body.NEAR[k], side_body.FAR[k]))
    for k in tails.NEAR_SHADES:                                # tails: highlight, base, shadow
        pairs.append((tails.NEAR_SHADES[k], tails.FAR_SHADES[k]))
    pairs += [("D", "M"), ("A", "C"), ("E", "P")]              # arms: sleeve, cuff, hand
    for near, far in pairs:
        assert _lum(pal[far]) <= _lum(pal[near]), (near, far)


def test_cheerful_walk_is_upright():
    """Posture: in every cheerful-walk frame the head centre is at most 1 px ahead of the hip
    centre (direction of travel = +x). Not applied to walk_tired, which slouches on purpose."""
    for f in miku_assets.load("walk")["frames"]:
        a = f["anchors"]
        assert a["head_cx"] - a["hip_cx"] <= 1.0, (f["drawing"], a["head_cx"], a["hip_cx"])


def test_tired_walk_uses_side_view_turns():
    ticks = miku_motion.plan([("walk", 30), ("stop", None), ("walk", 50)], x0=10, tired={2})
    clips = [t.clip for t in ticks]
    assert "turn_to_side" in clips and "turn_to_side_tired" in clips
    assert "turn_to_front" in clips and "walk_tired" in clips
    assert miku_motion.violations(ticks) == []


def test_diagonal_walk_keeps_a_foot_on_the_ground():
    """3/4 walk: in every drawing at least one foot touches the baseline (row 67)."""
    for f in miku_assets.load("walk")["frames"]:
        assert any(c not in ".Z" for c in f["grid"][67]), f["drawing"]
        assert all(c in ".Z" for c in f["grid"][68]), f["drawing"]
