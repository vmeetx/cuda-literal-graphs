"""Dev-only: before/after images for each GATE 2b fix, at 1x and 8x.

Before = the GATE 2 clips (commit 803e3c9, saved in .wsl/before/); after = the current clips.
Writes findings/miku_v2/gate2b/fix_NN.png.
"""

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "tools/miku")]

import sheet  # noqa: E402

OUT = ROOT / "findings/miku_v2/gate2b"
F = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
PAL = sheet.palette()


def clip(path):
    return json.loads(Path(path).read_text())


def frame(data, drawing):
    return next(f for f in data["frames"] if f["drawing"] == drawing)["grid"]


def crop(rows, box):
    x0, y0, x1, y1 = box
    return [r[x0:x1] for r in rows[y0:y1]]


def onion(prev, cur, s, bg=(255, 255, 255)):
    a = sheet.img(prev, PAL, s, bg).convert("RGBA")
    b = sheet.img(cur, PAL, s, bg).convert("RGBA")
    a.putalpha(77)
    base = Image.new("RGBA", a.size, bg + (255,))
    base.alpha_composite(a)
    mask = Image.new("L", b.size, 0)
    bp, mp = b.load(), mask.load()
    for y in range(b.height):
        for x in range(b.width):
            if bp[x, y][:3] != bg:
                mp[x, y] = 255
    base.paste(b, (0, 0), mask)
    return base.convert("RGB")


def panel(title, tiles, out):
    """tiles: list of (label, image)."""
    widths = [max(t.width, round(F.getlength(label)) + 8) for label, t in tiles]
    W = max(sum(w + 20 for w in widths) + 20, round(F.getlength(title)) + 40)
    H = max(t.height for _, t in tiles) + 70
    im = Image.new("RGB", (W, H), (236, 236, 236))
    d = ImageDraw.Draw(im)
    d.text((20, 6), title, font=F, fill=(20, 20, 20))
    x = 20
    for (label, t), w in zip(tiles, widths):
        d.text((x, 30), label, font=F, fill=(60, 60, 60))
        im.paste(t, (x, 52))
        x += w + 20
    im.save(out)


def pair(title, before, after, out, box=None, s=8):
    if box:
        before, after = crop(before, box), crop(after, box)
    tiles = [("before 1x", sheet.img(before, PAL, 1)), ("before 8x", sheet.img(before, PAL, s)),
             ("after 1x", sheet.img(after, PAL, 1)), ("after 8x", sheet.img(after, PAL, s))]
    panel(title, tiles, out)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    bw, aw = clip(ROOT / ".wsl/before/walk.json"), clip(ROOT / "cgviz/assets/miku/walk.json")
    bt, at = clip(ROOT / ".wsl/before/walk_tired.json"), clip(ROOT / "cgviz/assets/miku/walk_tired.json")
    full = (0, 0, 74, 72)
    pair("1. tails trail behind her: no tail pixel ahead of her front edge (walk, contact_r)",
         frame(bw, "contact_r"), frame(aw, "contact_r"), OUT / "fix_01.png", full, 5)
    pair("2. tails arc back and down from the tie, clear of her back, tips lag (walk, pass_r)",
         frame(bw, "pass_r"), frame(aw, "pass_r"), OUT / "fix_02.png", full, 5)
    pair("3. rounded crown and back, bangs sweep forward over the brow, near hair tie (head)",
         frame(bw, "contact_r"), frame(aw, "contact_r"), OUT / "fix_03.png", (0, 0, 60, 36))
    pair("4. far leg one shade darker than the near leg (walk, pass_r, legs)",
         frame(bw, "pass_r"), frame(aw, "pass_r"), OUT / "fix_04.png", (20, 50, 60, 72))
    # 5. the halo: onion-skin bleed (previous frame at 30%), not the outline treatment
    b0, b1 = frame(bw, "contact_r"), frame(bw, "down_r")
    a1 = frame(aw, "down_r")
    panel("5. the grey halo was the onion skin's 30% ghost of the previous frame; "
          "the frame itself is clean on white and dark",
          [("before: onion skin 1x", onion(b0, b1, 1)), ("before: onion skin 4x", onion(b0, b1, 4)),
           ("after: frame on white 4x", sheet.img(a1, PAL, 4)),
           ("after: frame on dark 4x", sheet.img(a1, PAL, 4, (30, 30, 30)))], OUT / "fix_05.png")
    # 6. the pale blob in frame 2 = ghost of the far arm swinging forward in frame 1
    panel("6. the pale blob in frame 2 was the onion ghost of frame 1's forward arm; "
          "that arm lobe is gone, no smear added",
          [("before: onion frame 2, 1x", onion(b0, b1, 1)), ("before: onion frame 2, 4x", onion(b0, b1, 4)),
           ("after: onion frame 2, 1x", onion(frame(aw, "contact_r"), a1, 1)),
           ("after: onion frame 2, 4x", onion(frame(aw, "contact_r"), a1, 4))], OUT / "fix_06.png")
    pair("7. bright open eye and an open, happy mouth in every frame (head)",
         frame(bw, "pass_r"), frame(aw, "pass_r"), OUT / "fix_07.png", (20, 0, 60, 36))
    pair("8. the leek spins in her leading hand instead of being strapped to her back (up_r)",
         frame(bw, "up_r"), frame(aw, "up_r"), OUT / "fix_08.png", full, 5)
    pair("9. tired walk keeps the closed line eyes, the droop and the dragged leek (contact_r)",
         frame(bt, "contact_r"), frame(at, "contact_r"), OUT / "fix_09.png", full, 5)
    pair("10. tired: near arm hangs limp in front (sleeve, cuff, hand); far arm drags the leek",
         frame(bt, "pass_r"), frame(at, "pass_r"), OUT / "fix_10.png", (18, 28, 60, 72))
    pair("11. tired: both tails hang heavily down and back, close to her, little sway",
         frame(bt, "up_r"), frame(at, "up_r"), OUT / "fix_11.png", full, 5)
    print("ok")


if __name__ == "__main__":
    main()
