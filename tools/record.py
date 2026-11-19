"""Design-time: record a command in a pty as asciicast v2, then render it to a GIF.

    python tools/record.py --cols 100 --rows 32 --cast out.cast --gif out.gif -- cgviz decode

The .cast file is standard asciicast v2 (playable with `asciinema play`, renderable with agg).
The GIF is rendered here by replaying the recording through the pyte terminal emulator and
drawing each screen with DejaVu Sans Mono (the same path as tools/screenshot.py), sampled at
the animation's frame rate. Everything before the program enters the alternate screen (the
GPU capture) is trimmed from the GIF; the static graph printed after it is kept as the
closing frame.
"""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import pty
import select
import struct
import subprocess
import sys
import termios
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pyte  # noqa: E402
from PIL import Image  # noqa: E402

import screenshot  # noqa: E402


def record(cmd, cols, rows, timeout=900):
    master, slave = pty.openpty()
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))
    env = dict(os.environ, COLUMNS=str(cols), LINES=str(rows), TERM="xterm-256color")
    t0 = time.monotonic()
    p = subprocess.Popen(cmd, stdin=slave, stdout=slave, stderr=slave, env=env, close_fds=True)
    os.close(slave)
    events = []
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
        events.append((time.monotonic() - t0, chunk))
    p.wait()
    os.close(master)
    return events


def write_cast(events, cols, rows, path):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"version": 2, "width": cols, "height": rows,
                             "env": {"TERM": "xterm-256color"}}) + "\n")
        for t, chunk in events:
            fh.write(json.dumps([round(t, 6), "o", chunk.decode("utf-8", "replace")]) + "\n")


def read_cast(path):
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    head = json.loads(lines[0])
    ev = [(e[0], e[2].encode()) for e in map(json.loads, lines[1:]) if e[1] == "o"]
    return head["width"], head["height"], ev


def render_gif(events, cols, rows, path, fps=12, size=14, tail=2.5, scale=1.0):
    screen = pyte.Screen(cols, rows)
    stream = pyte.ByteStream(screen)
    start = next((t for t, c in events if b"\x1b[?1049h" in c), events[0][0] if events else 0)
    # end on the last animation frame (the victory), just before the alternate screen closes
    leave = [t for t, c in events if b"\x1b[?1049l" in c]
    end = leave[-1] - 0.01 if leave else (events[-1][0] if events else 0)
    events = [(t, c) for t, c in events if t <= end]
    tail = 0.0
    frames, durs = [], []
    k = 0
    t = start
    last_png = None
    step = 1.0 / fps
    while t <= end + tail:
        while k < len(events) and events[k][0] <= t:
            stream.feed(events[k][1].replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
                        if False else events[k][1])
            k += 1
        tmp = "/tmp/_rec_frame.png"
        screenshot.render(screen, tmp, size=size, crop=False)
        im = Image.open(tmp).convert("RGB")
        if scale != 1.0:
            im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
        b = im.tobytes()
        if last_png is not None and b == last_png:
            durs[-1] += int(step * 1000)
        else:
            frames.append(im)
            durs.append(int(step * 1000))
            last_png = b
        t += step
    durs[-1] = max(durs[-1], 2500)
    pal = [f.quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
           for f in frames]
    pal[0].save(path, save_all=True, append_images=pal[1:], duration=durs, loop=0,
                optimize=True, disposal=1)
    return len(frames), sum(durs) / 1000


def main(argv=None):
    a = argparse.ArgumentParser()
    a.add_argument("--cols", type=int, default=100)
    a.add_argument("--rows", type=int, default=32)
    a.add_argument("--cast", required=True)
    a.add_argument("--gif")
    a.add_argument("--from-cast", action="store_true", help="only render an existing cast")
    a.add_argument("--fps", type=int, default=12)
    a.add_argument("--scale", type=float, default=1.0)
    a.add_argument("cmd", nargs=argparse.REMAINDER)
    o = a.parse_args(argv)
    if o.from_cast:
        cols, rows, ev = read_cast(o.cast)
    else:
        cmd = o.cmd[1:] if o.cmd and o.cmd[0] == "--" else o.cmd
        ev = record(cmd, o.cols, o.rows)
        cols, rows = o.cols, o.rows
        write_cast(ev, cols, rows, o.cast)
        print("cast", o.cast, len(ev), "events", f"{ev[-1][0]:.1f}s" if ev else "")
    if o.gif:
        n, secs = render_gif(ev, cols, rows, o.gif, fps=o.fps, scale=o.scale)
        print("gif", o.gif, n, "frames", f"{secs:.1f}s", f"{os.path.getsize(o.gif) / 1e6:.1f} MB")


if __name__ == "__main__":
    sys.exit(main())
