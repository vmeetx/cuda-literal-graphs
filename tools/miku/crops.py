"""Dev-only: before/after crops for each reference correction (for MIKU_V2_REFERENCE.md)."""
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT = Path(__file__).resolve().parents[2]
REF = ROOT / "tools/miku/ref"
OUT = ROOT / "findings/miku_v2"
F = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)

def img(rows, pal, box, s=10):
    x0, y0, x1, y1 = box
    im = Image.new("RGB", ((x1 - x0) * s, (y1 - y0) * s), (255, 255, 255))
    d = ImageDraw.Draw(im)
    for y in range(y0, y1):
        for x in range(x0, x1):
            ch = rows[y][x] if 0 <= y < len(rows) and 0 <= x < len(rows[0]) else "."
            if ch != "." and ch in pal:
                hx = pal[ch]
                d.rectangle([(x - x0) * s, (y - y0) * s, (x - x0 + 1) * s - 1, (y - y0 + 1) * s - 1],
                            fill=tuple(int(hx[i:i + 2], 16) for i in (1, 3, 5)))
    return im

def pair(name, before, after, title):
    w = before.width + after.width + 60
    out = Image.new("RGB", (w, max(before.height, after.height) + 50), (255, 255, 255))
    d = ImageDraw.Draw(out)
    d.text((10, 8), title + "  (before | after)", font=F, fill=(20, 20, 20))
    out.paste(before, (10, 40)); out.paste(after, (before.width + 50, 40))
    out.save(OUT / f"fix_{name}.png")

raw = (ROOT / "findings/miku_v2/study/grid.txt").read_text().split()
rawpal = {k: v["hex"] for k, v in json.loads((ROOT / "findings/miku_v2/study/palette.json").read_text()).items()}
auto = (REF / "front_auto.txt").read_text().split()
autopal = json.loads((REF / "palette_auto.json").read_text())
fixed = (REF / "front.txt").read_text().split()
fixpal = {k: v["hex"] for k, v in json.loads((REF / "palette.json").read_text()).items()}
# raw grid coordinates are offset from the crop by (14, 12)
pair("strays", img(raw, rawpal, (0, 0, 95, 95), 4),
     img([("." * 14) + r for r in [("." * 66)] * 12 + fixed], fixpal, (0, 0, 95, 95), 4),
     "stray squares and bar removed")
pair("torso", img(auto, autopal, (20, 29, 46, 46)), img(fixed, fixpal, (20, 29, 46, 46)),
     "torso: collar, tie knot, top, bare arms")
pair("leek", img(auto, autopal, (4, 38, 52, 62)), img(fixed, fixpal, (4, 38, 52, 62)),
     "leek held in a visible hand, skirt and hem rebuilt")
pair("whites", img(auto, autopal, (12, 26, 46, 63), 8), img(fixed, fixpal, (12, 26, 46, 63), 8),
     "background gaps that read as white (between tail and body, between boots)")
print("ok")
