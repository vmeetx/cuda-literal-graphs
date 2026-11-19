"""Load Miku v2 sprite clips (cgviz/assets/miku/*.json). Standard library only.

Each clip holds palette-indexed frames drawn facing right (or front), each with a duration in
ticks (1 tick = 1/12 s) and anchor metadata. Left-facing frames are mirrors.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

ASSETS = Path(__file__).resolve().parent / "assets" / "miku"


def _rgb(hx):
    return tuple(int(hx[i:i + 2], 16) for i in (1, 3, 5))


@lru_cache(maxsize=None)
def load(clip: str) -> dict:
    data = json.loads((ASSETS / f"{clip}.json").read_text(encoding="utf-8"))
    data["rgb"] = {k: _rgb(v) for k, v in data["palette"].items()}
    return data


def clips() -> list[str]:
    return sorted(p.stem for p in ASSETS.glob("*.json"))


def frame_grid(clip: str, index: int, facing: str = "right") -> list[str]:
    rows = load(clip)["frames"][index]["grid"]
    if facing == "left":
        return [r[::-1] for r in rows]
    return rows


def ticks(clip: str) -> list[int]:
    return [f["ticks"] for f in load(clip)["frames"]]


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
