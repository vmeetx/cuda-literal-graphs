"""Capture a CUDA graph from a PyTorch workload."""

from __future__ import annotations

import json
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class Captured:
    graph: Any            # torch.cuda.CUDAGraph, captured with keep_graph=True
    output: Any           # static output tensor written by replay
    data: dict            # graph.get_graph_data(): nodes with types, kernel names, deps


def _torch():
    import torch

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is not available")
    return torch


def _warmup_gpu(seconds: float = 0.5) -> None:
    torch = _torch()
    a = torch.randn(2048, 2048, device="cuda")
    t0 = time.time()
    while time.time() - t0 < seconds:
        for _ in range(20):
            a @ a
        torch.cuda.synchronize()


def capture(workload: Callable[..., Any], static_inputs: Sequence[Any]) -> Captured:
    """Takes: a workload callable and its static (pre-allocated CUDA) inputs.
    Gives: the captured graph with its graph data (debug info kept so it can be dumped).
    Raises: RuntimeError if CUDA is unavailable or capture fails.
    """
    torch = _torch()
    _warmup_gpu()
    s = torch.cuda.Stream()
    s.wait_stream(torch.cuda.current_stream())
    with torch.cuda.stream(s):
        for _ in range(3):
            workload(*static_inputs)
    torch.cuda.current_stream().wait_stream(s)
    torch.cuda.synchronize()
    g = torch.cuda.CUDAGraph(keep_graph=True)
    try:
        with torch.cuda.graph(g):
            out = workload(*static_inputs)
        g.instantiate()
    except Exception as e:
        raise RuntimeError(f"capture failed: {type(e).__name__}: {e}") from e
    return Captured(graph=g, output=out, data=g.get_graph_data())


def check_replay(graph: Captured, workload: Callable[..., Any], static_inputs: Sequence[Any]) -> bool:
    """Takes: a captured graph, the workload and its static inputs.
    Gives: True if graph replay output matches eager output.
    Raises: RuntimeError if replay fails.
    """
    torch = _torch()
    ref = workload(*static_inputs)
    torch.cuda.synchronize()
    try:
        graph.graph.replay()
        torch.cuda.synchronize()
    except Exception as e:
        raise RuntimeError(f"replay failed: {e}") from e
    out = graph.output
    if not (torch.is_tensor(ref) and torch.is_tensor(out)):
        raise RuntimeError("the workload must return a CUDA tensor")
    tol = dict(rtol=1e-4, atol=1e-4) if ref.dtype == torch.float32 else dict(rtol=2e-2, atol=2e-2)
    return bool(torch.allclose(out.float(), ref.float(), **tol))


def dump_dot(graph: Captured, path: Path) -> Path:
    """Takes: a captured graph (with debug info) and a destination path.
    Gives: the path of the written .dot file.
    Raises: RuntimeError if the graph was captured without debug info.
    """
    try:
        graph.graph.debug_dump(str(path))
    except Exception as e:
        raise RuntimeError(f"no debug info: {e}") from e
    return Path(path)


def save_data(graph: Captured, path: Path) -> Path:
    """Write the graph data as JSON (the drawer's input)."""
    Path(path).write_text(json.dumps(graph.data, indent=1), encoding="utf-8")
    return Path(path)
