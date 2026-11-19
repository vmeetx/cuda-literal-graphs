"""The player restores the terminal on Ctrl-C and SIGTERM, and stays static when not a tty."""

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

pty = pytest.importorskip("pty")

ROOT = Path(__file__).resolve().parents[1]

PLAYER = """
import json, sys
sys.path.insert(0, {root!r})
from cgviz import draw, presets, show, walk
d = json.load(open({fix!r}))
lay, *_ = draw.layout(d, presets.ROLES["diamond"], 100)
a, _, cn, ce = draw.layout(d, presets.ROLES["diamond"], 100, prefer=(lay.orient,),
                           node_gap=show.NODE_GAP[lay.orient])
frames = walk.Walk(a, cn, ce, speed=0.5).frames()
print("READY", flush=True)
show.play(a, cn, frames, title="test")
print("AFTER", flush=True)
"""


def _run(sig):
    import fcntl
    import struct
    import termios

    code = PLAYER.format(root=str(ROOT), fix=str(ROOT / "tests/fixtures/graphs/diamond.json"))
    master, slave = pty.openpty()
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 30, 100, 0, 0))
    env = dict(os.environ, COLUMNS="100", LINES="30")
    p = subprocess.Popen([sys.executable, "-c", code], stdin=slave, stdout=slave, stderr=slave,
                         env=env, close_fds=True, start_new_session=True)
    os.close(slave)
    out = b""
    deadline = time.time() + 20
    sent = False
    while time.time() < deadline:
        import select

        r, _, _ = select.select([master], [], [], 0.2)
        if r:
            try:
                chunk = os.read(master, 65536)
            except OSError:
                break
            if not chunk:
                break
            out += chunk
        if not sent and out.count(b"\x1b[") > 50:
            p.send_signal(sig)
            sent = True
        if p.poll() is not None and not r:
            break
    p.wait(timeout=10)
    os.close(master)
    return out


@pytest.mark.skipif(sys.platform == "win32", reason="needs a POSIX pty")
@pytest.mark.parametrize("sig", [signal.SIGINT, signal.SIGTERM])
def test_terminal_restored_on_interrupt(sig):
    out = _run(sig)
    assert b"\x1b[?1049h" in out and b"\x1b[?25l" in out        # entered alt screen, hid cursor
    tail = out[out.rfind(b"\x1b[?1049h"):]
    assert b"\x1b[?25h" in tail and b"\x1b[?1049l" in tail and b"\x1b[?7h" in tail
    assert b"AFTER" in out                                        # play() returned normally


def test_static_when_not_a_tty(capsys):
    from cgviz import show

    assert not show.can_animate(open(os.devnull, "w"))
