"""Eager vs graph-replay timing."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from cgviz.types import TimingRow


def time_sweep(fn: Callable[[int], Any], sizes: Sequence[int]) -> list[TimingRow]:
    """Takes: a callable that builds and runs the workload for a given size, and sizes.
    Gives: one TimingRow per size (eager vs graph replay, milliseconds).
    Raises: RuntimeError if CUDA is unavailable.
    """
    raise NotImplementedError("TODO(veer)")
