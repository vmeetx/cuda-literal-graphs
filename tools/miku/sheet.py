"""Dev-only: render poses.json side by side (1x and Nx) with a baseline and height line."""
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT = Path(__file__).resolve().parents[2]
REF = ROOT / "tools/miku/ref"
F = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)

def palette():
    return {k: tuple(int(v["hex"][i:i + 2], 16) for i in (1, 3, 5))
            for k, v in json.loads((REF / "palette_v2.json").read_text()).items()}

def img(rows, pal, s, bg=(255, 255, 255)):
    h, w = len(rows), len(rows[0])
    im = Image.new("RGB", (w, h), bg)
    for y, r in enumerate(rows):
        for x, c in enumerate(r):
            if c != ".":
                im.putpixel((x, y), pal[c])
    return im.resize((w * s, h * s), Image.NEAREST)

def model_sheet(poses, out, scale=8, src=None, bg=(255, 255, 255)):
    pal = palette()
    names = list(poses)
    ims = [img(poses[n], pal, scale, bg) for n in names]
    w1 = [img(poses[n], pal, 1, bg) for n in names]
    pad = 16
    H = ims[0].height
    W = sum(i.width + pad for i in ims) + pad + 60
    top = 30
    extra = 0
    if src is not None:
        s = Image.open(src).convert("RGB")
        s = s.resize((W - 2 * pad, round(s.height * (W - 2 * pad) / s.width)), Image.LANCZOS)
        extra = s.height + 40
    sheet = Image.new("RGB", (W, top + H + 130 + extra), (236, 236, 236))
    d = ImageDraw.Draw(sheet)
    x = pad + 60
    for n, im, small in zip(names, ims, w1):
        d.text((x, 6), n, font=F, fill=(20, 20, 20))
        sheet.paste(im, (x, top))
        sheet.paste(small, (x, top + H + 20))
        x += im.width + pad
    rows = [r for n in names for r in poses[n]]
    first = min(next(y for y, r in enumerate(poses[n]) if any(c not in ".Z" for c in r)) for n in names)
    sole = max(max(y for y, r in enumerate(poses[n]) if any(c in "BF" for c in r)) for n in names)
    for yy, label in ((first, f"top {first}"), (sole + 1, "baseline")):
        y = top + yy * scale
        d.line([(50, y), (W - pad, y)], fill=(220, 40, 40), width=2)
        d.text((4, y - 8), label, font=F, fill=(220, 40, 40))
    d.text((4, top + H + 20), "1x", font=F, fill=(20, 20, 20))
    d.text((60, top + H + 100), f"height {sole + 1 - first} px between the lines; canvas {len(poses[names[0]][0])} x {len(poses[names[0]])}",
           font=F, fill=(20, 20, 20))
    if src is not None:
        sheet.paste(s, (pad, top + H + 130))
        d.text((pad, top + H + 130 + s.height + 8), "source sheet", font=F, fill=(20, 20, 20))
    sheet.save(out)

if __name__ == "__main__":
    poses = json.loads((REF / sys.argv[1]).read_text())
    model_sheet(poses, sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 8,
                sys.argv[4] if len(sys.argv) > 4 else None)
