"""Dev-only: GATE 1 images — reference vs extracted grid, outline-contrast test, and a real
terminal screenshot of the front frame standing on a node.

    python tools/miku/gate1.py [outer_hex] [shadow_hex]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "tools")]

import screenshot  # noqa: E402
from cgviz import halfblock  # noqa: E402

REF = ROOT / "tools/miku/ref"
OUT = ROOT / "findings/miku_v2"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
OUTER = {"navy (reference)": "#14172e", "slate": "#4c5a78", "light slate": "#8394b4"}
BGS = {"#1e1e1e": (30, 30, 30), "#000000": (0, 0, 0), "#ffffff": (255, 255, 255)}
SHADOW_ROWS_FROM = 62


def load():
    rows = (REF / "front.txt").read_text().split()
    pal = {k: v["hex"] for k, v in json.loads((REF / "palette.json").read_text()).items()}
    return rows, pal


def rgb(hx):
    return tuple(int(hx[i:i + 2], 16) for i in (1, 3, 5))


def terminal_variant(rows, outer="#4c5a78", shadow="#3b4350"):
    """Outer silhouette outline -> 'O'; ground shadow -> 'S'. Inner navy lines untouched."""
    g = [list(r) for r in rows]
    h, w = len(g), len(g[0])
    for y in range(h):
        for x in range(w):
            if y >= SHADOW_ROWS_FROM and g[y][x] == "C":
                g[y][x] = "S"
    for y in range(min(h, SHADOW_ROWS_FROM)):
        for x in range(w):
            if g[y][x] != "B":
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if not (0 <= nx < w and 0 <= ny < h) or rows[ny][nx] == "." or (
                        ny >= SHADOW_ROWS_FROM and rows[ny][nx] in "C."):
                    g[y][x] = "O"
                    break
    return ["".join(r) for r in g], {"O": outer, "S": shadow}


def image(rows, pal, scale=1, bg=None):
    h, w = len(rows), len(rows[0])
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0) if bg is None else bg + (255,))
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch != ".":
                im.putpixel((x, y), rgb(pal[ch]) + (255,))
    return im.resize((w * scale, h * scale), Image.NEAREST)


def label(im, text, size=18):
    f = ImageFont.truetype(FONT, size)
    out = Image.new("RGB", (im.width, im.height + size + 12), (255, 255, 255))
    out.paste(im.convert("RGB"), (0, size + 12))
    ImageDraw.Draw(out).text((6, 4), text, font=f, fill=(20, 20, 20))
    return out


def side_by_side(ims, gap=24, bg=(255, 255, 255)):
    h = max(i.height for i in ims)
    out = Image.new("RGB", (sum(i.width for i in ims) + gap * (len(ims) + 1), h + 2 * gap), bg)
    x = gap
    for i in ims:
        out.paste(i, (x, gap))
        x += i.width + gap
    return out


def main(outer="#4c5a78", shadow="#3b4350"):
    OUT.mkdir(parents=True, exist_ok=True)
    rows, pal = load()
    # 1. reference | grid 1x | grid 8x
    ref = Image.open(ROOT / "assets/reference/miku_ref.png").convert("RGB")
    grid8 = image(rows, pal, 8, (255, 255, 255))
    ref_s = ref.resize((round(ref.width * grid8.height / ref.height),) * 2, Image.LANCZOS)
    g1 = image(rows, pal, 1, (255, 255, 255))
    g1_box = Image.new("RGB", (max(g1.width, 160), grid8.height), (255, 255, 255))
    g1_box.paste(g1.convert("RGB"), (10, 10))
    side_by_side([label(ref_s, "reference (860x860)"),
                  label(g1_box, f"grid 1x ({len(rows[0])}x{len(rows)})"),
                  label(grid8, "grid 8x, corrected")]).save(OUT / "gate1_reference_vs_grid.png")
    # 2. outline contrast: 3 outer colours x 3 backgrounds
    tiles = []
    for name, hx in OUTER.items():
        trows, extra = terminal_variant(rows, hx, shadow)
        p2 = dict(pal, **extra)
        row_ims = [label(image(trows, p2, 4, bg), f"{name} on {bgname}", 14)
                   for bgname, bg in BGS.items()]
        tiles.append(side_by_side(row_ims, gap=12))
    sheet = Image.new("RGB", (max(t.width for t in tiles), sum(t.height for t in tiles)), "white")
    y = 0
    for t in tiles:
        sheet.paste(t, (0, y))
        y += t.height
    sheet.save(OUT / "gate1_outline_contrast.png")
    # 3. real terminal: half-block render of the terminal variant standing on a node box
    trows, extra = terminal_variant(rows, outer, shadow)
    p2 = {k: rgb(v) for k, v in dict(pal, **extra).items()}
    sprite = [r for r in trows[:SHADOW_ROWS_FROM]]      # body; shadow drawn as part of scene
    shadow_rows = trows[SHADOW_ROWS_FROM:]
    w = len(trows[0])
    cols = w + 30
    body = halfblock.cells(sprite, p2)
    sh = halfblock.cells(shadow_rows, p2)
    left = 15
    box_w = w + 8
    box_x = left - 4
    lines = []
    blank = [None] * cols
    grid = [list(blank) for _ in range(len(body) + len(sh) + 6)]
    for j, row in enumerate(body):
        for i, c in enumerate(row):
            if c:
                grid[j][left + i] = c
    for j, row in enumerate(sh):
        for i, c in enumerate(row):
            if c:
                grid[len(body) + j - 1][left + i] = grid[len(body) + j - 1][left + i] or c
    # the box top border sits right under her shadow: she stands on the node
    while sh and all(c is None for c in sh[-1]):
        sh.pop()
    top = len(body) + len(sh) - 1
    gemm = (80, 220, 255)
    title = " gemm1 "
    border = "┏" + "━" * (box_w - 2) + "┓"
    mid = "┃" + title.center(box_w - 2) + "┃"
    bot = "┗" + "━" * (box_w - 2) + "┛"
    for k, s in enumerate((border, mid, bot)):
        for i, ch in enumerate(s):
            if grid[top + k][box_x + i] is None or k > 0:
                grid[top + k][box_x + i] = (ch, gemm if ch not in title or k != 1 else (255, 255, 255), None)
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
    (OUT / "gate1_terminal.ans").write_text(text, encoding="utf-8")
    for name, bg in (("dark", (30, 30, 30)), ("light", (255, 255, 255))):
        screenshot.BG = bg
        screenshot.FG = (20, 20, 20) if name == "light" else (210, 212, 216)
        sc = screenshot.screen_of(text.encode(), cols, len(grid) + 2)
        screenshot.render(sc, str(OUT / f"gate1_terminal_{name}.png"))
    print("rows used by the sprite:", len(body), "terminal cols:", cols)


if __name__ == "__main__":
    main(*sys.argv[1:])
