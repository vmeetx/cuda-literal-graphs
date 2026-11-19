"""Dev-only: render a letter grid at 12x with a coordinate grid, for hand editing."""
import json, sys
from PIL import Image, ImageDraw, ImageFont
grid = open(sys.argv[1]).read().split()
pal = json.load(open(sys.argv[2]))
S = 12
h, w = len(grid), len(grid[0])
im = Image.new("RGB", (w * S + 30, h * S + 30), (255, 255, 255))
d = ImageDraw.Draw(im)
f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 9)
for y, row in enumerate(grid):
    for x, ch in enumerate(row):
        if ch != ".":
            hx = pal[ch]
            d.rectangle([30 + x * S, 30 + y * S, 30 + x * S + S - 1, 30 + y * S + S - 1],
                        fill=tuple(int(hx[i:i + 2], 16) for i in (1, 3, 5)))
for x in range(0, w + 1):
    d.line([30 + x * S, 30, 30 + x * S, 30 + h * S], fill=(200, 60, 60) if x % 5 == 0 else (225, 225, 225))
    if x % 5 == 0 and x < w:
        d.text((30 + x * S + 1, 2), str(x), font=f, fill=(200, 0, 0))
for y in range(0, h + 1):
    d.line([30, 30 + y * S, 30 + w * S, 30 + y * S], fill=(200, 60, 60) if y % 5 == 0 else (225, 225, 225))
    if y % 5 == 0 and y < h:
        d.text((2, 30 + y * S + 1), str(y), font=f, fill=(200, 0, 0))
im.save(sys.argv[3])
