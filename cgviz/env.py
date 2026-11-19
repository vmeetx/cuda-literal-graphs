"""Collect and print environment versions."""

from __future__ import annotations

import importlib.metadata as md
import platform
import shutil
import subprocess

NOT_INSTALLED = "not installed"


def _dist_version(name: str) -> str:
    try:
        return md.version(name)
    except md.PackageNotFoundError:
        return NOT_INSTALLED


def _nvidia_smi(query: str) -> str:
    exe = shutil.which("nvidia-smi")
    if exe is None:
        return "nvidia-smi not found"
    try:
        out = subprocess.run(
            [exe, f"--query-gpu={query}", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        ).stdout.strip()
    except (subprocess.SubprocessError, OSError) as e:
        return f"error: {type(e).__name__}"
    return out.splitlines()[0].strip() if out else "unknown"


def collect() -> dict[str, str]:
    """Return an ordered mapping of component -> version string."""
    info: dict[str, str] = {"python": platform.python_version()}
    torch_cuda = NOT_INSTALLED
    gpu = None
    try:
        import torch

        info["torch"] = torch.__version__
        torch_cuda = str(torch.version.cuda)
        if torch.cuda.is_available():
            gpu = torch.cuda.get_device_name(0)
    except Exception:
        info["torch"] = NOT_INSTALLED
    info["torch CUDA"] = torch_cuda
    info["driver"] = _nvidia_smi("driver_version")
    for dist in ("cuda-bindings", "networkx", "matplotlib", "img2unicode", "n2"):
        info[dist] = _dist_version(dist)
    info["GPU"] = gpu or _nvidia_smi("name")
    return info


def format_info(info: dict[str, str]) -> str:
    """Format a mapping as aligned key/value lines."""
    width = max((len(k) for k in info), default=0)
    return "\n".join(f"{k.ljust(width)}  {v}" for k, v in info.items())


def print_env() -> None:
    print(format_info(collect()))
