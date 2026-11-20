"""Built-in workloads: diamond, and one transformer layer in decode or prefill shape.

Each preset gives (workload, static_inputs). Branches that are independent run on side
streams so the captured graph has real forks and joins.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

NAMES = ("diamond", "decode", "prefill")

# Labels for GEMM-type kernels, applied in execution order (the label pipeline's first step).
LAYER_ROLES = ["Q", "K", "V", "QK", "PV", "out", "gate", "up", "down"]
ROLES = {"diamond": ["gemm1", "gemm2"], "decode": LAYER_ROLES, "prefill": LAYER_ROLES,
         # the examples/ workloads
         "mlp": ["fc1", "fc2", "fc3"],
         "experts": ["router"] + [f"{p}{i}" for i in range(1, 5) for p in ("up", "down")]}

_STREAMS: dict[str, list] = {}


def _torch():
    import torch

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is not available")
    return torch


def _streams(key: str, k: int) -> list:
    torch = _torch()
    if key not in _STREAMS:
        _STREAMS[key] = [torch.cuda.Stream() for _ in range(k)]
    return _STREAMS[key]


def fork(fns: Sequence[Callable[[], Any]], key: str) -> list:
    """Run each fn on its own side stream, joined back on the current stream."""
    torch = _torch()
    cur = torch.cuda.current_stream()
    outs = []
    for s, fn in zip(_streams(key, len(fns)), fns):
        s.wait_stream(cur)
        with torch.cuda.stream(s):
            outs.append(fn())
    for s in _streams(key, len(fns)):
        cur.wait_stream(s)
    return outs


# ---------------------------------------------------------------- diamond


def diamond_step(a, w1, w2):
    torch = _torch()
    h = a @ w1
    b1, b2 = fork([lambda: torch.relu(h), lambda: h @ w2], "diamond")
    return b1 + b2


def diamond(size: int | None = None, dtype: str = "fp32"):
    torch = _torch()
    n = size or 1024
    g = torch.Generator(device="cuda").manual_seed(0)
    dt = {"bf16": torch.bfloat16, "fp16": torch.float16, "fp32": torch.float32}[dtype]
    a, w1, w2 = (torch.randn(n, n, device="cuda", dtype=dt, generator=g) / n**0.5 for _ in range(3))
    return diamond_step, (a, w1, w2)


# ---------------------------------------------------------------- transformer layer


def _rmsnorm(x, w, eps=1e-6):
    torch = _torch()
    xf = x.float()
    return (xf * torch.rsqrt(xf.pow(2).mean(-1, keepdim=True) + eps)).to(x.dtype) * w


def layer_step(x, wq, wk, wv, wo, wg, wu, wd, n1, n2, kc, vc):
    torch = _torch()
    import torch.nn.functional as F

    heads, _, hd = kc.shape
    t = x.shape[0]
    h = _rmsnorm(x, n1)
    q, k, v = fork([lambda: F.linear(h, wq), lambda: F.linear(h, wk), lambda: F.linear(h, wv)],
                   "qkv")
    q = q.view(t, heads, hd).transpose(0, 1)
    k = k.view(t, heads, hd).transpose(0, 1)
    v = v.view(t, heads, hd).transpose(0, 1)
    ka = torch.cat([kc, k], dim=1)
    va = torch.cat([vc, v], dim=1)
    sc = torch.bmm(q, ka.transpose(1, 2)) * hd**-0.5
    pr = torch.softmax(sc.float(), dim=-1).to(x.dtype)
    o = torch.bmm(pr, va).transpose(0, 1).reshape(t, heads * hd)
    x2 = x + F.linear(o, wo)
    h2 = _rmsnorm(x2, n2)
    gt, up = fork([lambda: F.linear(h2, wg), lambda: F.linear(h2, wu)], "gu")
    return x2 + F.linear(F.silu(gt) * up, wd)


def layer(tokens: int, hidden: int = 1024, inter: int = 4096, kv: int = 128, heads: int = 8):
    torch = _torch()
    g = torch.Generator(device="cuda").manual_seed(0)

    def r(*s, scale=1.0):
        t = torch.randn(*s, device="cuda", dtype=torch.float32, generator=g)
        return (t * scale).to(torch.bfloat16)

    s = hidden**-0.5
    params = [r(tokens, hidden), r(hidden, hidden, scale=s), r(hidden, hidden, scale=s),
              r(hidden, hidden, scale=s), r(hidden, hidden, scale=s), r(inter, hidden, scale=s),
              r(inter, hidden, scale=s), r(hidden, inter, scale=inter**-0.5),
              r(hidden).abs() + 0.5, r(hidden).abs() + 0.5,
              r(heads, kv, hidden // heads), r(heads, kv, hidden // heads)]
    return layer_step, tuple(params)


def get(name: str) -> tuple[Callable[..., Any], Sequence[Any]]:
    """Takes: a preset name. Gives: (workload, static_inputs). Raises: KeyError, RuntimeError."""
    if name == "diamond":
        return diamond()
    if name == "decode":
        return layer(1)
    if name == "prefill":
        return layer(512)
    raise KeyError(name)
