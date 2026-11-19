"""Facing rules for Miku v2: turn the moves of a walk into ticks of (clip, frame, facing, x).

Invariants (checked by `violations`, enforced by `plan`):
- she faces the way she is moving;
- every change of direction plays a turn; she never switches straight from one profile to the
  other (right -> front -> left), and never moonwalks;
- the walk cycle plays only in profile;
- she turns to the front when she stops at a node, and toward the next target when leaving.
Standard library only.
"""

from __future__ import annotations

from dataclasses import dataclass

from cgviz import miku_assets

WALK_CELLS_PER_TICK = 1


@dataclass(frozen=True)
class Tick:
    clip: str          # "idle" (front hold), "walk", "walk_tired", "turn_to_side", "turn_to_front"
    frame: int         # frame index within the clip
    facing: str        # "front", "right" or "left"
    x: int             # walker cell
    moving: int = 0    # -1, 0, +1: direction the walker moved on this tick


def _clip_ticks(clip):
    return miku_assets.ticks(clip)


def _play(out, clip, facing, x):
    """Append a turn clip. A frame drawn in front view faces front, whatever the direction."""
    frames = miku_assets.load(clip)["frames"]
    for i, f in enumerate(frames):
        view = f.get("anchors", {}).get("view")
        for _ in range(f["ticks"]):
            out.append(Tick(clip, i, "front" if view == "front" else facing, x))


def plan(moves, x0=0, idle_ticks=12, tired=None):
    """moves: a list of ("walk", target_x) and ("stop", None).
    tired: optional set of move indices that use walk_tired. Returns a list of Ticks."""
    out: list[Tick] = []
    x, facing = x0, "front"
    for _ in range(idle_ticks):
        out.append(Tick("idle", 0, "front", x))
    for k, (kind, target) in enumerate(moves):
        if kind == "stop":
            if facing != "front":
                _play(out, "turn_to_front", facing, x)
                facing = "front"
            for _ in range(idle_ticks):
                out.append(Tick("idle", 0, "front", x))
            continue
        d = (target > x) - (target < x)
        if d == 0:
            continue
        want = "right" if d > 0 else "left"
        if facing not in ("front", want):          # opposite profile: through the front
            _play(out, "turn_to_front", facing, x)
            facing = "front"
        if facing == "front":
            _play(out, "turn_to_side", want, x)
            facing = want
        clip = "walk_tired" if tired and k in tired else "walk"
        seq = [(i, n) for i, n in enumerate(_clip_ticks(clip))]
        step = 0
        while x != target:
            i, n = seq[(step // 1) % len(seq)]
            for _ in range(n):
                if x == target:
                    break
                x += d * WALK_CELLS_PER_TICK
                out.append(Tick(clip, i, facing, x, d))
            step += 1
    return out


def violations(ticks):
    """Every broken facing rule, as (tick index, message)."""
    bad = []
    prev = None
    for k, t in enumerate(ticks):
        if t.moving:
            if t.clip not in ("walk", "walk_tired"):
                bad.append((k, f"moving during {t.clip}"))
            if t.facing != ("right" if t.moving > 0 else "left"):
                bad.append((k, f"moving {t.moving:+d} while facing {t.facing} (moonwalk)"))
        if t.clip in ("walk", "walk_tired") and t.facing == "front":
            bad.append((k, "walk cycle in front view"))
        if prev is not None and prev.facing != t.facing:
            pair = {prev.facing, t.facing}
            if pair == {"left", "right"}:
                bad.append((k, "switched profile to profile without a turn"))
            if "front" in pair and not (prev.clip.startswith("turn") or t.clip.startswith("turn")):
                bad.append((k, f"{prev.facing}->{t.facing} without a turn clip"))
        prev = t
    return bad
