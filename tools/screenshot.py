"""Design-time: screenshot what a real terminal shows for a command's output.

    python tools/screenshot.py --cols 120 --rows 40 --out shot.png -- python spike/lab.py decode --fit
    python tools/screenshot.py --cols 120 --out shot.png --ansi saved_output.ans

The command runs inside a pseudo-terminal of the given size (so isatty() is true, colours
are on and --fit sees that size). Its exact bytes are fed to the pyte terminal emulator and
the resulting screen is drawn with real font glyphs: DejaVu Sans Mono, falling back per glyph
to DejaVu Sans only where Mono has no glyph (as terminals do). Nothing is hand-drawn.
The emulated screen is taller than --rows so output that would scroll is kept in full.
"""

from __future__ import annotations

import argparse
import fcntl
import os
import pty
import select
import struct
import subprocess
import sys
import termios

import pyte
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
MONO_B = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
FALLBACK = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BG, FG = (24, 26, 32), (210, 212, 216)
NAMED = {"black": (0, 0, 0), "red": (205, 49, 49), "green": (13, 188, 121), "brown": (229, 229, 16),
         "yellow": (229, 229, 16), "blue": (36, 114, 200), "magenta": (188, 63, 188),
         "cyan": (17, 168, 205), "white": (229, 229, 229), "brightblack": (102, 102, 102),
         "brightred": (241, 76, 76), "brightgreen": (35, 209, 139), "brightyellow": (245, 245, 67),
         "brightblue": (59, 142, 234), "brightmagenta": (214, 112, 214), "brightcyan": (41, 184, 219),
         "brightwhite": (255, 255, 255)}


def run_in_pty(cmd, cols, rows, timeout=600):
    master, slave = pty.openpty()
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))
    env = dict(os.environ, COLUMNS=str(cols), LINES=str(rows), TERM="xterm-256color")
    p = subprocess.Popen(cmd, stdin=slave, stdout=slave, stderr=slave, env=env, close_fds=True)
    os.close(slave)
    out = bytearray()
    while True:
        r, _, _ = select.select([master], [], [], timeout)
        if not r:
            break
        try:
            chunk = os.read(master, 65536)
        except OSError:
            break
        if not chunk:
            break
        out += chunk
    p.wait()
    os.close(master)
    return bytes(out)


def colour(c, default):
    if c in (None, "default"):
        return default
    if isinstance(c, str) and len(c) == 6:
        try:
            return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))
        except ValueError:
            pass
    return NAMED.get(c, default)


def screen_of(data, cols, rows):
    sc = pyte.Screen(cols, rows)
    st = pyte.ByteStream(sc)
    # the pty turns \n into \r\n; a raw file may not, so normalise
    st.feed(data.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
    return sc


class Glyphs:
    def __init__(self, size):
        self.f = ImageFont.truetype(MONO, size)
        self.fb = ImageFont.truetype(MONO_B, size)
        self.fall = ImageFont.truetype(FALLBACK, size)
        self.cmap = TTFont(MONO).getBestCmap()
        self.cmap_b = TTFont(MONO_B).getBestCmap()
        asc, desc = self.f.getmetrics()
        self.cw = round(self.f.getlength("M"))
        self.ch = asc + desc

    def font(self, ch, bold):
        if bold and ord(ch) in self.cmap_b:
            return self.fb
        return self.f if ord(ch) in self.cmap else self.fall


def render(sc, path, size=16, crop=True):
    g = Glyphs(size)
    lines = list(range(sc.lines))
    if crop:
        used = [y for y in lines if any(sc.buffer[y][x].data.strip() for x in range(sc.columns))]
        lines = lines[: (max(used) + 1 if used else 1)]
    W, H = sc.columns * g.cw + 2 * g.cw, len(lines) * g.ch + 2 * g.ch
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    for j, y in enumerate(lines):
        row = sc.buffer[y]
        for x in range(sc.columns):
            c = row[x]
            fg, bg = colour(c.fg, FG), colour(c.bg, None)
            if c.reverse:
                fg, bg = (bg or BG), fg
            px, py = g.cw + x * g.cw, g.ch + j * g.ch
            if bg:
                d.rectangle([px, py, px + g.cw - 1, py + g.ch - 1], fill=bg)
            if c.data and c.data != " ":
                d.text((px, py), c.data, font=g.font(c.data, c.bold), fill=fg)
    im.save(path)
    return path


def main(argv=None):
    a = argparse.ArgumentParser()
    a.add_argument("--cols", type=int, default=120)
    a.add_argument("--rows", type=int, default=40, help="pty height the command sees")
    a.add_argument("--keep", type=int, default=400, help="emulated rows kept (scrollback)")
    a.add_argument("--out", required=True)
    a.add_argument("--ansi", help="render a saved ANSI file instead of running a command")
    a.add_argument("--save-ansi", help="also save the raw bytes here")
    a.add_argument("cmd", nargs=argparse.REMAINDER)
    o = a.parse_args(argv)
    if o.ansi:
        data = open(o.ansi, "rb").read()
    else:
        cmd = o.cmd[1:] if o.cmd and o.cmd[0] == "--" else o.cmd
        data = run_in_pty(cmd, o.cols, o.rows)
    if o.save_ansi:
        open(o.save_ansi, "wb").write(data)
    sc = screen_of(data, o.cols, o.keep)
    render(sc, o.out)
    print(o.out)


if __name__ == "__main__":
    sys.exit(main())
