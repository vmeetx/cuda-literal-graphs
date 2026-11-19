"""Dev-only: GATE 1 (redo) images from the cleaned six-pose model.

Writes to findings/miku_v2/:
  gate1b_model_sheet.png      six poses at 8x and 1x on one baseline with a height line,
                              above the source sheet
  gate1b_p1_terminal_{dark,light}.png   P1 standing on a node (pyte screenshot)
  gate1b_fix_P{n}.png         per pose: raw resample | changed pixels | cleaned
  gate1b_faces.png            the six faces on one strip
  gate1b_stiffness.txt        the automatic stiffness flags
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "tools"), str(ROOT / "tools/miku")]

import screenshot  # noqa: E402
import sheet  # noqa: E402
from cgviz import halfblock  # noqa: E402

REF = ROOT / "tools/miku/ref"
OUT = ROOT / "findings/miku_v2"
F = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
FACE_NAMES = {"P1": "smile", "P2": "wink", "P3": "smug", "P4": "squeezed shut",
              "P5": "excited", "P6": "sleepy"}
CLOTH = set("LNKDMEPF")


def terminal_variant(rows):
    """Outer silhouette outline (navy touching background) -> slate O."""
    g = [list(r) for r in rows]
    h, w = len(g), len(g[0])
    for y in range(h):
        for x in range(w):
            if g[y][x] != "B":
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if not (0 <= nx < w and 0 <= ny < h) or rows[ny][nx] in ".Z":
                    g[y][x] = "O"
                    break
    return ["".join(r) for r in g]


def p1_on_node(rows, pal):
    rgb = {k: v for k, v in pal.items()}
    body = [r for r in rows if True]
    sole = max(y for y, r in enumerate(rows) if any(c in "BFO" for c in r))
    cells = halfblock.cells(body[: sole + 1], rgb)
    shadow = halfblock.cells(body[sole + 1:], rgb)
    while shadow and all(c is None for c in shadow[-1]):
        shadow.pop()
    w = len(rows[0])
    cols, left = w + 24, 12
    grid = [[None] * cols for _ in range(len(cells) + len(shadow) + 4)]
    for j, row in enumerate(cells + shadow):
        for i, c in enumerate(row):
            if c:
                grid[j][left + i] = c
    top = len(cells) + len(shadow)
    box_w, bx = w - 6, left + 3
    gemm = (80, 220, 255)
    for k, s in enumerate(("┏" + "━" * (box_w - 2) + "┓", "┃" + " gemm1 ".center(box_w - 2) + "┃",
                           "┗" + "━" * (box_w - 2) + "┛")):
        for i, ch in enumerate(s):
            grid[top + k][bx + i] = (ch, (255, 255, 255) if (k == 1 and ch not in "┃ ") else gemm, None)
    lines = []
    for row in grid:
        s = []
        for c in row:
            if c is None:
                s.append("\x1b[0m ")
            else:
                ch, fg, bg = c
                s.append("\x1b[0m\x1b[38;2;%d;%d;%dm" % fg + ("\x1b[48;2;%d;%d;%dm" % bg if bg else "") + ch)
        lines.append("".join(s) + "\x1b[0m")
    text = "\n".join(lines)
    for name, bg, fg in (("dark", (30, 30, 30), (210, 212, 216)), ("light", (255, 255, 255), (20, 20, 20))):
        screenshot.BG, screenshot.FG = bg, fg
        sc = screenshot.screen_of(text.encode(), cols, len(grid) + 2)
        screenshot.render(sc, str(OUT / f"gate1b_p1_terminal_{name}.png"))
    return len(cells)


def fix_views(raw, raw_pal, clean, clean_pal, name, s=5):
    """raw resample (study colours) | changed pixels in red | cleaned. Same alignment."""
    log = json.loads((REF / "poses_log.json").read_text())[name]
    ox, oy = log["offset"]
    h, w = len(clean), len(clean[0])
    A = Image.new("RGB", (w, h), (255, 255, 255))
    Bm = Image.new("RGB", (w, h), (255, 255, 255))
    C = Image.new("RGB", (w, h), (255, 255, 255))
    for y in range(h):
        for x in range(w):
            ry, rx = y - oy, x - ox
            r = raw[ry][rx] if 0 <= ry < len(raw) and 0 <= rx < len(raw[0]) else "."
            c = clean[y][x]
            if r != ".":
                A.putpixel((x, y), raw_pal[r])
            if c != ".":
                C.putpixel((x, y), clean_pal[c])
            mapped = sheet_map(r)
            if c != "Z" and mapped != c:
                Bm.putpixel((x, y), (230, 40, 40))
            elif c not in ".Z":
                Bm.putpixel((x, y), (215, 215, 215))
    ims = [i.resize((w * s, h * s), Image.NEAREST) for i in (A, Bm, C)]
    out = Image.new("RGB", (sum(i.width for i in ims) + 80, ims[0].height + 40), (240, 240, 240))
    d = ImageDraw.Draw(out)
    x = 20
    for im, t in zip(ims, ("raw resample", "changed pixels (red)", "cleaned")):
        d.text((x, 8), t, font=F, fill=(20, 20, 20))
        out.paste(im, (x, 32))
        x += im.width + 20
    out.save(OUT / f"gate1b_fix_{name}.png")


MAP = None


def sheet_map(c):
    if c == ".":
        return "."
    return MAP.get(c, c)


def face_crop(rows, w=24, h=17):
    """A fixed window centred on the skin of the face (the top rows of skin, where hands
    raised beside the head are a minority)."""
    pts = [(x, y) for y, r in enumerate(rows) for x, c in enumerate(r) if c in "EPU"]
    counts = {}
    for _, y in pts:
        counts[y] = counts.get(y, 0) + 1
    y_first = min(counts)
    cy = max((y for y in counts if y <= y_first + 30), key=lambda y: counts[y])  # widest face row
    face = [(x, y) for x, y in pts if abs(y - cy) <= 4]
    xs = sorted(x for x, _ in face)
    cx = xs[len(xs) // 2]                      # median: robust to a hand at one side
    return cx - w // 2, cy - 11, cx + w // 2, cy - 11 + h          # eyes to chin


def faces(poses, pal, s=8):
    ims = []
    for n, rows in poses.items():
        x0, y0, x1, y1 = face_crop(rows)
        im = sheet.img([r[x0:x1] for r in rows[y0:y1]], pal, s)
        lab = Image.new("RGB", (im.width, im.height + 26), (240, 240, 240))
        lab.paste(im, (0, 26))
        ImageDraw.Draw(lab).text((4, 4), f"{n} {FACE_NAMES[n]}", font=F, fill=(20, 20, 20))
        ims.append(lab)
    out = Image.new("RGB", (sum(i.width + 16 for i in ims) + 16, max(i.height for i in ims) + 32),
                    (240, 240, 240))
    x = 16
    for im in ims:
        out.paste(im, (x, 16))
        x += im.width + 16
    out.save(OUT / "gate1b_faces.png")


def stiffness(poses):
    """Warnings, not failures: long straight outline runs on limbs/clothing, and mirror
    similarity of the torso."""
    lines = []
    for n, rows in poses.items():
        h, w = len(rows), len(rows[0])
        runs = []
        for y in range(h):
            x = 0
            while x < w:
                if rows[y][x] == "B":
                    x2 = x
                    while x2 + 1 < w and rows[y][x2 + 1] == "B":
                        x2 += 1
                    if x2 - x + 1 > 5:
                        side = [rows[yy][xx] for xx in range(x, x2 + 1) for yy in (y - 1, y + 1)
                                if 0 <= yy < h]
                        if sum(c in CLOTH for c in side) > len(side) / 2:
                            runs.append(f"h y{y} x{x}-{x2}")
                    x = x2 + 1
                else:
                    x += 1
        for x in range(w):
            y = 0
            while y < h:
                if rows[y][x] == "B":
                    y2 = y
                    while y2 + 1 < h and rows[y2 + 1][x] == "B":
                        y2 += 1
                    if y2 - y + 1 > 5:
                        side = [rows[yy][xx] for yy in range(y, y2 + 1) for xx in (x - 1, x + 1)
                                if 0 <= xx < w]
                        if sum(c in CLOTH for c in side) > len(side) / 2:
                            runs.append(f"v x{x} y{y}-{y2}")
                    y = y2 + 1
                else:
                    y += 1
        top = [(x, y) for y, r in enumerate(rows) for x, c in enumerate(r) if c in "LNK"]
        if top:
            x0 = min(x for x, _ in top)
            x1 = max(x for x, _ in top)
            y0 = min(y for _, y in top)
            y1 = max(y for _, y in top)
            same = total = 0
            for y in range(y0, y1 + 1):
                for x in range(x0, x1 + 1):
                    m = x1 - (x - x0)
                    total += 1
                    same += rows[y][x] == rows[y][m]
            sym = same / total
        else:
            sym = 0
        flag = "FLAG" if sym > 0.85 else "ok"
        lines.append(f"{n}: torso mirror similarity {sym:.2f} ({flag}); "
                     f"straight cloth/limb outline runs > 5 px: {len(runs)} "
                     f"{'(' + ', '.join(runs) + ')' if runs else ''}")
    (OUT / "gate1b_stiffness.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


def main():
    global MAP
    import poses_clean
    MAP = poses_clean.MAP
    poses = json.loads((REF / "poses.json").read_text())
    pal = sheet.palette()
    sheet.model_sheet(poses, OUT / "gate1b_model_sheet.png", 8, ROOT / "assets/reference/miku_poses.png")
    p1 = terminal_variant(poses["P1"])
    rows_used = p1_on_node(p1, pal)
    raw = json.loads((ROOT / ".wsl/poses_hi.json").read_text())
    raw_pal = {k: tuple(int(v["hex"][i:i + 2], 16) for i in (1, 3, 5)) for k, v in
               json.loads((ROOT / "findings/miku_v2/study_poses_hi/palette.json").read_text()).items()}
    for n in poses:
        fix_views(raw[n], raw_pal, poses[n], pal, n)
    faces(poses, pal)
    stiffness(poses)
    print("P1 body rows in terminal:", rows_used)


if __name__ == "__main__":
    main()
