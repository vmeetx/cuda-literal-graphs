"""Dev-only: crop the top of Miku's head from consecutive GIF frames into one strip, to see
flicker the way the viewer sees it.

    python tools/miku/gif_heads.py in.gif out.png first last [scale]
"""

import sys

from PIL import Image, ImageSequence


def main(src, out, first, last, scale=3):
    first, last, scale = int(first), int(last), int(scale)
    frames = [f.convert("RGB") for f in ImageSequence.Iterator(Image.open(src))]
    crops = []
    for k in range(first, min(last, len(frames))):
        im = frames[k]
        w, h = im.size
        px = im.load()
        bg = px[2, 2]
        xs = [x for x in range(0, w, 2) for y in range(40, 200, 4)
              if sum(abs(a - b) for a, b in zip(px[x, y], bg)) > 90]
        if not xs:
            continue
        cx = (min(xs) + max(xs)) // 2
        box = (max(cx - 110, 0), 0, min(cx + 110, w), 150)
        c = im.crop(box)
        crops.append(c.resize((c.width * scale, c.height * scale), Image.NEAREST))
    cols = 6
    cw, ch = max(c.width for c in crops), max(c.height for c in crops)
    rows = (len(crops) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (cw + 6), rows * (ch + 6)), (255, 0, 255))
    for i, c in enumerate(crops):
        sheet.paste(c, ((i % cols) * (cw + 6), (i // cols) * (ch + 6)))
    sheet.save(out)
    print(len(frames), "frames;", len(crops), "crops")


if __name__ == "__main__":
    main(*sys.argv[1:])
