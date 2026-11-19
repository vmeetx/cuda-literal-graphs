"""Render text pixel maps as terminal half blocks with 24-bit colour. Standard library only.

A frame is a list of equal-length strings, one letter per pixel; a palette maps letters to
(r, g, b). '.' is transparent. Two vertical pixels share one terminal cell: the upper one is
drawn as the foreground of '▀' (or '▄' for the lower one alone). A transparent half never
sets a background, so whatever the terminal shows behind it stays visible.
"""

from __future__ import annotations

UPPER, LOWER, FULL = "▀", "▄", "█"
RESET = "\x1b[0m"


def _fg(c):
    return "\x1b[38;2;%d;%d;%dm" % c


def _bg(c):
    return "\x1b[48;2;%d;%d;%dm" % c


def shift(frame, dy=0, dx=0):
    """Move a frame by whole pixels (used for the idle bob), padding with transparency."""
    w = len(frame[0])
    rows = ["." * w] * max(dy, 0) + list(frame[max(-dy, 0):])
    if dx > 0:
        rows = ["." * dx + r[:w - dx] for r in rows]
    elif dx < 0:
        rows = [r[-dx:] + "." * -dx for r in rows]
    return rows


def cells(frame, palette):
    """Return rows of cells: None (fully transparent) or (char, fg, bg-or-None)."""
    rows = list(frame)
    if len(rows) % 2:
        rows.append("." * len(rows[0]))
    out = []
    for y in range(0, len(rows), 2):
        line = []
        for top, bot in zip(rows[y], rows[y + 1]):
            t = palette.get(top) if top != "." else None
            b = palette.get(bot) if bot != "." else None
            if t is None and b is None:
                line.append(None)
            elif b is None:
                line.append((UPPER, t, None))
            elif t is None:
                line.append((LOWER, b, None))
            elif t == b:
                line.append((FULL, t, None))
            else:
                line.append((UPPER, t, b))
        out.append(line)
    return out


def lines(frame, palette):
    """Standalone strings. Transparent cells are written as cursor-forward moves, so printing
    a sprite over existing text leaves that text visible."""
    out = []
    for row in cells(frame, palette):
        s, run = [], 0
        for c in row:
            if c is None:
                run += 1
                continue
            if run:
                s.append(RESET + "\x1b[%dC" % run)
                run = 0
            ch, fg, bg = c
            s.append(_fg(fg) + (_bg(bg) if bg else "\x1b[49m") + ch)
        s.append(RESET)
        out.append("".join(s))
    return out


def lines_plain(frame, palette):
    """Like lines() but transparent cells are spaces (for files and previews)."""
    out = []
    for row in cells(frame, palette):
        s = []
        for c in row:
            if c is None:
                s.append(RESET + " ")
            else:
                ch, fg, bg = c
                s.append(_fg(fg) + (_bg(bg) if bg else "\x1b[49m") + ch)
        out.append("".join(s) + RESET)
    return out


def overlay(under, frame, palette, x, y):
    """Composite a sprite onto a grid of (char, fg, bg) cells in place at cell (x, y).

    Fully transparent cells keep the underlying cell; a half-transparent cell keeps the
    underlying background colour behind the visible half."""
    for j, row in enumerate(cells(frame, palette)):
        for i, c in enumerate(row):
            yy, xx = y + j, x + i
            if c is None or not (0 <= yy < len(under) and 0 <= xx < len(under[yy])):
                continue
            ch, fg, bg = c
            under[yy][xx] = (ch, fg, bg if bg else under[yy][xx][2])
    return under
