"""Render a Figure to Unicode in the terminal."""

from __future__ import annotations

import importlib.util

import numpy as np
from matplotlib.figure import Figure

RENDERERS = ("braille", "block", "gamma")


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


def render(fig: Figure, cols: int, rows: int, renderer: str) -> tuple[np.ndarray, np.ndarray]:
    """Takes: a Figure, a size in character cells and a renderer name.
    Gives: (char grid of shape (rows, cols), colours array).
    Raises: ValueError for an unknown or unavailable renderer.
    """
    raise NotImplementedError("TODO(veer)")


def print_grid(chars: np.ndarray, colours: np.ndarray) -> None:
    """Takes: a char grid and its colours.
    Gives: nothing; prints the grid to stdout with ANSI colour.
    Raises: ValueError if shapes do not match.
    """
    raise NotImplementedError("TODO(veer)")
