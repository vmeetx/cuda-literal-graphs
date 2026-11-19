"""Design-time: keyframes of the walk, through the real screenshot path.

    python tools/keyframes.py PRESET [COLS ROWS] [OUTDIR]

Builds the same Scene the player uses, composes the first frame, the first fork (first
split), the first join (first merge) and the final frame, writes each as the exact escape
sequence the player sends, and renders it with tools/screenshot.py (pyte + DejaVu Sans Mono).
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tools")]

from cgviz import draw, presets, show, walk  # noqa: E402

import screenshot  # noqa: E402

FIX = ROOT / "tests/fixtures/graphs"


def build(preset, cols=100, rows=30, speed=1.0, panel=True):
    data = json.loads((FIX / f"{preset}.json").read_text())
    lay, *_ = draw.layout(data, presets.ROLES[preset], cols)
    alay, _, acn, ace = draw.layout(data, presets.ROLES[preset], cols, prefer=(lay.orient,),
                                    node_gap=show.NODE_GAP[lay.orient])
    frames = walk.Walk(alay, acn, ace, speed=speed).frames()
    return show.Scene(alay, acn, frames, cols, rows, panel=panel, title=f"cgviz {preset}")


def keyframe_indices(frames):
    idx = {"first": 0}
    split_at = None
    for i, f in enumerate(frames):
        if f.event == "split" and split_at is None:
            split_at = i
        if split_at is not None and "fork" not in idx and len(f.walkers) > 1:
            xs = sorted(p[0] + p[1] * 1000 for _, p, *_r in f.walkers)
            spread = min(abs(a[1][0] - b[1][0]) + abs(a[1][1] - b[1][1])
                         for a in f.walkers for b in f.walkers if a is not b)
            if spread >= 14 and len(f.walkers) == max(len(g.walkers) for g in frames[i:i + 60]):
                idx["fork"] = i
        if f.event == "merge" and "join" not in idx:
            idx["join"] = max(i - 1, 0)                 # the moment before they merge
    idx["final"] = len(frames) - 1
    return idx


def main(preset, cols=100, rows=30, outdir=str(ROOT / "findings/beta")):
    cols, rows = int(cols), int(rows)
    sc = build(preset, cols, rows)
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    for name, i in keyframe_indices(sc.frames).items():
        grid = sc.compose(i)
        esc = show.diff(None, grid)
        scr = screenshot.screen_of(b"", cols, rows)
        import pyte

        st = pyte.ByteStream(scr)
        st.feed(esc.encode())
        png = out / f"{preset}_{name}_{cols}x{rows}.png"
        screenshot.render(scr, str(png), crop=False)
        print(png, "frame", i, "walkers", len(sc.frames[i].walkers))


if __name__ == "__main__":
    main(*sys.argv[1:])
