"""Design-time: measure GEMM border contrast in the screenshot (not in the source colours).

Renders a preset through the real screenshot path, then compares the mean luminance of the
lit pixels in GEMM border cells against other kernel border cells.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "spike"), str(ROOT / "tools")]

from PIL import Image  # noqa: E402

import boxdraw  # noqa: E402
import screenshot  # noqa: E402
from gf_render import ROLES  # noqa: E402


def lum(p):
    r, g, b = p[:3]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def measure(preset, width=120, out="/tmp/contrast.png"):
    data = json.loads((ROOT / "tests/fixtures/graphs" / f"{preset}.json").read_text())
    lay, _, cn, _ = boxdraw.layout(data, ROLES.get(preset), width)
    sc = screenshot.screen_of(boxdraw.to_ansi(lay).encode(), width, 400)
    screenshot.render(sc, out, crop=False)
    g = screenshot.Glyphs(16)
    im = Image.open(out).convert("RGB")
    px = im.load()
    bg = screenshot.BG

    def cell_pixels(x, y):
        x0, y0 = g.cw + x * g.cw, g.ch + y * g.ch
        return [px[i, j] for i in range(x0, x0 + g.cw) for j in range(y0, y0 + g.ch)
                if sum(abs(a - b) for a, b in zip(px[i, j], bg)) > 60]

    def border(n):
        x0, y0, x1, y1 = lay.boxes[n]
        cells = [(x, y0) for x in range(x0, x1 + 1)] + [(x, y1) for x in range(x0, x1 + 1)]
        cells += [(x0, y) for y in range(y0 + 1, y1)] + [(x1, y) for y in range(y0 + 1, y1)]
        return cells

    stats = {}
    for key, pick in (("gemm", lambda nd: nd["op"] in ("gemm", "splitK")),
                      ("kernel", lambda nd: nd["kind"] == "kernel" and nd["op"] not in ("gemm", "splitK"))):
        lit, n_px = 0.0, 0
        ink = 0
        cells = 0
        for n, nd in cn.items():
            if not pick(nd):
                continue
            for xy in border(n):
                ps = cell_pixels(*xy)
                lit += sum(lum(p) for p in ps)
                n_px += len(ps)
                ink += len(ps)
                cells += 1
        stats[key] = dict(mean_lum=round(lit / max(n_px, 1), 1), ink_per_cell=round(ink / max(cells, 1), 1))
    stats["ratio_lum"] = round(stats["gemm"]["mean_lum"] / max(stats["kernel"]["mean_lum"], 1), 2)
    stats["ratio_ink"] = round(stats["gemm"]["ink_per_cell"] / max(stats["kernel"]["ink_per_cell"], 1), 2)
    return stats


if __name__ == "__main__":
    for p in sys.argv[1:] or ["decode", "prefill"]:
        print(p, measure(p))
