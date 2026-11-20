"""A 3-layer MLP on one stream: `cgviz draw examples/mlp.py:make`.

Everything runs on the default stream, so every kernel waits for the one before it and the
captured graph is a plain chain. No forks: a single stream gives no parallelism to show.
"""

import torch

from cgviz.presets import ROLES as _R

ROLES = _R["mlp"]   # GEMM labels, in execution order


def step(x, w1, w2, w3):
    h = torch.nn.functional.gelu(x @ w1)
    h = torch.nn.functional.gelu(h @ w2)
    return h @ w3


def make():
    g = torch.Generator(device="cuda").manual_seed(0)

    def r(*s):
        return torch.randn(*s, device="cuda", generator=g, dtype=torch.float16) / s[0] ** 0.5

    return step, (r(64, 1024), r(1024, 4096), r(4096, 4096), r(4096, 1024))
