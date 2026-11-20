"""Four experts, each on its own stream: `cgviz draw examples/experts.py:make`.

Each expert is up-projection, GELU, down-projection. The experts don't depend on each other
and are issued on four side streams, so the captured graph forks four ways after the router
and joins at the weighted sum.
"""

import torch

from cgviz.presets import ROLES as _R
from cgviz.presets import fork

ROLES = _R["experts"]   # GEMM labels, in execution order


def expert(x, up, down, gate):
    return torch.nn.functional.gelu(x @ up) @ down * gate


def step(x, router, ups, downs):
    gates = torch.softmax(x @ router, dim=-1)
    outs = fork([lambda i=i: expert(x, ups[i], downs[i], gates[:, i:i + 1])
                 for i in range(len(ups))], "experts")
    return x + torch.stack(outs).sum(0)


def make(n=4):
    g = torch.Generator(device="cuda").manual_seed(0)

    def r(*s):
        return torch.randn(*s, device="cuda", generator=g, dtype=torch.float16) / s[0] ** 0.5

    return step, (r(32, 1024), r(1024, n), [r(1024, 2048) for _ in range(n)],
                  [r(2048, 1024) for _ in range(n)])
