"""Miku v2 on the graph walk: turn the walk simulation's frames into v2 clip frames, and give
the scene her cells. Standard library only.

walk.Walk(turns=TURN_TICKS) produces, per frame and walker, a state sprite ("walk",
"turn_side", "turn_reverse", "idle_1", "wait_1", "victory_1"). `animate` replaces each one with
a v2 key (clip, frame index, facing) under the facing rules of cgviz.miku_motion:
- the walk cycle advances one tick per cell walked, so at any --speed her feet keep pace with
  the ground;
- leaving a node she plays turn_to_side; reversing she plays turn_to_front then turn_to_side;
  stopping at a node she plays turn_to_front, then stands facing front;
- waiting at a join or before leaving a fork she stands in profile;
- the victory is the front pose with a hop.
"""

from __future__ import annotations

from functools import lru_cache

from cgviz import halfblock, miku_assets

HEADROOM = 4    # pixels above her head for the victory hop (the hop is at most 3 px)


def turn_ticks(tier="full"):
    side = sum(miku_assets.ticks("turn_to_side", tier))
    return {"side": side, "reverse": sum(miku_assets.ticks("turn_to_front", tier)) + side}


def _at_tick(clip, t, tier):
    """Frame index of `clip` showing at tick t (t wraps)."""
    ts = miku_assets.ticks(clip, tier)
    t %= sum(ts)
    for i, n in enumerate(ts):
        if t < n:
            return i
        t -= n
    return len(ts) - 1


def _turn(clip, k, n, facing, tier):
    """Frame k of n frames spent on `clip`: the clip stretched or squeezed over n frames."""
    total = sum(miku_assets.ticks(clip, tier))
    i = _at_tick(clip, min(total - 1, k * total // max(1, n)), tier)
    view = miku_assets.load(clip, tier)["frames"][i].get("anchors", {}).get("view")
    return clip, i, "front" if view == "front" else facing


FRONT = ("turn_to_side", 0, "front")


def _profile(tier, facing):
    return "turn_to_side", len(miku_assets.ticks("turn_to_side", tier)) - 1, facing


def animate(frames, tier="full", speed=1.0):
    """walk.Frame list (from a Walk with turns) -> the same frames with v2 keys as sprites."""
    from cgviz.walk import Frame

    # run lengths: how many frames in a row each walker keeps the same state sprite
    seqs: dict = {}
    for fi, f in enumerate(frames):
        for wid, pos, sprite, facing, dy in f.walkers:
            seqs.setdefault(wid, []).append((fi, sprite))
    run_len = {}
    for wid, seq in seqs.items():
        i = 0
        while i < len(seq):
            j = i
            while j + 1 < len(seq) and seq[j + 1][1] == seq[i][1] and seq[j + 1][0] == seq[j][0] + 1:
                j += 1
            for k in range(i, j + 1):
                run_len[(wid, seq[k][0])] = (k - i, j - i + 1)
            i = j + 1
    to_front = max(1, round(sum(miku_assets.ticks("turn_to_front", tier)) / max(speed, 0.1)))

    state: dict = {}            # wid -> {"pos", "dist", "view"}
    out = []
    for fi, f in enumerate(frames):
        walkers = []
        for wid, pos, sprite, facing, dy in f.walkers:
            side = "right" if facing > 0 else "left"
            st = state.get(wid)
            if st is None:       # a new walker splits off one standing on the same cell
                twin = next((s for s in state.values() if s["pos"] == pos), None)
                st = state[wid] = {"pos": pos, "dist": twin["dist"] if twin else 0,
                                   "view": twin["view"] if twin else "front", "run_view": None}
            k, n = run_len[(wid, fi)]
            if k == 0:
                st["run_view"] = st["view"]          # how she stood when this run began
            if sprite == "walk":
                (x0, y0), (x1, y1) = st["pos"], pos
                st["dist"] += max(abs(x1 - x0), abs(y1 - y0))
                key = ("walk", _at_tick("walk", st["dist"], tier), side)
            elif sprite == "turn_side":
                key = _turn("turn_to_side", k, n, side, tier)
            elif sprite == "turn_reverse":
                half = n // 2
                key = (_turn("turn_to_front", k, half, "left" if facing > 0 else "right", tier)
                       if k < half else _turn("turn_to_side", k - half, n - half, side, tier))
            elif sprite == "wait_1":
                key = _profile(tier, side)
            elif sprite == "victory_1":
                key = ("victory",) + FRONT[1:]
            else:                                   # idle_1: stopped at a node
                if st["run_view"] != "front" and k < min(to_front, n):
                    key = _turn("turn_to_front", k, min(to_front, n),
                                st["run_view"] or side, tier)
                else:
                    key = FRONT
            st["pos"] = pos
            st["view"] = key[2]
            walkers.append((wid, pos, key, facing, dy if sprite == "victory_1" else 0))
        for gone in [w for w in state if w not in {x[0] for x in f.walkers}]:
            del state[gone]
        out.append(Frame(walkers, f.highlight, f.caption, f.event))
    return out


class Sprites:
    """The v2 sprite for show.Scene: size, placement and cells. Her feet stand on the walker's
    row beside a vertical line, or on the row just above a horizontal one."""

    portrait = False

    def __init__(self, tier="full"):
        self.tier = tier
        wpx, hpx, _ = miku_assets.TIERS[tier]
        base = miku_assets.load("walk", tier)["baseline"]
        self.w, self.h = wpx, (hpx + HEADROOM + 1) // 2
        self.feet = (base + HEADROOM) // 2          # cell row of her soles
        self.side = (-(self.w // 2), -self.feet)
        self.above = (-(self.w // 2), -self.feet - 1)
        self.stand = (1, -self.feet)                # on a box's right side: just right of it
        self.under = (-(self.w // 2), 1)            # on its bottom border: just under it
        self.pal = miku_assets.load("walk", tier)["rgb"]

    def is_victory(self, key):
        return key[0] == "victory"

    def victory_at(self, box):
        x0, y0, x1, _ = box
        return (x0 + x1) // 2 + self.above[0], y0 + self.above[1]

    def cells(self, key, facing=1, dy=0):
        return _cells(self.tier, key, dy)


@lru_cache(maxsize=None)
def _cells(tier, key, dy):
    clip, i, facing = key
    clip = "turn_to_side" if clip == "victory" else clip
    rows = miku_assets.frame_grid(clip, i, "left" if facing == "left" else "right", tier)
    rows = [r.replace("Z", ".") for r in rows]      # no ground shadow over the graph lines
    rows = miku_assets.terminal_variant(rows)
    w = len(rows[0])
    rows = ["." * w] * HEADROOM + rows
    if len(rows) % 2:
        rows.append("." * w)
    if dy < 0:
        rows = rows[-dy:] + ["." * w] * -dy
    elif dy > 0:
        rows = ["." * w] * dy + rows[:-dy]
    return halfblock.cells(rows, miku_assets.load("walk", tier)["rgb"])


def pick(cols, rows, size="auto"):
    """The v2 tier for a cols x rows terminal, or None for the small v1 sprite."""
    if size == "small":
        return None
    if size in miku_assets.TIERS:
        return size
    return miku_assets.pick_tier(cols, rows)


def walk(data, roles, width, orient, cols, rows, speed=1.0, size="auto"):
    """Lay the graph out with room for the sprite and simulate the walk.
    Returns (layout, nodes, frames, sprites); sprites is None for the v1 sprite."""
    from cgviz import draw, show
    from cgviz.walk import Walk

    tier = pick(cols, rows, size)
    if tier is None:
        lay, _, cn, ce = draw.layout(data, roles, width, prefer=(orient,),
                                     node_gap=show.NODE_GAP[orient])
        return lay, cn, Walk(lay, cn, ce, speed=speed).frames(), None
    sp = Sprites(tier)
    gap = {"TB": sp.w + 3, "LR": sp.h}[orient]      # siblings a sprite apart
    rank = {"TB": sp.h + 2, "LR": sp.w + 2}[orient]  # and layers too
    lay, _, cn, ce = draw.layout(data, roles, width, prefer=(orient,), node_gap=gap,
                                 rank_gap=rank)
    frames = Walk(lay, cn, ce, speed=speed, turns=turn_ticks(tier), gap=sp.w + 1).frames()
    return lay, cn, animate(frames, tier, speed), sp
