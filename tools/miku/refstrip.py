"""Dev-only: reference strip of side-view walk cycles (CC0, study only) next to our walk, with a
vertical line through each figure's head centre (red) and hip centre (blue).

    python tools/miku/refstrip.py <refs_dir> <out.png> [walk.json ...]

Head centre = mean x of the figure's pixels in the top 28% of its height; hip centre = mean x
in the band 55-63% of its height (the same measure for every figure, ours included). The
offset (head - hip, toward the direction of travel) is printed under each frame, scaled to
our sprite height (67 px) so the numbers compare across sources.
"""

import json
import sys
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageSequence, ImageOps

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/miku"))
import sheet  # noqa: E402

F = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
H = 150   # display height per figure

# (label, file, crops as (x0, y0, x1, y1) or "gif", mirror to face right?, license note)
REFS = [
    ("r4t4: pixel girl walk", "r4t4.gif", "gif", False),
    ("Junko: chibi pixel girl, long hair", "junko_walking.png",
     [(41 * i, 43, 41 * i + 41, 86) for i in range(4)], True),
    ("Chibi walking bases (side frames)", "female_0.png",
     [(121 * i, 0, 121 * i + 121, 256) for i in range(4, 8)], False),
    ("Girl walking side", "walk.png", [(308 * i, 0, 308 * i + 308, 515) for i in range(0, 8, 2)], False),
    ("Cartoon female walk", "turn-around_16.png",
     [(10, 5, 125, 280), (130, 5, 225, 280), (225, 5, 320, 280), (325, 5, 420, 280)], True),
]


def frames_of(refs_dir, file, crops, mirror):
    im = Image.open(Path(refs_dir) / file)
    if crops == "gif":
        out = [f.convert("RGBA") for f in ImageSequence.Iterator(im)]
    else:
        im = im.convert("RGBA")
        out = [im.crop(c) for c in crops]
    return [ImageOps.mirror(f) if mirror else f for f in out]


def mask_of(im):
    px = im.load()
    w, h = im.size
    corners = [px[0, 0], px[w - 1, 0], px[0, h - 1], px[w - 1, h - 1]]
    bg = Counter(corners).most_common(1)[0][0]
    m = set()
    for y in range(h):
        for x in range(w):
            p = px[x, y]
            if p[3] > 40 and sum(abs(a - b) for a, b in zip(p[:3], bg[:3])) > 60:
                m.add((x, y))
    return m


def centres(m):
    ys = [y for _, y in m]
    y0, y1 = min(ys), max(ys)
    hgt = y1 - y0 + 1

    def cx(a, b):
        xs = [x for x, y in m if y0 + a * hgt <= y <= y0 + b * hgt]
        return sum(xs) / len(xs)

    return cx(0.0, 0.28), cx(0.55, 0.63), y0, y1


def annotate(im, m, scale_to=67):
    head, hip, y0, y1 = centres(m)
    s = H / im.height
    big = im.resize((max(1, round(im.width * s)), H), Image.NEAREST).convert("RGB")
    d = ImageDraw.Draw(big)
    d.line([(head * s, 0), (head * s, H)], fill=(230, 30, 30), width=2)
    d.line([(hip * s, 0), (hip * s, H)], fill=(30, 80, 230), width=2)
    off = (head - hip) * scale_to / (y1 - y0 + 1)
    return big, off


def row(label, ims_offs):
    W = sum(i.width + 8 for i, _ in ims_offs) + 8
    out = Image.new("RGB", (max(W, 260), H + 42), (236, 236, 236))
    d = ImageDraw.Draw(out)
    d.text((6, 2), label, font=F, fill=(20, 20, 20))
    x = 8
    for im, off in ims_offs:
        out.paste(im, (x, 20))
        d.text((x, H + 24), f"{off:+.1f}px", font=F, fill=(200, 30, 30) if off > 1.0 else (40, 40, 40))
        x += im.width + 8
    return out


def ours(path, label):
    """Our frames: head and hip centres come from the build (body only, no tails or leek)."""
    data = json.loads(Path(path).read_text())
    pal = sheet.palette()
    res = []
    for f in data["frames"]:
        rows = f["grid"]
        a = f["anchors"]
        im = sheet.img(rows, pal, 1, (255, 255, 255))
        s = H / im.height
        big = im.resize((round(im.width * s), H), Image.NEAREST)
        d = ImageDraw.Draw(big)
        d.line([(a["head_cx"] * s, 0), (a["head_cx"] * s, H)], fill=(230, 30, 30), width=2)
        d.line([(a["hip_cx"] * s, 0), (a["hip_cx"] * s, H)], fill=(30, 80, 230), width=2)
        res.append((big, a["head_cx"] - a["hip_cx"]))
    return row(label, res)


def main(refs_dir, out, *walks):
    rows_ = []
    for label, file, crops, mirror in REFS:
        fr = frames_of(refs_dir, file, crops, mirror)
        rows_.append(row(label + "  (CC0, study only)", [annotate(f, mask_of(f)) for f in fr]))
    for w in walks:
        p, label = w.split("=") if "=" in w else (w, Path(w).stem)
        rows_.append(ours(p, label))
    W = max(r.width for r in rows_)
    sheetim = Image.new("RGB", (W, sum(r.height for r in rows_) + 40), (236, 236, 236))
    d = ImageDraw.Draw(sheetim)
    d.text((8, 8), "red = head centre, blue = hip centre; number = head - hip toward travel, "
           "scaled to a 67 px figure (red when over +1)", font=F, fill=(20, 20, 20))
    y = 34
    for r in rows_:
        sheetim.paste(r, (0, y))
        y += r.height
    sheetim.save(out)


if __name__ == "__main__":
    main(*sys.argv[1:])
