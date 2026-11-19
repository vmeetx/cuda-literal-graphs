"""Dev-only: interior cleanup of a pose (in-between colours left by resampling).

    python tools/miku/interior.py P1

Edits the pose in place in poses.json (the previous version is kept in poses_prev.json):
1. specks: an interior single pixel unlike its 4 neighbours joins the most common neighbour
   colour, unless it is deliberate detail (eye highlight, outline-coloured detail such as
   finger separations, hair-tie stripes, pleat lines).
2. clusters: a material pixel with at most one same-colour 8-neighbour, surrounded mostly by
   one other shade of the same material, takes that shade (removes checkerboard mixing).
3. doubled outline: an outline pixel that is the inner layer of a two-thick outline (it has
   outline on its outward side and only body colour inward) becomes the inward colour.
4. outline gaps: a body pixel touching the background becomes outline.
Pose, gesture and folds stay: only isolated pixels change.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import checks  # noqa: E402

REF = HERE / "ref"
N4, N8, at = checks.N4, checks.N8, checks.at


def majority(cs):
    cs = [c for c in cs if c not in ".Z"]
    return max(set(cs), key=cs.count) if cs else None


def fix_specks(g):
    n = 0
    for x, y in checks.specks(g):
        m = majority([at(g, x + dx, y + dy) for dx, dy in N4])
        if m:
            g[y][x] = m
            n += 1
    return n


def fix_clusters(g):
    fr = checks.face_rows(g)
    changes = []
    for y in range(len(g)):
        for x in range(len(g[0])):
            c = g[y][x]
            grp = checks.GROUP_OF.get(c)
            if grp in (None, "line", "mouth", "shadow", "sock") or checks.protected(g, x, y, fr):
                continue
            n8 = [at(g, x + dx, y + dy) for dx, dy in N8]
            if "." in n8 or n8.count(c) > 1:
                continue
            same_mat = [k for k in n8 if checks.GROUP_OF.get(k) == grp and k != c]
            if len(same_mat) >= 4:
                changes.append((x, y, majority(same_mat)))
    for x, y, m in changes:
        g[y][x] = m
    return len(changes)


def fix_doubled(g):
    changes = []
    for y in range(len(g)):
        for x in range(len(g[0])):
            if g[y][x] != "B":
                continue
            if any(at(g, x + dx, y + dy) == "." for dx, dy in N4):
                continue                          # outer layer: keep
            near = {at(g, x + dx, y + dy) for dx in range(-2, 3) for dy in range(-2, 3)}
            if near & set("SVF") or checks.face_rows(g) and \
                    checks.face_rows(g)[0] - 2 <= y <= checks.face_rows(g)[1]:
                continue                          # ties, eyes, face lines: keep
            for dx, dy in N4:
                out1 = at(g, x + dx, y + dy)
                out2 = at(g, x + 2 * dx, y + 2 * dy)
                inward = at(g, x - dx, y - dy)
                if out1 == "B" and out2 == "." and inward not in ".BOZ":
                    others = [at(g, x + ex, y + ey) for ex, ey in N4 if (ex, ey) != (dx, dy)]
                    if sum(o == "B" for o in others) <= 1:
                        changes.append((x, y, inward))
                    break
    for x, y, c in changes:
        g[y][x] = c
    return len(changes)


def fix_gaps(g):
    """A body pixel touching the background: if the outline already runs just inside it, the
    pixel pokes outside the silhouette and is removed; otherwise it becomes outline."""
    gaps = checks.outline_gaps(g)
    changes = []
    for x, y in gaps:
        outside_line = False
        for dx, dy in N4:
            if at(g, x + dx, y + dy) == "." and at(g, x - dx, y - dy) in "BO":
                outside_line = True
        changes.append((x, y, "." if outside_line else "B"))
    for x, y, c in changes:
        g[y][x] = c
    return len(gaps)


def main(name="P1"):
    poses = json.loads((REF / "poses.json").read_text())
    prev = REF / "poses_prev.json"
    if not prev.exists():
        prev.write_text(json.dumps(poses, indent=0))
    g = [list(r) for r in json.loads(prev.read_text())[name]]   # always from the pre-cleanup pose
    before = checks.report(g)
    log = {"specks": fix_specks(g), "clusters": fix_clusters(g)}
    log["clusters_2"] = fix_clusters(g)
    log["specks_2"] = fix_specks(g)
    log["gaps"] = log["doubled"] = 0
    for _ in range(4):                    # removing a stray edge pixel can expose a new edge
        log["gaps"] += fix_gaps(g)
        log["doubled"] += fix_doubled(g)
    log["gaps"] += fix_gaps(g)
    after = checks.report(g)
    poses[name] = ["".join(r) for r in g]
    (REF / "poses.json").write_text(json.dumps(poses, indent=0))
    print(name, log)
    print(checks.fmt(before, "before"))
    print(checks.fmt(after, "after"))


if __name__ == "__main__":
    main(*sys.argv[1:])
