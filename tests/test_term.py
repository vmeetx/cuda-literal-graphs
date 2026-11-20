"""Terminal capabilities: colour depth guess, 256-colour mapping, and the diff renderer in 256."""

import re

import pytest

from cgviz import miku_assets, show, term


@pytest.mark.parametrize("env, want", [
    ({"COLORTERM": "truecolor", "TERM": "xterm-256color"}, term.TRUECOLOR),
    ({"COLORTERM": "24bit"}, term.TRUECOLOR),
    ({"WT_SESSION": "abc", "TERM": "xterm-256color"}, term.TRUECOLOR),
    ({"TERM_PROGRAM": "iTerm.app", "TERM": "xterm-256color"}, term.TRUECOLOR),
    ({"TERM": "xterm-kitty"}, term.TRUECOLOR),
    ({"TERM": "xterm-direct"}, term.TRUECOLOR),
    ({"TERM": "xterm-256color"}, term.C256),
    ({"TERM_PROGRAM": "Apple_Terminal", "TERM": "xterm-256color"}, term.C256),
    ({"TERM": "screen-256color"}, term.C256),
    ({"TERM": "xterm-256color", "CGVIZ_COLOR": "truecolor"}, term.TRUECOLOR),
    ({"COLORTERM": "truecolor", "CGVIZ_COLOR": "256"}, term.C256),
])
def test_color_depth(env, want):
    assert term.color_depth(env) == want


@pytest.mark.parametrize("rgb, idx", [
    ((0, 0, 0), 16), ((255, 255, 255), 231), ((255, 0, 0), 196), ((0, 255, 0), 46),
    ((0, 0, 255), 21), ((95, 135, 175), 67), ((128, 128, 128), 244), ((30, 30, 30), 234),
])
def test_rgb_to_256(rgb, idx):
    assert term.rgb_to_256(rgb) == idx


def test_miku_palette_stays_distinct_in_256():
    """Her palette keeps the colours that touch apart: hair from outline, skin from blush,
    skirt from top. A collapse would erase the drawing in 256-colour terminals."""
    pal = {k: tuple(v) for k, v in miku_assets.load("walk")["rgb"].items()}
    pairs = [("G", "B"), ("A", "G"), ("E", "U"), ("D", "L"), ("S", "D"), ("b", "I"),
             ("E", "P"), ("G", "C")]
    for a, b in pairs:
        if a in pal and b in pal:
            assert term.rgb_to_256(pal[a]) != term.rgb_to_256(pal[b]), (a, b)


def test_diff_in_256_uses_only_indexed_colour():
    g = [[("▀", (57, 197, 187), (20, 30, 60), False), ("x", (255, 255, 255), None, True)]]
    s = show.diff(None, g, term.C256)
    assert "38;2;" not in s and "48;2;" not in s
    assert re.search(r"\x1b\[38;5;\d+m", s) and re.search(r"\x1b\[48;5;\d+m", s)
    assert show.diff(None, g) == show.diff(None, g, term.TRUECOLOR)
    assert "38;2;57;197;187" in show.diff(None, g)


def test_enable_vt_off_windows(monkeypatch):
    monkeypatch.setattr(term.sys, "platform", "linux")
    assert term.enable_vt() is True
