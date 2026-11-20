"""Show things in the terminal: the static graph, and the animated walk.

The animation composes each frame as a grid of cells (graph tiles, highlighted boxes,
half-block sprites, caption) and redraws only the cells that changed since the previous
frame. Standard library only.
"""

from __future__ import annotations

import importlib.util
import os
import shutil
import signal
import sys
import time

from cgviz import halfblock, term
from cgviz.sprites import FRAMES, PALETTE

RENDERERS = ("braille", "block", "gamma")

# ---------------------------------------------------------------- scaffold renderer API


def available_renderers() -> list[str]:
    """Report which renderers are importable. "block" always; "gamma" and
    "braille" only when n2 imports."""
    out = ["block"]
    if importlib.util.find_spec("n2") is not None:
        try:
            import n2  # noqa: F401
        except Exception:
            return out
        out = ["braille", "block", "gamma"]
    return out


def best_renderer() -> str:
    """Pick the preferred renderer among the available ones."""
    avail = available_renderers()
    for name in ("braille", "gamma", "block"):
        if name in avail:
            return name
    return "block"


def render(fig, cols: int, rows: int, renderer: str):
    """Takes: a matplotlib Figure, a size in character cells and a renderer name.
    Gives: (char grid of shape (rows, cols), colours array).
    Raises: ValueError for an unknown or unavailable renderer."""
    raise NotImplementedError("TODO(veer)")


def print_grid(chars, colours) -> None:
    """Takes: a char grid and its colours. Gives: nothing; prints it with ANSI colour."""
    raise NotImplementedError("TODO(veer)")


# ---------------------------------------------------------------- animation constants

MIN_COLS, MIN_ROWS = 40, 16
SPRITE_W, SPRITE_H = 12, 10         # cells (12x16 px padded to 20 px for the bob and hop)
PORTRAIT_W, PORTRAIT_H = 32, 24     # cells (32x48 px)
PANEL_GAP = 2
HL = (255, 244, 170)                # highlighted box border: bright glyph...
HL_BG = (110, 84, 10)               # ...on a gold background, so it reads on every box colour
CAPTION = (235, 238, 242)
DIM = (130, 134, 142)
BLANK = (" ", None, None, False)
BOTTOM_MARGIN = 3                   # rows kept free below the last box
NODE_GAP = {"TB": 15, "LR": 10}     # sibling gap in the animated layout: room for a sprite


def _pad(frame):
    w = len(frame[0])
    # 3 rows of headroom for the hop, 1 below for the bob; the feet land in the bottom cell, so
    # a walker's line runs through her shins
    return ["." * w] * 3 + list(frame) + ["." * w]


_SPRITE_CACHE: dict = {}


def sprite_cells(name, facing=1, dy=0):
    """Cell grid for a sprite frame: mirrored when facing left, bobbed by dy pixels."""
    key = (name, facing, dy)
    if key not in _SPRITE_CACHE:
        rows = _pad(FRAMES[name]) if not name.startswith("portrait") else list(FRAMES[name])
        if dy < 0:
            rows = rows[-dy:] + ["." * len(rows[0])] * -dy
        elif dy > 0:
            rows = ["." * len(rows[0])] * dy + rows[:-dy]
        if facing < 0:
            rows = [r[::-1] for r in rows]
        _SPRITE_CACHE[key] = halfblock.cells(rows, PALETTE)
    return _SPRITE_CACHE[key]


SIDE = (-(SPRITE_W // 2) + 1, -(SPRITE_H - 2))  # on a vertical line: centred, feet on its row
ABOVE = (-(SPRITE_W // 2) + 1, -(SPRITE_H - 1))  # on a horizontal line: centred, just above


class V1Sprites:
    """The small v1 sprite (12x10 cells) with its portrait panel: the fallback when the
    terminal is too small for the v2 Miku."""

    w, h, side, above, portrait = SPRITE_W, SPRITE_H, SIDE, ABOVE, True

    def is_victory(self, sprite):
        return sprite == "victory_1"

    def victory_at(self, box):
        x0, y0, x1, _ = box
        return (x0 + x1) // 2 - SPRITE_W // 2 + 1, y0 - SPRITE_H

    def cells(self, sprite, facing=1, dy=0):
        return sprite_cells(sprite, facing, dy)


class TinySprites:
    """The tiny sprite (9x10 px, about one graph box): the default, so the whole graph fits
    the terminal. 2 px of headroom for the hop; her feet are the bottom cell."""

    portrait = False
    TOP, BOTTOM = 2, 0          # headroom for the hop; the bob only goes up
    margin = 0                  # no extra rows below the graph: the victory is on a box

    def __init__(self):
        from cgviz.sprites import TINY

        self.frames = TINY
        self.w = len(TINY["idle_1"][0])
        self.h = (self.TOP + len(TINY["idle_1"]) + self.BOTTOM + 1) // 2
        self.side = (-(self.w // 2), -(self.h - 1))    # on a vertical line: centred on it
        self.above = (-(self.w // 2), -self.h)         # on a horizontal line: just above it
        self.stand = (1, -(self.h - 1))                # at a stop: just right of the box
        self._cache = {}

    def is_victory(self, sprite):
        return sprite == "victory_1"

    def victory_at(self, box):
        x0, y0, x1, _ = box
        return (x0 + x1) // 2 - self.w // 2, y0 - self.h

    def cells(self, sprite, facing=1, dy=0):
        dy = max(-self.TOP, min(self.BOTTOM, dy))
        key = (sprite, facing, dy)
        if key not in self._cache:
            fr = self.frames[sprite]
            w = len(fr[0])
            rows = ["." * w] * self.TOP + list(fr) + ["." * w] * self.BOTTOM
            if dy < 0:
                rows = rows[-dy:] + ["." * w] * -dy
            elif dy > 0:
                rows = ["." * w] * dy + rows[:-dy]
            if facing < 0:
                rows = [r[::-1] for r in rows]
            self._cache[key] = halfblock.cells(rows, PALETTE)
        return self._cache[key]


def sprite_rect(pos, orient, off=None):
    """Top-left cell of the walker sprite for a walker standing at `pos`."""
    dx, dy = off or (SIDE if orient == "TB" else ABOVE)
    return pos[0] + dx, pos[1] + dy


def sprite_offsets(frames, orient, side=SIDE, above=ABOVE, places=None, ease=(2, 1)):
    """Per frame, per walker: where the sprite sits relative to the walker's cell.

    Walking along a vertical line she stands beside it; along a horizontal line, above it.
    The offset eases between the two (`ease` = columns, rows per frame) so corners never jump;
    `places` maps cells on a box's border to an offset that keeps a big sprite off the box
    (beside its right side, under its bottom).
    A walker that just split off inherits the offset of the walker it split from."""
    start = side if orient == "TB" else above
    cur, target, last = {}, {}, {}
    out = []
    for f in frames:
        by_pos = {last[w]: cur[w] for w in cur if w in last}
        offs = {}
        for wid, pos, *_r in f.walkers:
            if wid not in cur:
                cur[wid] = by_pos.get(pos, start)
                target[wid] = cur[wid]
            p = last.get(wid)
            if places and pos in places:                  # on a box's border: off the box
                target[wid] = places[pos]
            elif p is not None and p != pos:
                target[wid] = side if p[0] == pos[0] else above
            (cx, cy), (tx, ty) = cur[wid], target[wid]
            cx += max(-ease[0], min(ease[0], tx - cx))
            cy += max(-ease[1], min(ease[1], ty - cy))
            cur[wid] = offs[wid] = (cx, cy)
            last[wid] = pos
        for wid in [w for w in cur if w not in offs]:
            cur.pop(wid), target.pop(wid), last.pop(wid, None)
        out.append(offs)
    return out


# ---------------------------------------------------------------- scene


class Scene:
    """Everything needed to compose frames for one terminal size."""

    def __init__(self, lay, nodes, frames, cols, rows, panel=True, title="", sprites=None):
        self.lay, self.nodes, self.frames, self.title = lay, nodes, frames, title
        self.cols, self.rows = cols, rows
        self.sp = sp = sprites or V1Sprites()
        # canvas = graph plus room for sprites wherever they go
        places = {}
        if lay.orient == "TB":
            for x0, y0, x1, y1 in lay.boxes.values():
                if getattr(sp, "stand", None):
                    places.update({(x1, y): sp.stand for y in range(y0 + 1, y1)})
                if getattr(sp, "under", None):
                    places.update({(x, y1): sp.under for x in range(x0, x1 + 1)})
        self.offs = sprite_offsets(frames, lay.orient, sp.side, sp.above, places,
                                   ease=(max(2, sp.w // 6), max(1, sp.h // 6)))
        xs, ys = [0, lay.width - 1], [0, lay.height - 1]
        for f, offs in zip(frames, self.offs):
            for wid, pos, sprite, *_r in f.walkers:
                sx, sy = self._at(pos, sprite, offs[wid])
                xs += [sx, sx + sp.w - 1]
                ys += [sy, sy + sp.h - 1]
        ys.append(max(ys) + getattr(sp, "margin", BOTTOM_MARGIN))  # room for the ending
        self.ox, self.oy = -min(xs), -min(ys)
        self.cw, self.ch = max(xs) - min(xs) + 1, max(ys) - min(ys) + 1
        self.vh = rows - 2                       # caption + status lines
        self.panel = (panel and sp.portrait and rows - 2 >= PORTRAIT_H
                      and cols - PORTRAIT_W - PANEL_GAP >= min(self.cw, MIN_COLS))
        self.vw = cols - PORTRAIT_W - PANEL_GAP if self.panel else cols
        self.border = {}
        for n, (x0, y0, x1, y1) in lay.boxes.items():
            cells = {(x, y0) for x in range(x0, x1 + 1)} | {(x, y1) for x in range(x0, x1 + 1)}
            cells |= {(x0, y) for y in range(y0, y1 + 1)} | {(x1, y) for y in range(y0, y1 + 1)}
            self.border[n] = cells
        # label characters (inside boxes, not on the border): drawn over sprites
        self.labels = {xy for n, (x0, y0, x1, y1) in lay.boxes.items()
                       for xy in ((x, (y0 + y1) // 2) for x in range(x0 + 1, x1))
                       if lay.cells.get(xy, (" ",))[0] != " "}
        self.cams = self._track()

    def _at(self, pos, sprite, off):
        """Graph-coordinate top-left of a sprite. For the victory she stands centred on top
        of the final box (feet just above its top border) so the box never hides her."""
        if self.sp.is_victory(sprite):
            for box in self.lay.boxes.values():
                x0, y0, x1, y1 = box
                if x0 <= pos[0] <= x1 and y0 <= pos[1] <= y1:
                    return self.sp.victory_at(box)
        return sprite_rect(pos, self.lay.orient, off)

    # canvas coordinates of each walker's sprite
    def rects(self, i):
        out = []
        for wid, pos, sprite, *_r in self.frames[i].walkers:
            sx, sy = self._at(pos, sprite, self.offs[i][wid])
            out.append((sx + self.ox, sy + self.oy, sx + self.ox + self.sp.w - 1,
                        sy + self.oy + self.sp.h - 1))
        return out

    def _axis(self, cam, lo, hi, view, total, first):
        if total <= view:
            return -((view - total) // 2)
        if hi - lo + 1 > view:
            hi = lo + view - 1
        c = (lo + hi) / 2
        want = cam
        if first or c < cam + view / 3:
            want = c - view / 2 if first else c - view / 3
        elif c > cam + 2 * view / 3:
            want = c - 2 * view / 3
        want = max(0, min(int(round(want)), total - view))
        step = max(-3, min(3, want - cam)) if not first else want - cam
        cam += step
        cam = min(cam, lo)                 # never lose her
        cam = max(cam, hi - view + 1)
        return max(0, min(cam, total - view))

    def _track(self):
        cams, cx, cy = [], 0, 0
        for i, f in enumerate(self.frames):
            rs = self.rects(i)
            if not rs:
                cams.append((cx, cy))
                continue
            x0, y0 = min(r[0] for r in rs), min(r[1] for r in rs)
            x1, y1 = max(r[2] for r in rs), max(r[3] for r in rs)
            if x1 - x0 + 1 > self.vw:       # walkers don't fit side by side: follow the leftmost
                left = min(rs, key=lambda r: r[0])
                x0, x1 = left[0], left[2]
            if y1 - y0 + 1 > self.vh:
                top = min(rs, key=lambda r: r[1])
                y0, y1 = top[1], top[3]
            cx = self._axis(cx, x0, x1, self.vw, self.cw, i == 0)
            cy = self._axis(cy, y0, y1, self.vh, self.ch, i == 0)
            cams.append((cx, cy))
        return cams

    def compose(self, i):
        """The full terminal grid for frame i: rows x cols of (char, fg, bg, bold)."""
        f, (cx, cy) = self.frames[i], self.cams[i]
        grid = [[BLANK] * self.cols for _ in range(self.rows)]
        hl = set()
        for n in f.highlight:
            hl |= self.border[n]
        cells = self.lay.cells
        for r in range(self.vh):
            gy = r + cy - self.oy
            for c in range(self.vw):
                gx = c + cx - self.ox
                cell = cells.get((gx, gy))
                if cell and cell[0] != " ":
                    ch, fg, bold = cell
                    bg = None
                    if (gx, gy) in hl:
                        fg, bg, bold = HL, HL_BG, True
                    grid[r][c] = (ch, fg, bg, bold)
        for (wid, pos, sprite, facing, dy), (sx, sy, _, _) in sorted(
                zip(f.walkers, self.rects(i)), key=lambda t: t[0][0]):
            for j, row in enumerate(self.sp.cells(sprite, facing, dy)):
                for k, sc in enumerate(row):
                    if sc is None:
                        continue                       # transparent: keep the graph cell
                    r, c = sy + j - cy, sx + k - cx
                    if 0 <= r < self.vh and 0 <= c < self.vw:
                        ch, fg, bg = sc
                        grid[r][c] = (ch, fg, bg, False)
        # box labels stay readable on top of the sprites
        for (gx, gy) in self.labels:
            r, c = gy + self.oy - cy, gx + self.ox - cx
            if 0 <= r < self.vh and 0 <= c < self.vw:
                ch, fg, bold = cells[(gx, gy)]
                grid[r][c] = (ch, fg, None, bold)
        # the box being visited stays in front of the sprites, so the stop is always visible
        for n in f.highlight:
            x0, y0, x1, y1 = self.lay.boxes[n]
            for gy in range(y0, y1 + 1):
                r = gy + self.oy - cy
                if not 0 <= r < self.vh:
                    continue
                for gx in range(x0, x1 + 1):
                    c = gx + self.ox - cx
                    if not 0 <= c < self.vw:
                        continue
                    ch, fg, bold = cells.get((gx, gy), (" ", None, False))
                    if (gx, gy) in hl:
                        grid[r][c] = (ch, HL, HL_BG, True)
                    else:
                        grid[r][c] = (ch, fg, None, bold)
        if self.panel:
            name = "portrait_victory" if f.event == "victory" else "portrait_idle"
            px, py = self.vw + PANEL_GAP, max(0, (self.vh - PORTRAIT_H) // 2)
            for j, row in enumerate(sprite_cells(name)):
                for k, sc in enumerate(row):
                    if sc is not None and py + j < self.vh:
                        grid[py + j][px + k] = (sc[0], sc[1], sc[2], False)
        _put(grid, self.vh, f.caption, CAPTION, True)
        status = (f"{self.title}   walkers: {len(f.walkers)}   "
                  f"{'victory!' if f.event == 'victory' else ''}")
        _put(grid, self.vh + 1, status.rstrip(), DIM, False)
        return grid


def _put(grid, r, text, fg, bold):
    from cgviz.layout import cut

    text = cut(text, len(grid[r]))
    c = 0
    for ch in text:
        if c >= len(grid[r]):
            break
        grid[r][c] = (ch, fg, None, bold)
        c += 1


def grid_text(grid):
    return "\n".join("".join(c[0] for c in row).rstrip() for row in grid)


# ---------------------------------------------------------------- diff renderer


def _sgr(fg, bg, bold, depth=term.TRUECOLOR):
    s = "\x1b[0m"
    if bold:
        s += "\x1b[1m"
    if fg:
        s += term.fg(fg, depth)
    if bg:
        s += term.bg(bg, depth)
    return s


def diff(prev, grid, depth=term.TRUECOLOR):
    """Escape sequence that turns `prev` into `grid`, touching only changed cells. `depth` is
    the terminal's colour depth (term.TRUECOLOR or term.C256)."""
    out, cur = [], None
    for r, row in enumerate(grid):
        old = prev[r] if prev is not None and r < len(prev) else None
        c = 0
        while c < len(row):
            if old is not None and c < len(old) and old[c] == row[c]:
                c += 1
                continue
            out.append(f"\x1b[{r + 1};{c + 1}H")
            while c < len(row) and (old is None or c >= len(old) or old[c] != row[c]):
                ch, fg, bg, bold = row[c]
                st = (fg, bg, bold)
                if st != cur:
                    out.append(_sgr(fg, bg, bold, depth))
                    cur = st
                out.append(ch)
                c += 1
    return "".join(out)


# ---------------------------------------------------------------- player


class _Terminal:
    """Alternate screen, hidden cursor, no echo; restored on exit, Ctrl-C and SIGTERM."""

    def __init__(self, out):
        self.out, self.restore_input, self.old_term = out, None, None

    def __enter__(self):
        self.restore_input = term.raw_input()
        self.old_term = signal.getsignal(signal.SIGTERM)
        signal.signal(signal.SIGTERM, _raise_interrupt)
        self.out.write("\x1b[?1049h\x1b[?25l\x1b[?7l\x1b[2J")
        self.out.flush()
        return self

    def __exit__(self, *exc):
        try:
            # end any synchronized frame first: an interrupt mid-frame must not leave the
            # terminal holding its paint
            self.out.write(term.SYNC_END + "\x1b[0m\x1b[?7h\x1b[?25h\x1b[?1049l")
            self.out.flush()
        finally:
            if self.restore_input is not None:
                self.restore_input()
            signal.signal(signal.SIGTERM, self.old_term or signal.SIG_DFL)
        return False


def _raise_interrupt(*_):
    raise KeyboardInterrupt


def can_animate(out=None) -> bool:
    out = out or sys.stdout
    if not out.isatty() or not term.enable_vt(out):
        return False
    size = shutil.get_terminal_size((0, 0))
    return size.columns >= MIN_COLS and size.lines >= MIN_ROWS


def play(lay, nodes, frames, title="", panel=True, out=None, fps=12, hold=1.5, sprites=None):
    """Run the animation in the alternate screen. Returns True if it ran to the end."""
    out = out or sys.stdout
    finished = False
    depth = term.color_depth()
    with _Terminal(out):
        size, scene, prev = None, None, None
        t0 = time.monotonic()
        i = 0
        try:
            while i < len(frames):
                now = shutil.get_terminal_size((80, 24))
                if now != size:
                    size = now
                    scene = Scene(lay, nodes, frames, size.columns, size.lines, panel, title,
                                  sprites)
                    prev = None
                    out.write("\x1b[0m\x1b[2J")
                grid = scene.compose(i)
                # one synchronized update per frame: the terminal paints it all at once
                out.write(term.SYNC_BEGIN + diff(prev, grid, depth) + term.SYNC_END)
                out.flush()
                prev = grid
                i += 1
                delay = t0 + i / fps - time.monotonic()
                if delay > 0:
                    time.sleep(delay)
            time.sleep(hold)
            finished = True
        except KeyboardInterrupt:
            finished = False
    return finished


def print_static(text: str, out=None) -> None:
    out = out or sys.stdout
    out.write(text.rstrip("\n") + "\n")
    out.flush()


def environ_size():
    """Terminal size honouring COLUMNS/LINES (for pty-driven screenshots)."""
    try:
        return int(os.environ["COLUMNS"]), int(os.environ["LINES"])
    except (KeyError, ValueError):
        s = shutil.get_terminal_size((100, 30))
        return s.columns, s.lines
