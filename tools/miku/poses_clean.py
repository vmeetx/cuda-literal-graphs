"""Dev-only: clean the six resampled poses into one character on one palette.

    python tools/miku/poses_clean.py

Input: .wsl/poses_hi.json (six raw grids sampled at the normalisation pitch) and the study
palette. Steps, each recorded for MIKU_V2_REFERENCE.md:
1. Map every study colour onto one shared, named palette (2-3 step ramps per material).
2. Strip the anti-alias halo: light pixels on her outer edge that sit outside the outline.
3. Drop detached specks (islands under 4 pixels) that aren't part of her.
4. Put all six on one canvas size with a shared baseline (boot soles on the same row) and
   add the dim ground shadow under her feet.
Writes tools/miku/ref/poses_raw.json (after step 1, for before/after crops) and
tools/miku/ref/poses.json (after all steps) plus palette_v2.json.
"""

from __future__ import annotations

import json
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REF = ROOT / "tools/miku/ref"

# shared palette: letter -> (hex, name). Ramps: hair G>A>C, top L>N>K, skirt D>M,
# skin E>P, leek b>I>X, mouth S>V.
PALETTE = {
    "G": ("#caf1fa", "hair highlight"),
    "A": ("#6fcbe2", "hair cyan"),
    "C": ("#3c8698", "hair shadow teal"),
    "B": ("#111d37", "outline navy"),
    "F": ("#21364d", "dark slate: socks, boots, iris"),
    "L": ("#d3d6da", "top light grey"),
    "N": ("#aab2bc", "top grey"),
    "K": ("#758391", "top shade / pleat line"),
    "D": ("#4c6377", "skirt and sleeve grey"),
    "M": ("#3f485a", "skirt and sleeve shadow"),
    "E": ("#f5eae2", "skin"),
    "P": ("#f3c4be", "skin shade"),
    "U": ("#e09999", "blush"),
    "S": ("#b14551", "hair-tie red, mouth"),
    "V": ("#713444", "mouth inside"),
    "b": ("#91c880", "leek stalk pale green"),
    "I": ("#43a635", "leek green"),
    "X": ("#2f6d3a", "leek shadow green"),
    "O": ("#4c5a78", "outer outline slate (terminal)"),
    "Z": ("#3b4350", "ground shadow (terminal)"),
}

# study letter -> shared letter
MAP = {
    "A": "A", "H": "A", "G": "G", "O": "G", "C": "C", "J": "C",
    "B": "B", "F": "F",
    "L": "L", "R": "L", "N": "N", "Q": "N", "K": "K",
    "D": "D", "M": "M",
    "E": "E", "P": "P", "U": "U", "Y": "U", "a": "U",
    "S": "S", "V": "V", "T": "V",
    "I": "I", "Z": "I", "X": "X", "W": "X", "b": "b",
}
LIGHT = set("LNGbEP")


def neighbours(x, y, w, h):
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nx, ny = x + dx, y + dy
        if 0 <= nx < w and 0 <= ny < h:
            yield nx, ny, dx, dy


def strip_halo(g):
    """A light pixel on the outer edge whose neighbour toward her inside is the outline is
    anti-alias fringe: remove it. Repeat once for two-pixel fringes."""
    h, w = len(g), len(g[0])
    removed = 0
    for _ in range(2):
        kill = []
        for y in range(h):
            for x in range(w):
                c = g[y][x]
                if c == "." or c not in LIGHT:
                    continue
                # off-grid counts as background
                outer = []
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if not (0 <= nx < w and 0 <= ny < h) or g[ny][nx] == ".":
                        outer.append((nx, ny, dx, dy))
                if not outer:
                    continue
                for _, _, dx, dy in outer:
                    ix, iy = x - dx, y - dy
                    if 0 <= ix < w and 0 <= iy < h and g[iy][ix] in "BF":
                        kill.append((x, y))
                        break
        for x, y in kill:
            g[y][x] = "."
        removed += len(kill)
    return removed


HAIR_OR_LINE = set("GACBF")


def fix_specks(g):
    """A single off-material pixel (its colour matches none of its 4 neighbours) with at least
    3 neighbours of one hair or outline colour takes that colour. Face details (eye highlight,
    mouth) are surrounded by skin, so they are untouched."""
    h, w = len(g), len(g[0])
    fixed = 0
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            c = g[y][x]
            if c == "." or c in HAIR_OR_LINE or c in "SV":   # S/V: hair-tie stripes
                continue
            ns = [g[y + dy][x + dx] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
            if c in ns:
                continue
            best = max(set(ns), key=ns.count)
            if best in HAIR_OR_LINE and ns.count(best) >= 3:
                g[y][x] = best
                fixed += 1
    return fixed


def restore_outline(g):
    """On the outer edge, a grey pixel between background and hair is the navy outline that
    blended into the background: make it navy again."""
    h, w = len(g), len(g[0])
    fixed = []
    for y in range(h):
        for x in range(w):
            if g[y][x] not in "KMNLD":
                continue
            ns = []
            edge = False
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if not (0 <= nx < w and 0 <= ny < h) or g[ny][nx] == ".":
                    edge = True
                else:
                    ns.append(g[ny][nx])
            if edge and ns and all(c in "GACB" for c in ns) and any(c in "GAC" for c in ns):
                fixed.append((x, y, "B"))
            elif edge and ns and all(c == "B" for c in ns):
                fixed.append((x, y, "."))      # grey fringe outside the outline
    for x, y, c in fixed:
        g[y][x] = c
    return len(fixed)


def fix_stray_mouth(g):
    """Mouth colours (V, U) belong on the face. Away from skin they are noise: take the most
    common neighbouring colour."""
    h, w = len(g), len(g[0])
    fixed = 0
    for y in range(h):
        for x in range(w):
            if g[y][x] not in "VU":
                continue
            # near skin it's the mouth or blush; near hair-tie red it's the stripes' shading
            near = {g[yy][xx] for yy in range(max(0, y - 2), min(h, y + 3))
                    for xx in range(max(0, x - 2), min(w, x + 3))}
            if near & set("EPS"):
                continue
            ns = [g[y + dy][x + dx] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                  if 0 <= x + dx < w and 0 <= y + dy < h and g[y + dy][x + dx] not in ".VU"]
            if ns:
                g[y][x] = max(set(ns), key=ns.count)
                fixed += 1
    return fixed


def drop_islands(g, min_size=4):
    h, w = len(g), len(g[0])
    seen = set()
    dropped = 0
    sizes = []
    for y in range(h):
        for x in range(w):
            if g[y][x] == "." or (x, y) in seen:
                continue
            q, comp = deque([(x, y)]), []
            seen.add((x, y))
            while q:
                cx, cy = q.popleft()
                comp.append((cx, cy))
                for nx, ny, _, _ in neighbours(cx, cy, w, h):
                    if (nx, ny) not in seen and g[ny][nx] != ".":
                        seen.add((nx, ny))
                        q.append((nx, ny))
            sizes.append(comp)
    biggest = max(len(c) for c in sizes)
    for comp in sizes:
        if len(comp) < min_size and len(comp) < biggest:
            for x, y in comp:
                g[y][x] = "."
            dropped += len(comp)
    return dropped


def sole_row(g):
    """Lowest row with boot pixels (dark slate / outline)."""
    for y in range(len(g) - 1, -1, -1):
        if any(c in "BF" for c in g[y]):
            return y
    return len(g) - 1


def main():
    raw = json.loads((ROOT / ".wsl/poses_hi.json").read_text())
    mapped, cleaned, log = {}, {}, {}
    for name, rows in raw.items():
        g = [[MAP.get(c, c) if c != "." else "." for c in r] for r in rows]
        unknown = {c for r in g for c in r if c != "." and c not in PALETTE}
        assert not unknown, (name, unknown)
        mapped[name] = ["".join(r) for r in g]
        halo = strip_halo(g)
        specks = fix_specks(g)
        mouth = fix_stray_mouth(g)
        line = restore_outline(g)
        isl = drop_islands(g)
        cleaned[name] = g
        log[name] = {"halo_removed": halo, "specks_fixed": specks, "stray_mouth_fixed": mouth,
                     "outline_restored": line, "island_pixels_removed": isl}
    # shared canvas and baseline
    W = max(len(g[0]) for g in cleaned.values()) + 4
    above = max(sole_row(g) for g in cleaned.values()) + 2
    H = above + 4                      # 3 rows of ground shadow below the soles
    out = {}
    for name, g in cleaned.items():
        sole = sole_row(g)
        ox = (W - len(g[0])) // 2
        oy = above - 1 - sole
        canvas = [["."] * W for _ in range(H)]
        for y, r in enumerate(g):
            for x, c in enumerate(r):
                if c != "." and 0 <= y + oy < H:
                    canvas[y + oy][x + ox] = c
        # ground shadow: a flat ellipse centred under the feet
        feet = [x for x in range(W) if canvas[above - 1][x] in "BF"]
        cx = (min(feet) + max(feet)) // 2 if feet else W // 2
        for dy, half in ((0, 20), (1, 24), (2, 18)):
            y = above + dy
            for x in range(cx - half, cx + half + 1):
                if 0 <= x < W and canvas[y][x] == ".":
                    canvas[y][x] = "Z"
        out[name] = ["".join(r) for r in canvas]
        log[name].update({"offset": [ox, oy], "sole_row": above - 1})
    REF.mkdir(parents=True, exist_ok=True)
    (REF / "poses_raw.json").write_text(json.dumps(mapped, indent=0))
    (REF / "poses.json").write_text(json.dumps(out, indent=0))
    (REF / "poses_log.json").write_text(json.dumps(log, indent=1))
    (REF / "palette_v2.json").write_text(json.dumps(
        {k: {"hex": v[0], "name": v[1]} for k, v in PALETTE.items()}, indent=1))
    print(f"canvas {W} x {H}, baseline row {above - 1}")
    for k, v in log.items():
        print(k, v)


if __name__ == "__main__":
    main()
