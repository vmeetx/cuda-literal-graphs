"""Compare against Nsight Compute (ncu)."""

from __future__ import annotations

from collections.abc import Sequence

from cgviz.types import NcuRow


def ncu_sweep(kernel: str, sizes: Sequence[int]) -> list[NcuRow]:
    """Takes: a kernel identifier and sizes.
    Gives: one NcuRow per size (default clocks and unlocked clocks, milliseconds).
    Raises: FileNotFoundError if ncu is not on PATH; RuntimeError if profiling fails.
    """
    raise NotImplementedError("TODO(veer)")
