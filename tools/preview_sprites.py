"""Design-time (Pillow): print every sprite frame in the terminal and save PNGs.

Writes to assets/sprites/:
  <frame>.png           pixel map upscaled 16x on a checker background
  <frame>_term.png      the half-block terminal rendering of the frame
  <frame>_bob.png       terminal rendering with the 1-pixel idle bob, side by side
  onion_<a>_<b>.png     <a> at 30% opacity under <b>, 16x
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tools")]

from PIL import Image  # noqa: E402

import render_term  # noqa: E402
from cgviz import halfblock  # noqa: E402
from cgviz.sprites import FRAMES, PALETTE  # noqa: E402

OUT = ROOT / "assets/sprites"
ONION = [("idle_1", "walk_1"), ("walk_1", "walk_2"), ("walk_2", "walk_1"), ("idle_1", "victory_1"),
         ("portrait_idle", "portrait_victory")]


def to_image(frame, scale=16, checker=True):
    h, w = len(frame), len(frame[0])
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for y, row in enumerate(frame):
        for x, ch in enumerate(row):
            if ch != ".":
                im.putpixel((x, y), PALETTE[ch] + (255,))
    im = im.resize((w * scale, h * scale), Image.NEAREST)
    if not checker:
        return im
    bg = Image.new("RGBA", im.size, (60, 62, 70, 255))
    for y in range(0, im.size[1], scale):
        for x in range(0, im.size[0], scale):
            if (x // scale + y // scale) % 2:
                bg.paste((48, 50, 58, 255), (x, y, x + scale, y + scale))
    return Image.alpha_composite(bg, im)


def onion(a, b, scale=16):
    ia, ib = to_image(FRAMES[a], scale, False), to_image(FRAMES[b], scale, False)
    ga = ia.copy()
    ga.putalpha(ia.getchannel("A").point(lambda v: int(v * 0.3)))
    bg = Image.new("RGBA", ia.size, (60, 62, 70, 255))
    return Image.alpha_composite(Image.alpha_composite(bg, ga), ib)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fr in FRAMES.items():
        assert len({len(r) for r in fr}) == 1, name
        assert set("".join(fr)) <= set(PALETTE) | {"."}, name
        print(name, f"{len(fr[0])}x{len(fr)}")
        txt = halfblock.lines_plain(fr, PALETTE)
        print("\n".join(txt))
        to_image(fr).convert("RGB").save(OUT / f"{name}.png")
        render_term.render("\n".join(txt), str(OUT / f"{name}_term.png"), size=16)
        bob = halfblock.lines_plain(halfblock.shift(fr, 1), PALETTE)
        side = [a + "  " + b for a, b in zip(txt + [""], bob)]
        render_term.render("\n".join(side), str(OUT / f"{name}_bob.png"), size=16)
    for a, b in ONION:
        if a in FRAMES and b in FRAMES:
            onion(a, b).convert("RGB").save(OUT / f"onion_{a}_{b}.png")
    # contact sheet of the walker set plus its onion skins
    names = [n for n in ("idle_1", "walk_1", "walk_2", "victory_1") if n in FRAMES]
    ims = [to_image(FRAMES[n]) for n in names]
    ims += [onion(a, b) for a, b in ONION[:4] if a in FRAMES and b in FRAMES]
    sheet = Image.new("RGBA", (sum(i.width + 12 for i in ims), ims[0].height), (20, 20, 24, 255))
    x = 0
    for im in ims:
        sheet.paste(im, (x, 0))
        x += im.width + 12
    sheet.convert("RGB").save(OUT / "walker_sheet.png")


if __name__ == "__main__":
    main()
