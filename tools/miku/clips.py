"""Dev-only: build clips from the exposure sheets into runtime data, plus review sheets.

    python tools/miku/clips.py [outdir]

Writes cgviz/assets/miku/<clip>.json (palette-indexed grids, ticks per frame, anchors) for
walk, walk_tired, turn_to_side, turn_to_front, and findings images: contact sheets with tick
counts, onion skins, and the turnaround sheet. Uses the provisional thumbnail picks
(side face A, passing pose D: lean 1, higher swing kick, stronger skirt lag, tail swing).
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

from PIL import Image, ImageDraw, ImageFont  # noqa: E402

import sheet  # noqa: E402
import side_body  # noqa: E402
import xsheet  # noqa: E402

ASSETS = ROOT / "cgviz/assets/miku"
F = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
SIDE_FACE = "A"
PASS_PICK = "D"


def palette_hex():
    return {k: v["hex"] for k, v in json.loads((HERE / "ref/palette_v2.json").read_text()).items()}


def p1():
    return json.loads((HERE / "ref/poses.json").read_text())["P1"]


def walk_frames(tired=False):
    xs = xsheet.load("walk_tired" if tired else "walk")
    period = xs["ticks"]
    out, t = [], 0
    pick = side_body.PASS_ALTS[PASS_PICK]
    for f in xs["frames"]:
        d = f["drawing"]
        # tails lag one tick: their swing is driven by the phase of the previous tick
        swing = 0.3 * math.sin(2 * math.pi * (t - 1) / period)
        # trailing lag: strongest on the contact keys (body decelerating forward), least on passing
        lag = {"contact": 2.4, "down": 1.8, "pass": 0.8, "up": 1.2}[d.split("_")[0]]
        kw = dict(head=SIDE_FACE, lag_prev=lag, swing=swing, tired=tired, lean=pick.get("lean", 0))
        if d.startswith("pass") and not tired:
            front, back, near, bob, slag = side_body.WALK[d]
            side_body.WALK["_pass"] = (front, pick.get("back", back), near, bob, pick.get("slag", slag))
            rows, meta = side_body.pose_side("_pass", **kw)
            meta["drawing"] = d
        else:
            rows, meta = side_body.pose_side(d, **kw)
        out.append({"drawing": d, "ticks": f["ticks"], "key": f.get("key", False),
                    "grid": rows, "anchors": meta})
        t += f["ticks"]
    return xs, out


def turn_frames(name):
    xs = xsheet.load(name)
    out = []
    for f in xs["frames"]:
        d = f["drawing"]
        if d == "front":
            rows, meta = p1(), {"view": "front", "facing": "front", "drawing": "front"}
        else:
            rows, meta = side_body.pose_side(d, head=SIDE_FACE, swing=f.get("swing", 0.0))
        out.append({"drawing": d, "ticks": f["ticks"], "key": f.get("key", False),
                    "grid": rows, "anchors": meta})
    return xs, out


def save_clip(name, xs, frames):
    ASSETS.mkdir(parents=True, exist_ok=True)
    data = {"clip": name, "fps": 12, "loop": xs.get("loop", False), "view": xs.get("view"),
            "faces": "right", "mirror_for_left": True, "baseline": 67,
            "palette": palette_hex(), "ticks": sum(f["ticks"] for f in frames), "frames": frames}
    (ASSETS / f"{name}.json").write_text(json.dumps(data, separators=(",", ":")))
    return data


def contact_sheet(name, frames, out, scale=3):
    pal = sheet.palette()
    ims = [sheet.img(f["grid"], pal, scale) for f in frames]
    W = sum(i.width + 10 for i in ims) + 10
    im = Image.new("RGB", (W, ims[0].height + 60), (236, 236, 236))
    d = ImageDraw.Draw(im)
    d.text((10, 4), f"{name}: {len(frames)} drawings, {sum(f['ticks'] for f in frames)} ticks",
           font=F, fill=(20, 20, 20))
    x = 10
    for f, i in zip(frames, ims):
        im.paste(i, (x, 24))
        d.text((x, 28 + i.height), f"{f['drawing']} ×{f['ticks']}{' key' if f['key'] else ''}",
               font=F, fill=(200, 30, 30) if f["key"] else (40, 40, 40))
        x += i.width + 10
    im.save(out)


def onion(frames, out, scale=3):
    pal = sheet.palette()
    tiles = []
    for k, f in enumerate(frames):
        prev = frames[k - 1]["grid"]
        a = sheet.img(prev, pal, scale).convert("RGBA")
        b = sheet.img(f["grid"], pal, scale).convert("RGBA")
        a.putalpha(77)
        base = Image.new("RGBA", a.size, (255, 255, 255, 255))
        base.alpha_composite(a)
        mask = Image.new("L", b.size, 0)
        bp = b.load()
        mp = mask.load()
        for y in range(b.height):
            for x in range(b.width):
                if bp[x, y][:3] != (255, 255, 255):
                    mp[x, y] = 255
        base.paste(b, (0, 0), mask)
        tiles.append(base.convert("RGB"))
    W = sum(t.width + 8 for t in tiles) + 8
    im = Image.new("RGB", (W, tiles[0].height + 16), (236, 236, 236))
    x = 8
    for t in tiles:
        im.paste(t, (x, 8))
        x += t.width + 8
    im.save(out)


def turnaround(out):
    pal = sheet.palette()
    front = p1()
    q, _ = side_body.pose_side("three_quarter", head=SIDE_FACE)
    sd, _ = side_body.pose_side("side_stand", head=SIDE_FACE)
    mirror = lambda rows: [r[::-1] for r in rows]
    views = [("front (P1)", front), ("3/4 right", q), ("side right", sd),
             ("side left", mirror(sd)), ("3/4 left", mirror(q))]
    s = 5
    ims = [(n, sheet.img(r, pal, s)) for n, r in views]
    W = sum(i.width + 20 for _, i in ims) + 80
    H = ims[0][1].height + 60
    src = Image.open(ROOT / "assets/reference/miku_poses.png").convert("RGB")
    src = src.resize((W - 40, round(src.height * (W - 40) / src.width)))
    sheetim = Image.new("RGB", (W, H + src.height + 40), (236, 236, 236))
    d = ImageDraw.Draw(sheetim)
    x = 60
    for n, i in ims:
        d.text((x, 6), n, font=F, fill=(20, 20, 20))
        sheetim.paste(i, (x, 30))
        x += i.width + 20
    top = min(next(y for y, r in enumerate(v) if any(c not in ".Z" for c in r)) for _, v in views)
    for yy, label in ((top, "top"), (68, "baseline")):
        y = 30 + yy * s
        d.line([(50, y), (W - 10, y)], fill=(220, 40, 40), width=2)
        d.text((4, y - 8), label, font=F, fill=(220, 40, 40))
    sheetim.paste(src, (20, H + 20))
    sheetim.save(out)


def main(outdir=str(ROOT / "findings/miku_v2/gate2")):
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    built = {}
    for name, fn in (("walk", lambda: walk_frames(False)), ("walk_tired", lambda: walk_frames(True)),
                     ("turn_to_side", lambda: turn_frames("turn_to_side")),
                     ("turn_to_front", lambda: turn_frames("turn_to_front"))):
        xs, frames = fn()
        save_clip(name, xs, frames)
        contact_sheet(name, frames, out / f"contact_{name}.png")
        onion(frames, out / f"onion_{name}.png")
        built[name] = (xs, frames)
        print(name, len(frames), "drawings", sum(f["ticks"] for f in frames), "ticks")
    turnaround(out / "turnaround.png")
    return built


if __name__ == "__main__":
    main(*sys.argv[1:])
