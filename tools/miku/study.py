"""Dev-only: study the reference image and recover its native pixel grid.

    python tools/miku/study.py assets/reference/miku_ref.png findings/miku_v2/study

1. Edge signal: colour change between neighbouring image pixels, summed per column / row.
2. Pitch + phase: for each candidate pitch (non-integer allowed) and phase, score how much
   edge energy falls on the predicted grid lines; take the best.
3. Sample the median colour of the central half of every cell.
4. Cluster the samples into a palette (merge colours closer than a threshold), map the
   background to transparent.
Writes: grid.txt (one letter per cell), palette.json, native_1x.png, zoom_8x.png,
swatch.png, silhouette.png, report.txt.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"


def edge_profile(a, axis):
    d = np.abs(np.diff(a.astype(np.int32), axis=axis)).sum(axis=2)
    return d.sum(axis=1 - axis if axis == 0 else 0) if False else d.sum(axis=0 if axis == 1 else 1)


def fit_grid(profile, lo=6.0, hi=12.0):
    n = len(profile)
    best = (-1, None, None)
    for p in np.arange(lo, hi, 0.01):
        for ph in np.arange(0, p, 0.25):
            idx = np.round(np.arange(ph, n, p)).astype(int)
            idx = idx[idx < n]
            s = profile[idx].sum() / len(idx)
            if s > best[0]:
                best = (s, p, ph)
    return best[1], best[2]


def sample(a, p, phx, phy):
    h, w = a.shape[:2]
    cols = int((w - phx) // p)
    rows = int((h - phy) // p)
    out = np.zeros((rows, cols, 3), dtype=np.uint8)
    for r in range(rows):
        for c in range(cols):
            x0, x1 = phx + c * p, phx + (c + 1) * p
            y0, y1 = phy + r * p, phy + (r + 1) * p
            q = (x1 - x0) / 4
            cell = a[int(y0 + q):int(np.ceil(y1 - q)), int(x0 + q):int(np.ceil(x1 - q))]
            out[r, c] = np.median(cell.reshape(-1, 3), axis=0)
    return out


def cluster(cells, thresh=34.0):
    """Greedy merge in RGB: big clusters first, nearby colours join them."""
    flat = cells.reshape(-1, 3).astype(float)
    uniq, counts = np.unique(flat, axis=0, return_counts=True)
    order = np.argsort(-counts)
    centres, weights = [], []
    for i in order:
        c = uniq[i]
        if centres:
            d = np.linalg.norm(np.array(centres) - c, axis=1)
            j = int(np.argmin(d))
            if d[j] < thresh:
                w = weights[j] + counts[i]
                centres[j] = (centres[j] * weights[j] + c * counts[i]) / w
                weights[j] = w
                continue
        centres.append(c.copy())
        weights.append(counts[i])
    centres = np.array(centres)
    d = np.linalg.norm(flat[:, None, :] - centres[None, :, :], axis=2)
    lab = d.argmin(axis=1).reshape(cells.shape[:2])
    return centres.round().astype(int), np.array(weights), lab


def main(src, out, thresh="34"):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    im = Image.open(src).convert("RGB")
    a = np.asarray(im)
    px = edge_profile(a, 1)
    py = edge_profile(a, 0)
    p1, phx = fit_grid(px)
    p2, phy = fit_grid(py)
    p = (p1 + p2) / 2
    cells = sample(a, p, phx, phy)
    centres, weights, lab = cluster(cells, float(thresh))
    # background = the brightest, most common near-white cluster
    bg = max(range(len(centres)), key=lambda k: (centres[k].sum() > 700, weights[k]))
    letters = {}
    k = 0
    for i in np.argsort(-weights):
        if i == bg:
            letters[i] = "."
        else:
            letters[i] = LETTERS[k]
            k += 1
    rows = ["".join(letters[v] for v in row) for row in lab]
    pal = {letters[i]: "#%02x%02x%02x" % tuple(centres[i]) for i in letters if letters[i] != "."}
    (out / "grid.txt").write_text("\n".join(rows) + "\n")
    (out / "palette.json").write_text(json.dumps(
        {k: {"hex": v, "count": int(weights[[i for i in letters if letters[i] == k][0]])}
         for k, v in pal.items()}, indent=1))
    h, w = lab.shape
    n1 = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sil = Image.new("RGB", (w, h), (255, 255, 255))
    for r in range(h):
        for c in range(w):
            ch = rows[r][c]
            if ch != ".":
                n1.putpixel((c, r), tuple(centres[lab[r, c]]) + (255,))
                sil.putpixel((c, r), (0, 0, 0))
    n1.save(out / "native_1x.png")
    n1.resize((w * 8, h * 8), Image.NEAREST).save(out / "zoom_8x.png")
    sil.resize((w * 4, h * 4), Image.NEAREST).save(out / "silhouette.png")
    sw = Image.new("RGB", (len(pal) * 40, 40), (255, 255, 255))
    for i, (k2, hx) in enumerate(pal.items()):
        sw.paste(tuple(int(hx[j:j + 2], 16) for j in (1, 3, 5)), (i * 40, 0, i * 40 + 38, 38))
    sw.save(out / "swatch.png")
    rep = [f"source {src} {im.size}", f"pitch x {p1:.3f} phase {phx:.2f}",
           f"pitch y {p2:.3f} phase {phy:.2f}", f"grid {w} x {h} cells",
           f"distinct source colours {len(np.unique(a.reshape(-1, 3), axis=0))}",
           f"palette {len(pal)} colours"] + [f"  {k2} {v}" for k2, v in pal.items()]
    (out / "report.txt").write_text("\n".join(rep) + "\n")
    print("\n".join(rep))
    print("\n".join(rows))


if __name__ == "__main__":
    main(*sys.argv[1:])
