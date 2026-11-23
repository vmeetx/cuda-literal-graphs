"""Two Llama-style decoder layers generating one token, at TinyLlama size:
`cgviz draw examples/llama_decode.py:make`.

Closer to a real model than the decode preset: hidden 2048, 32 query heads sharing 4 KV heads
(grouped-query attention), rotary position embeddings, a preallocated KV cache written in
place, PyTorch's fused scaled-dot-product attention, and SwiGLU. Everything runs on one
stream, as a normal model does, so the captured graph is a chain.
"""

import torch
import torch.nn.functional as F

HIDDEN, HEADS, KV_HEADS, INTER, CTX, POS = 2048, 32, 4, 5632, 512, 300
HD = HIDDEN // HEADS
ROLES = [r for _ in range(2) for r in ("q", "k", "v", "o", "gate", "up", "down")]


def rms(x, w, eps=1e-5):
    xf = x.float()
    return (xf * torch.rsqrt(xf.pow(2).mean(-1, keepdim=True) + eps)).to(x.dtype) * w


def rope(x, cos, sin):
    a, b = x[..., : HD // 2], x[..., HD // 2:]
    return x * cos + torch.cat([-b, a], dim=-1) * sin


def layer(x, p, kc, vc, cos, sin):
    h = rms(x, p["n1"])
    q = F.linear(h, p["q"]).view(1, HEADS, 1, HD)
    k = F.linear(h, p["k"]).view(1, KV_HEADS, 1, HD)
    v = F.linear(h, p["v"]).view(1, KV_HEADS, 1, HD)
    q, k = rope(q, cos, sin), rope(k, cos, sin)
    kc[:, :, POS:POS + 1] = k                       # write this token into the cache
    vc[:, :, POS:POS + 1] = v
    o = F.scaled_dot_product_attention(q, kc[:, :, :POS + 1], vc[:, :, :POS + 1],
                                       enable_gqa=True)
    x = x + F.linear(o.reshape(1, HIDDEN), p["o"])
    h = rms(x, p["n2"])
    return x + F.linear(F.silu(F.linear(h, p["gate"])) * F.linear(h, p["up"]), p["down"])


def step(x, params, caches, cos, sin):
    for p, (kc, vc) in zip(params, caches):
        x = layer(x, p, kc, vc, cos, sin)
    return x


def make(layers=2):
    g = torch.Generator(device="cuda").manual_seed(0)

    def r(*s, scale=None):
        t = torch.randn(*s, device="cuda", generator=g, dtype=torch.float32)
        return (t * (scale if scale is not None else s[-1] ** -0.5)).to(torch.bfloat16)

    params = [dict(q=r(HIDDEN, HIDDEN), k=r(KV_HEADS * HD, HIDDEN), v=r(KV_HEADS * HD, HIDDEN),
                   o=r(HIDDEN, HIDDEN), gate=r(INTER, HIDDEN), up=r(INTER, HIDDEN),
                   down=r(HIDDEN, INTER), n1=r(HIDDEN, scale=0.1) + 1, n2=r(HIDDEN, scale=0.1) + 1)
              for _ in range(layers)]
    caches = [(r(1, KV_HEADS, CTX, HD, scale=1.0), r(1, KV_HEADS, CTX, HD, scale=1.0))
              for _ in range(layers)]
    ang = POS / 10000 ** (torch.arange(0, HD, 2, device="cuda").float() / HD)
    cos = torch.cat([ang.cos(), ang.cos()]).to(torch.bfloat16)
    sin = torch.cat([ang.sin(), ang.sin()]).to(torch.bfloat16)
    return step, (r(1, HIDDEN, scale=1.0), params, caches, cos, sin)
