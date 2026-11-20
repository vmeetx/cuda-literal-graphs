"""Load Miku v2 sprite clips (cgviz/assets/miku/*.json). Standard library only.

Each clip holds palette-indexed frames drawn facing right (or front), each with a duration in
ticks (1 tick = 1/12 s) and anchor metadata. Left-facing frames are mirrors.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

ASSETS = Path(__file__).resolve().parent / "assets" / "miku"

# Size tiers, largest first: each is drawn by hand at its size (never scaled), with the same
# clips and timing, so the facing planner works for all of them. (width px, height px, folder)
TIERS = {"full": (74, 72, ""), "compact": (37, 36, "compact")}
RESERVE_ROWS = 6     # terminal rows kept for the graph box, the caption and a margin
RESERVE_COLS = 16


def _rgb(hx):
    return tuple(int(hx[i:i + 2], 16) for i in (1, 3, 5))


def tier_cells(tier: str) -> tuple[int, int]:
    """Sprite size in terminal cells (two pixels per cell vertically)."""
    w, h, _ = TIERS[tier]
    return w, (h + 1) // 2


def pick_tier(cols: int, rows: int) -> str | None:
    """The largest tier that fits a cols x rows terminal with room for the graph, or None
    when even the smallest doesn't (then the graph is shown without her)."""
    for tier in TIERS:
        w, h = tier_cells(tier)
        if cols >= w + RESERVE_COLS and rows >= h + RESERVE_ROWS:
            return tier
    return None


@lru_cache(maxsize=None)
def load(clip: str, tier: str = "full") -> dict:
    data = json.loads((ASSETS / TIERS[tier][2] / f"{clip}.json").read_text(encoding="utf-8"))
    data["rgb"] = {k: _rgb(v) for k, v in data["palette"].items()}
    return data


def clips(tier: str = "full") -> list[str]:
    return sorted(p.stem for p in (ASSETS / TIERS[tier][2]).glob("*.json"))


def frame_grid(clip: str, index: int, facing: str = "right", tier: str = "full") -> list[str]:
    rows = load(clip, tier)["frames"][index]["grid"]
    if facing == "left":
        return [r[::-1] for r in rows]
    return rows


def ticks(clip: str, tier: str = "full") -> list[int]:
    return [f["ticks"] for f in load(clip, tier)["frames"]]


def terminal_variant(rows: list[str]) -> list[str]:
    """Outer silhouette outline (navy touching transparency or the ground shadow) becomes the
    slate 'O', so she stays readable on dark terminals; inner navy lines stay navy."""
    h, w = len(rows), len(rows[0])
    out = []
    for y in range(h):
        r = list(rows[y])
        for x in range(w):
            if r[x] != "B":
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if not (0 <= nx < w and 0 <= ny < h) or rows[ny][nx] in ".Z":
                    r[x] = "O"
                    break
        out.append("".join(r))
    return out
