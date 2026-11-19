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
    provenance: Any = None  # cgviz.provenance.Provenance recorded during capture


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
    rec = _Recorder(torch)
    try:
        with torch.cuda.graph(g):
            with rec:
                out = workload(*static_inputs)
        g.instantiate()
    except Exception as e:
        raise RuntimeError(f"capture failed: {type(e).__name__}: {e}") from e
    return Captured(graph=g, output=out, data=g.get_graph_data(), provenance=rec.provenance())


def _shape(t) -> str:
    return "x".join(str(d) for d in t.shape)


class _Recorder:
    """While capturing: which CUDA streams issued work, and the shapes of GEMM-type calls."""

    def __init__(self, torch):
        from torch.overrides import TorchFunctionMode

        self.torch = torch
        self.streams: set[int] = set()
        self.shapes: list[str] = []
        rec = self
        F = torch.nn.functional
        gemms = {torch.matmul, torch.Tensor.__matmul__, torch.mm, torch.bmm, torch.addmm,
                 torch.baddbmm, F.linear}

        class Mode(TorchFunctionMode):
            def __torch_function__(self, func, types, args=(), kwargs=None):
                kwargs = kwargs or {}
                rec.streams.add(torch.cuda.current_stream().cuda_stream)
                if func in gemms:
                    try:
                        if func is F.linear:
                            x, w = args[0], args[1]
                            s = f"{_shape(x)} @ {w.shape[1]}x{w.shape[0]}"
                        elif func in (torch.addmm, torch.baddbmm):
                            s = f"{_shape(args[1])} @ {_shape(args[2])}"
                        else:
                            s = f"{_shape(args[0])} @ {_shape(args[1])}"
                        if s not in rec.shapes:
                            rec.shapes.append(s)
                    except Exception:
                        pass
                return func(*args, **kwargs)

        self.mode = Mode()

    def __enter__(self):
        self.mode.__enter__()
        return self

    def __exit__(self, *exc):
        return self.mode.__exit__(*exc)

    def provenance(self):
        from cgviz.provenance import Provenance, cublas_version

        torch = self.torch
        return Provenance(streams=len(self.streams) or None,
                          gpu=torch.cuda.get_device_name(),
                          cuda=str(torch.version.cuda), cublas=cublas_version(),
                          shapes=self.shapes)


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
    if graph.provenance is not None:
        Path(path).with_name("provenance.json").write_text(
            json.dumps(graph.provenance.to_dict(), indent=1), encoding="utf-8")
    return Path(path)
