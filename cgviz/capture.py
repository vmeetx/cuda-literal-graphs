"""Capture a CUDA graph from a PyTorch workload."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any


def capture(workload: Callable[..., Any], static_inputs: Sequence[Any]) -> Any:
    """Takes: a workload callable and its static (pre-allocated CUDA) inputs.
    Gives: the captured graph object, with debug info kept so it can be dumped.
    Raises: RuntimeError if CUDA is unavailable or capture fails.
    """
    raise NotImplementedError("TODO(veer)")


def check_replay(
    graph: Any, workload: Callable[..., Any], static_inputs: Sequence[Any]
) -> bool:
    """Takes: a captured graph, the workload and its static inputs.
    Gives: True if graph replay output matches eager output.
    Raises: RuntimeError if replay fails.
    """
    raise NotImplementedError("TODO(veer)")


def dump_dot(graph: Any, path: Path) -> Path:
    """Takes: a captured graph (with debug info) and a destination path.
    Gives: the path of the written .dot file.
    Raises: RuntimeError if the graph was captured without debug info.
    """
    raise NotImplementedError("TODO(veer)")
