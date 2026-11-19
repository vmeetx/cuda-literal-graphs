"""Where a captured graph came from: printed as a header with every run.

    captured graph · 3 streams during capture · NVIDIA GeForce RTX 3050 · CUDA 13.0 ·
    cuBLAS 13.1.0 · shapes: 1x1024 @ 1024x1024, ...

The stream count and GEMM shapes are recorded while the workload is being captured (see
capture.capture); the rest is read from the runtime. Standard library only here.
"""

from __future__ import annotations

from dataclasses import dataclass, field

KERNEL_NOTE = "kernel names: chosen at capture for these shapes on this GPU"
SINGLE_STREAM_NOTE = "single stream → chain; parallelism can't appear."


@dataclass
class Provenance:
    streams: int | None = None
    gpu: str = "unknown GPU"
    cuda: str = "?"
    cublas: str = "?"
    shapes: list[str] = field(default_factory=list)

    def header(self) -> str:
        n = "?" if self.streams is None else str(self.streams)
        unit = "stream" if self.streams == 1 else "streams"
        shapes = ", ".join(self.shapes[:3]) + (" …" if len(self.shapes) > 3 else "")
        parts = ["captured graph", f"{n} {unit} during capture", self.gpu, f"CUDA {self.cuda}",
                 f"cuBLAS {self.cublas}", f"shapes: {shapes or '?'}"]
        line = " · ".join(parts)
        if self.streams == 1:
            line += "\n" + SINGLE_STREAM_NOTE
        return line

    def to_dict(self) -> dict:
        return {"streams": self.streams, "gpu": self.gpu, "cuda": self.cuda,
                "cublas": self.cublas, "shapes": self.shapes}

    @classmethod
    def from_dict(cls, d: dict) -> "Provenance":
        return cls(d.get("streams"), d.get("gpu", "unknown GPU"), d.get("cuda", "?"),
                   d.get("cublas", "?"), list(d.get("shapes", [])))


def cublas_version() -> str:
    """cuBLAS version from the library torch loaded (cublasGetProperty), or '?'."""
    import ctypes
    import glob
    import os

    try:
        import torch

        roots = [os.path.dirname(torch.__file__)]
        try:
            import nvidia  # pip CUDA wheels

            roots += list(nvidia.__path__)
        except Exception:
            pass
        libs = []
        for r in roots:
            libs += glob.glob(os.path.join(r, "**", "libcublas.so*"), recursive=True)
        libs += ["libcublas.so"]
        for lib in libs:
            try:
                h = ctypes.CDLL(lib)
            except OSError:
                continue
            vals = []
            for prop in (0, 1, 2):          # MAJOR, MINOR, PATCH
                v = ctypes.c_int()
                if h.cublasGetProperty(prop, ctypes.byref(v)) != 0:
                    break
                vals.append(v.value)
            if len(vals) == 3:
                return ".".join(map(str, vals))
    except Exception:
        pass
    return "?"
