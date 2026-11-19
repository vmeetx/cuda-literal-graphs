"""Dev-only: thumbnail sheets (alternatives side by side at 1x and 8x)."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import sheet
F = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)

def thumb_sheet(items, out, scale=8, title="", pick=None, why=""):
    pal = sheet.palette()
    ims = [(k, note, sheet.img(rows, pal, scale), sheet.img(rows, pal, 1)) for k, note, rows in items]
    W = sum(i[2].width + 24 for i in ims) + 24
    H = max(i[2].height for i in ims) + 150
    im = Image.new("RGB", (W, H), (236, 236, 236))
    d = ImageDraw.Draw(im)
    d.text((24, 6), title, font=F, fill=(20, 20, 20))
    x = 24
    for k, note, big, small in ims:
        col = (200, 30, 30) if k == pick else (20, 20, 20)
        d.text((x, 30), f"{k}{'  (provisional pick)' if k == pick else ''}", font=F, fill=col)
        if k == pick:
            d.rectangle([x - 4, 52, x + big.width + 3, 56 + big.height], outline=(200, 30, 30), width=3)
        im.paste(big, (x, 54))
        im.paste(small, (x, 64 + big.height))
        d.text((x, 74 + big.height + small.height), note[:48], font=F, fill=(60, 60, 60))
        x += big.width + 24
    if why:
        d.text((24, H - 26), why, font=F, fill=(200, 30, 30))
    im.save(out)
