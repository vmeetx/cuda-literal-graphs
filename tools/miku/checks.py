"""Dev-only: automatic checks for Miku sprite grids (palette, islands, outline, noise, stiffness).

Each check returns (name, value, ok, note). `report(grid)` runs them all.
Hard checks: palette, islands, outline gaps. Measures for cleanup: specks, checker,
doubled corners. Warnings for the critic: stiffness flags.
"""

from __future__ import annotations

import json
from collections import deque
from pathlib import Path

REF = Path(__file__).resolve().parent / "ref"
GROUPS = {"hair": "GAC", "top": "LNK", "skirt": "DMK", "skin": "EPU", "leek": "bIX",
          "sock": "F", "line": "BO", "mouth": "SV", "shadow": "Z"}
GROUP_OF = {}
for g, cs in GROUPS.items():
    for c in cs:
        GROUP_OF.setdefault(c, g)
CLOTH = set("LNKDMEPF")
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
N8 = N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))


def palette():
    return json.loads((REF / "palette_v2.json").read_text())


def at(g, x, y):
    if 0 <= y < len(g) and 0 <= x < len(g[0]):
        return g[y][x]
    return "."


def protected(g, x, y, face_rows=None):
    """Deliberate single-pixel detail: hair-tie stripes / mouth, outline-coloured detail
    (finger separations, eye lines), eye highlights, pleat lines."""
    c = g[y][x]
    if c in "SVB":
        return True
    if any(at(g, x + dx, y + dy) == c for dx, dy in ((1, 1), (1, -1), (-1, 1), (-1, -1))):
        return True                                     # part of a 1-px diagonal stroke
    if c in "UP" and any(at(g, x + dx, y + dy) == "E" for dx, dy in N4):
        return True                                     # blush on skin
    if c in "GLE" and face_rows and face_rows[0] <= y <= face_rows[1] and any(
            at(g, x + dx, y + dy) in "FC" for dx, dy in N8):
        return True                                     # eye highlight
    if c == "K" and any(at(g, x + dx, y + dy) == "K" for dx, dy in ((0, 1), (0, -1), (1, 1),
                                                                   (-1, 1), (1, -1), (-1, -1))):
        return True                                     # pleat line
    return False


def face_rows(g):
    """Rows of the face: from the first row with skin to 14 rows below it."""
    for y, r in enumerate(g):
        if sum(c in "EP" for c in r) >= 3:
            return (y, y + 14)
    return None


def specks(g):
    fr = face_rows(g)
    out = []
    for y in range(len(g)):
        for x in range(len(g[0])):
            c = g[y][x]
            if c in ".Z" or protected(g, x, y, fr):
                continue
            ns = [at(g, x + dx, y + dy) for dx, dy in N4]
            if "." in ns:
                continue
            if c not in ns:
                out.append((x, y))
    return out


def checker(g):
    """Material pixels with no same-colour 4-neighbour but a same-material one: mixing."""
    fr = face_rows(g)
    out = []
    for y in range(len(g)):
        for x in range(len(g[0])):
            c = g[y][x]
            grp = GROUP_OF.get(c)
            if grp in (None, "line", "mouth", "shadow", "sock") or protected(g, x, y, fr):
                continue
            ns = [at(g, x + dx, y + dy) for dx, dy in N4]
            if c in ns:
                continue
            if any(GROUP_OF.get(n) == grp for n in ns):
                out.append((x, y))
    return out


def outline_gaps(g):
    out = []
    for y in range(len(g)):
        for x in range(len(g[0])):
            c = g[y][x]
            if c in ".BOZF":
                continue
            if any(at(g, x + dx, y + dy) == "." for dx, dy in N4):
                out.append((x, y))
    return out


def doubled(g):
    """2x2 blocks of outline away from hair ties and eyes (where dark masses are drawn)."""
    out = []
    for y in range(len(g) - 1):
        for x in range(len(g[0]) - 1):
            if all(g[y + j][x + i] in "BO" for i in (0, 1) for j in (0, 1)):
                near = {at(g, x + dx, y + dy) for dx in range(-2, 4) for dy in range(-2, 4)}
                if not near & set("SVF"):
                    out.append((x, y))
    return out


def islands(g, min_size=4):
    seen, small = set(), []
    for y in range(len(g)):
        for x in range(len(g[0])):
            if g[y][x] in ".Z" or (x, y) in seen:
                continue
            q, comp = deque([(x, y)]), []
            seen.add((x, y))
            while q:
                cx, cy = q.popleft()
                comp.append((cx, cy))
                for dx, dy in N4:
                    nx, ny = cx + dx, cy + dy
                    if (nx, ny) not in seen and at(g, nx, ny) not in ".Z":
                        seen.add((nx, ny))
                        q.append((nx, ny))
            if len(comp) < min_size:
                small.append(comp)
    return small


def stiffness(g):
    h, w = len(g), len(g[0])
    runs = []
    for horiz in (True, False):
        outer, inner = (h, w) if horiz else (w, h)
        for a in range(outer):
            b = 0
            while b < inner:
                cell = (lambda k: g[a][k]) if horiz else (lambda k: g[k][a])
                if cell(b) == "B":
                    e = b
                    while e + 1 < inner and cell(e + 1) == "B":
                        e += 1
                    if e - b + 1 > 5:
                        side = []
                        for k in range(b, e + 1):
                            for o in (-1, 1):
                                side.append(at(g, k, a + o) if horiz else at(g, a + o, k))
                        if sum(c in CLOTH for c in side) > len(side) / 2:
                            runs.append(("h" if horiz else "v", a, b, e))
                    b = e + 1
                else:
                    b += 1
    top = [(x, y) for y, r in enumerate(g) for x, c in enumerate(r) if c in "LNK"]
    sym = 0.0
    if top:
        x0, x1 = min(x for x, _ in top), max(x for x, _ in top)
        y0, y1 = min(y for _, y in top), max(y for _, y in top)
        same = total = 0
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                total += 1
                same += g[y][x] == g[y][x1 - (x - x0)]
        sym = same / total
    return runs, sym


def report(g, name=""):
    pal = palette()
    off = {c for r in g for c in r if c != "." and c not in pal}
    sp, ch, gaps, dbl, isl = specks(g), checker(g), outline_gaps(g), doubled(g), islands(g)
    runs, sym = stiffness(g)
    res = [
        ("palette", len(off), not off, "colours outside the approved palette"),
        ("islands", len(isl), not isl, "detached pieces under 4 px"),
        ("outline_gaps", len(gaps), not gaps, "body pixels touching background with no outline"),
        ("specks", len(sp), None, "interior single pixels (deliberate detail excluded)"),
        ("checker", len(ch), None, "pixels mixed into another shade of their material"),
        ("doubled", len(dbl), None, "2x2 outline blocks away from ties and eyes"),
        ("stiff_runs", len(runs), None, "straight outline runs > 5 px on cloth/limbs (warning)"),
        ("torso_mirror", round(sym, 2), sym <= 0.85, "torso mirror similarity (warn above 0.85)"),
    ]
    return res


def fmt(res, name=""):
    lines = [f"{name}:"] if name else []
    for k, v, ok, note in res:
        tag = "" if ok is None else ("ok" if ok else "FAIL")
        lines.append(f"  {k:13s} {v!s:>6}  {tag:4s} {note}")
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    poses = json.loads((REF / (sys.argv[1] if len(sys.argv) > 1 else "poses.json")).read_text())
    for n, rows in poses.items():
        print(fmt(report([list(r) for r in rows]), n))
