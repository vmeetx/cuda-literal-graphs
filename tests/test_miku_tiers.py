"""Size tiers: the compact Miku is the approved one at half size, with the same clips and timing,
and the largest tier that fits the terminal is picked."""

import pytest

from cgviz import miku_assets

COMPACT = miku_assets.clips("compact")


def test_compact_has_every_planner_clip():
    need = {"walk", "walk_tired", "walk_to_tired", "walk_from_tired", "turn_to_side",
            "turn_to_front", "turn_to_side_tired", "turn_to_front_tired"}
    assert need <= set(COMPACT)


@pytest.mark.parametrize("clip", COMPACT)
def test_compact_timing_matches_full(clip):
    """Same exposure sheets: the facing planner's timing holds for both tiers."""
    assert miku_assets.ticks(clip, "compact") == miku_assets.ticks(clip)
    full = [f["drawing"] for f in miku_assets.load(clip)["frames"]]
    small = [f["drawing"] for f in miku_assets.load(clip, "compact")["frames"]]
    assert small == full


@pytest.mark.parametrize("clip", COMPACT)
def test_compact_frames_size_palette_and_feet(clip):
    w, h, _ = miku_assets.TIERS["compact"]
    d = miku_assets.load(clip, "compact")
    for f in d["frames"]:
        g = f["grid"]
        assert len(g) == h and all(len(r) == w for r in g)
        assert set("".join(g)) <= set(d["palette"]) | {"."}
        assert any(c not in ".Z" for c in g[d["baseline"]]), (clip, f["drawing"])  # feet down
        assert not any(c not in ".Z" for c in g[d["baseline"] + 1]), (clip, f["drawing"])


def test_compact_head_does_not_shimmer():
    """Every walk frame halves on the same pixel pairs: once the bob is undone, the top of the
    head is identical in every frame."""
    tops = set()
    for f in miku_assets.load("walk", "compact")["frames"]:
        g = f["grid"]
        dy = (f["anchors"]["bob"] + f["anchors"]["head_dy"]) // 2
        tops.add(tuple(r[8:28] for r in g[2 + dy:7 + dy]))
    assert len(tops) == 1


@pytest.mark.parametrize("cols, rows, want", [
    (200, 60, "full"), (150, 44, "full"), (90, 42, "full"),
    (120, 30, "compact"), (80, 24, "compact"), (53, 24, "compact"),
    (80, 23, None), (52, 30, None),
])
def test_pick_tier(cols, rows, want):
    assert miku_assets.pick_tier(cols, rows) == want
