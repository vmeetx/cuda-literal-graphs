"""Built-in demo workload."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any


def diamond() -> tuple[Callable[..., Any], Sequence[Any]]:
    """Takes: nothing.
    Gives: (workload, static_inputs) for the diamond: two branches on two streams, joined.
    Raises: RuntimeError if CUDA is unavailable.
    """
    from cgviz import presets

    return presets.diamond()
