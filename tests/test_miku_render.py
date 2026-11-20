"""Hair-flicker regression: what reaches the terminal must be exactly the sprite's own pixels.

Every frame of every clip, both facings, composited over a graph box on a dark and a light
background, goes through the real diff redraw (cgviz.show.diff). The byte stream is cut into
small chunks that split multi-byte characters, decoded the way tools/record.py decodes a pty
recording, and replayed in a terminal emulator (pyte). Then every cell of the sprite's
rectangle must equal the composed scene: no U+FFFD glyph, no outline or black pixel the frame
data does not contain, no stale cell left by the bob.

Cause of the flicker seen in the walk GIFs (GATE 2e): the recorder decoded each pty read on its
own, so a half block split across two reads became two U+FFFD glyphs, drawn dark on the hair.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tools"), str(ROOT / "tools/miku")]

pyte = pytest.importorskip("pyte")
record = pytest.importorskip("record")
demo_walk = pytest.importorskip("demo_walk")

from cgviz import halfblock, miku_assets, miku_motion, show  # noqa: E402

COLS, ROWS, X = 100, 44, 12
BACKGROUNDS = {"dark": (30, 30, 30), "light": (250, 250, 250)}


def _chunks(data, n=7):
    return [(0.0, data[i:i + n]) for i in range(0, len(data), n)]


def _hex(c):
    return "default" if c is None else "%02x%02x%02x" % c


def _frames():
    for clip in miku_assets.clips():
        for i, _ in enumerate(miku_assets.load(clip)["frames"]):
            for facing in ("right", "left"):
                yield clip, i, facing


def test_split_half_blocks_survive_decoding():
    """The cause, pinned: decoding chunk by chunk breaks the half block; the fix does not."""
    data = ("\x1b[38;2;1;2;3m" + "▀▄█" * 50).encode()
    naive = "".join(c.decode("utf-8", "replace") for _, c in _chunks(data))
    fixed = "".join(t for _, t in record.decode_events(_chunks(data)))
    assert "�" in naive
    assert "�" not in fixed and fixed == data.decode()


@pytest.mark.parametrize("bgname", sorted(BACKGROUNDS))
def test_terminal_output_matches_sprite_cells(bgname):
    bg = BACKGROUNDS[bgname]
    screen = pyte.Screen(COLS, ROWS)
    stream = pyte.Stream(screen)
    prev = None
    for clip, i, facing in _frames():
        view = miku_assets.load(clip)["frames"][i]["anchors"].get("view")
        tick = miku_motion.Tick(clip, i, "front" if view == "front" else facing, X)
        grid = demo_walk.scene(COLS, ROWS, tick, "regression", bg=bg)
        data = show.diff(prev, grid).encode()
        stream.feed("".join(t for _, t in record.decode_events(_chunks(data))))
        prev = grid
        sprite = halfblock.cells(miku_assets.terminal_variant(
            miku_assets.frame_grid(clip, i, "left" if tick.facing == "left" else "right")),
            miku_assets.load("walk")["rgb"])
        for y in range(2, 2 + 36):                          # the sprite's rectangle (72 px = 36 cells)
            for x in range(X, min(X + 74, COLS)):
                own = sprite[y - 2][x - X] if x - X < len(sprite[y - 2]) else None
                if own is None or own[2] is None:           # transparent (half): the scene shows through
                    assert screen.buffer[y][x].bg == _hex(bg), (clip, i, facing, bgname, x, y)
                want = grid[y][x]
                got = screen.buffer[y][x]
                where = (clip, i, facing, bgname, x, y)
                assert got.data != "�", where
                assert got.data == want[0], (where, got.data, want[0])
                if want[0] != " ":
                    assert got.fg == _hex(want[1]), (where, got.fg, want[1])
                assert got.bg == _hex(want[2]), (where, got.bg, want[2])
