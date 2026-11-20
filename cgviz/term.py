"""What the user's terminal can do, so the animation works out of the box. Standard library only.

- Colour depth: 24-bit when the terminal says so, else the xterm 256-colour palette.
- Windows console: escape sequences are switched on (they are off by default in conhost).
- Synchronized output (DEC mode 2026): each frame is painted at once, with no tearing. Terminals
  that don't know the mode ignore it, so it is always sent.
"""

from __future__ import annotations

import os
import sys

SYNC_BEGIN = "\x1b[?2026h"
SYNC_END = "\x1b[?2026l"

TRUECOLOR, C256 = "truecolor", "256"
# terminals known to do 24-bit colour even when COLORTERM is not passed through (ssh, sudo, tmux)
_TRUE_TERMS = ("xterm-kitty", "xterm-ghostty", "wezterm", "alacritty", "foot", "contour")
_TRUE_PROGRAMS = ("iTerm.app", "WezTerm", "vscode", "ghostty", "Hyper", "Tabby", "WarpTerminal")


def color_depth(env=None) -> str:
    """TRUECOLOR or C256. CGVIZ_COLOR=truecolor|256 overrides the guess."""
    env = os.environ if env is None else env
    force = env.get("CGVIZ_COLOR", "").lower()
    if force in ("truecolor", "24bit"):
        return TRUECOLOR
    if force in ("256", "8bit"):
        return C256
    if env.get("COLORTERM", "").lower() in ("truecolor", "24bit"):
        return TRUECOLOR
    if env.get("WT_SESSION") or env.get("TERM_PROGRAM") in _TRUE_PROGRAMS:
        return TRUECOLOR
    term = env.get("TERM", "")
    if any(term.startswith(t) for t in _TRUE_TERMS) or term.endswith("-direct"):
        return TRUECOLOR
    if sys.platform == "win32" and not term:
        return TRUECOLOR          # Windows 10+ console and Windows Terminal both do 24-bit
    return C256


_CUBE = (0, 95, 135, 175, 215, 255)


def _cube_index(v):
    return min(range(6), key=lambda i: abs(_CUBE[i] - v))


_CACHE: dict = {}


def rgb_to_256(c) -> int:
    """Nearest xterm-256 index (6x6x6 cube 16-231 or grey ramp 232-255) to an (r, g, b)."""
    if c in _CACHE:
        return _CACHE[c]
    r, g, b = c
    ir, ig, ib = _cube_index(r), _cube_index(g), _cube_index(b)
    cube = (_CUBE[ir], _CUBE[ig], _CUBE[ib])
    grey_i = max(0, min(23, round(((r + g + b) / 3 - 8) / 10)))
    grey = 8 + 10 * grey_i

    def dist(p):
        # weighted distance: the eye is most sensitive to green, least to blue
        return 2 * (p[0] - r) ** 2 + 4 * (p[1] - g) ** 2 + 3 * (p[2] - b) ** 2

    if dist((grey, grey, grey)) < dist(cube):
        idx = 232 + grey_i
    else:
        idx = 16 + 36 * ir + 6 * ig + ib
    _CACHE[c] = idx
    return idx


def fg(c, depth=TRUECOLOR) -> str:
    if depth == TRUECOLOR:
        return "\x1b[38;2;%d;%d;%dm" % c
    return "\x1b[38;5;%dm" % rgb_to_256(c)


def bg(c, depth=TRUECOLOR) -> str:
    if depth == TRUECOLOR:
        return "\x1b[48;2;%d;%d;%dm" % c
    return "\x1b[48;5;%dm" % rgb_to_256(c)


_VT = None


def enable_vt(out=None) -> bool:
    """Make sure the terminal interprets escape sequences. True if it does.

    Off Windows this is always true. On Windows it turns on ENABLE_VIRTUAL_TERMINAL_PROCESSING
    for the console behind `out` (Windows Terminal already has it on; classic conhost doesn't).
    """
    global _VT
    if sys.platform != "win32":
        return True
    if _VT is not None:
        return _VT
    try:
        import ctypes
        import msvcrt
        from ctypes import wintypes

        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        k32.GetConsoleMode.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD))
        k32.SetConsoleMode.argtypes = (wintypes.HANDLE, wintypes.DWORD)
        out = out or sys.stdout
        h = msvcrt.get_osfhandle(out.fileno())
        mode = wintypes.DWORD()
        if not k32.GetConsoleMode(h, ctypes.byref(mode)):
            _VT = False
            return _VT
        # ENABLE_PROCESSED_OUTPUT | ENABLE_VIRTUAL_TERMINAL_PROCESSING
        _VT = bool(mode.value & 0x4) or bool(k32.SetConsoleMode(h, mode.value | 0x1 | 0x4))
    except Exception:
        _VT = False
    return _VT


def raw_input(inp=None):
    """Stop keypresses from echoing over the animation. Returns a function that restores the
    old mode and throws away anything typed meanwhile, so it doesn't land in the shell.

    POSIX: termios, echo and line mode off. Windows: the console input mode, echo and line
    input off (processed input stays on, so Ctrl-C still interrupts). A no-op when stdin is
    not a terminal.
    """
    inp = inp or sys.stdin
    try:
        if not inp.isatty():
            return lambda: None
        fd = inp.fileno()
    except (AttributeError, OSError, ValueError):
        return lambda: None
    if sys.platform == "win32":
        return _raw_windows(fd)
    try:
        import termios

        saved = termios.tcgetattr(fd)
        new = termios.tcgetattr(fd)
        new[3] &= ~(termios.ECHO | termios.ICANON)
        termios.tcsetattr(fd, termios.TCSANOW, new)
    except Exception:
        return lambda: None

    def restore():
        try:
            termios.tcsetattr(fd, termios.TCSAFLUSH, saved)
        except Exception:
            pass
    return restore


ENABLE_LINE_INPUT, ENABLE_ECHO_INPUT = 0x2, 0x4


def _raw_windows(fd):
    try:
        import ctypes
        import msvcrt
        from ctypes import wintypes

        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        k32.GetConsoleMode.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD))
        k32.SetConsoleMode.argtypes = (wintypes.HANDLE, wintypes.DWORD)
        k32.FlushConsoleInputBuffer.argtypes = (wintypes.HANDLE,)
        h = msvcrt.get_osfhandle(fd)
        mode = wintypes.DWORD()
        if not k32.GetConsoleMode(h, ctypes.byref(mode)):
            return lambda: None
        saved = mode.value
        if not k32.SetConsoleMode(h, saved & ~(ENABLE_LINE_INPUT | ENABLE_ECHO_INPUT)):
            return lambda: None
    except Exception:
        return lambda: None

    def restore():
        try:
            k32.FlushConsoleInputBuffer(h)
            k32.SetConsoleMode(h, saved)
        except Exception:
            pass
    return restore


def utf8_stdout(out=None):
    """Write UTF-8 when stdout is a pipe or file whose encoding can't hold the box and block
    characters (Windows PowerShell 5.1 pipes default to the ANSI code page). A real console
    is left alone: Python already writes it as Unicode."""
    out = out or sys.stdout
    enc = (getattr(out, "encoding", None) or "").lower().replace("-", "")
    if enc in ("utf8", "utf8sig"):
        return
    try:
        if out.isatty() and sys.platform == "win32":
            return
        out.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError, ValueError):
        pass
