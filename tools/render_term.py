"""Design-time only (Pillow): render 24-bit ANSI terminal text to a PNG.

Half blocks (▀ ▄ █) are painted as rectangles so they never depend on the font.
"""

from __future__ import annotations

import re
import sys

from PIL import Image, ImageDraw, ImageFont

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
SGR = re.compile(r"\x1b\[([0-9;]*)m")


def parse(text):
    rows = []
    for line in text.split("\n"):
        fg = bg = None
        row, i = [], 0
        while i < len(line):
            m = SGR.match(line, i)
            if m:
                ps = [int(p) for p in m.group(1).split(";") if p] or [0]
                j = 0
                while j < len(ps):
                    if ps[j] == 0:
                        fg = bg = None
                    elif ps[j] == 38 and ps[j + 1] == 2:
                        fg = tuple(ps[j + 2:j + 5]); j += 4
                    elif ps[j] == 48 and ps[j + 1] == 2:
                        bg = tuple(ps[j + 2:j + 5]); j += 4
                    elif ps[j] == 39:
                        fg = None
                    elif ps[j] == 49:
                        bg = None
                    j += 1
                i = m.end()
                continue
            row.append((line[i], fg, bg))
            i += 1
        rows.append(row)
    return rows


def render(text, path, size=16, bg=(18, 20, 24), fg=(220, 220, 220), scale=1):
    font = ImageFont.truetype(FONT, size)
    cw = round(font.getlength("M"))
    ch = int(size * 1.25)
    rows = parse(text)
    W = max((len(r) for r in rows), default=1) * cw + 2 * cw
    H = len(rows) * ch + 2 * ch
    im = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(im)
    for y, row in enumerate(rows):
        for x, (c, f, b) in enumerate(row):
            px, py = cw + x * cw, ch + y * ch
            if b:
                d.rectangle([px, py, px + cw - 1, py + ch - 1], fill=b)
            col = f or fg
            if c == "▀":
                d.rectangle([px, py, px + cw - 1, py + ch // 2 - 1], fill=col)
            elif c == "▄":
                d.rectangle([px, py + ch // 2, px + cw - 1, py + ch - 1], fill=col)
            elif c == "█":
                d.rectangle([px, py, px + cw - 1, py + ch - 1], fill=col)
            elif 0x2801 <= ord(c) <= 0x28FF:
                bits = ord(c) - 0x2800
                order = [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (0, 3), (1, 3)]
                r = max(1, cw // 5)
                for k, (bx, by) in enumerate(order):
                    if bits >> k & 1:
                        ox = px + cw * (1 + 2 * bx) // 4
                        oy = py + ch * (1 + 2 * by) // 8
                        d.ellipse([ox - r, oy - r, ox + r, oy + r], fill=col)
            elif c != " ":
                d.text((px, py), c, font=font, fill=col)
    if scale != 1:
        im = im.resize((W * scale, H * scale), Image.NEAREST)
    im.save(path)
    return path


if __name__ == "__main__":
    render(open(sys.argv[1], encoding="utf-8").read(), sys.argv[2])
