"""Dev-only: old vs new cheerful walk at 1x, 8x and in a real terminal (dark and light)."""

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "tools"), str(ROOT / "tools/miku")]

import beforeafter  # noqa: E402
import sheet  # noqa: E402

OUT = ROOT / "findings/miku_v2/gate2c"
F = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)


def frames(path):
    return {f["drawing"]: f["grid"] for f in json.loads(Path(path).read_text())["frames"]}


def strip(rows_list, s):
    pal = sheet.palette()
    ims = [sheet.img(r, pal, s) for r in rows_list]
    out = Image.new("RGB", (sum(i.width + 6 for i in ims), ims[0].height), (236, 236, 236))
    x = 0
    for i in ims:
        out.paste(i, (x, 0))
        x += i.width + 6
    return out


def main(old_path, new_path):
    OUT.mkdir(parents=True, exist_ok=True)
    old, new = frames(old_path), frames(new_path)
    order = list(new)
    pal = sheet.palette()
    tiles = []
    for label, fr in (("OLD (GATE 2b)", old), ("NEW", new)):
        one = strip([fr[d] for d in order], 1)
        big = strip([fr[d] for d in ("contact_r", "pass_r")], 8)
        t, cols = beforeafter.terminal_text(fr["pass_r"], pal)
        n = len(t.splitlines())
        dark = beforeafter.shot(t, cols, n, (30, 30, 30), (210, 212, 216), OUT / f"{label[:3].lower()}_dark.png")
        light = beforeafter.shot(t, cols, n, (255, 255, 255), (20, 20, 20), OUT / f"{label[:3].lower()}_light.png")
        tiles.append((label, one, big, dark, light))
    W = max(t[2].width + t[3].width + t[4].width for t in tiles) + 80
    H = sum(max(t[1].height, 0) + t[2].height + 90 for t in tiles) + 20
    im = Image.new("RGB", (W, H), (236, 236, 236))
    d = ImageDraw.Draw(im)
    y = 10
    for label, one, big, dark, light in tiles:
        d.text((10, y), f"{label}: all 8 drawings at 1x, then contact and passing at 8x, then a "
               f"real terminal (passing, dark and light)", font=F, fill=(20, 20, 20))
        y += 24
        im.paste(one, (10, y))
        y += one.height + 10
        im.paste(big, (10, y))
        sc = big.height / dark.height
        dk = dark.resize((round(dark.width * sc), big.height))
        lt = light.resize((round(light.width * sc), big.height))
        im.paste(dk, (20 + big.width, y))
        im.paste(lt, (30 + big.width + dk.width, y))
        y += big.height + 30
    im.save(OUT / "old_vs_new.png")
    print("ok")


if __name__ == "__main__":
    main(*sys.argv[1:])
