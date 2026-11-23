"""Turn captured CUDA graph data into nodes and edges; classify and collapse kernels.

Input is the dict from torch.cuda.CUDAGraph.get_graph_data(). Standard library only, except
`to_digraph`, which builds a networkx graph for callers that want one.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------- classify

GEMM_PAT = re.compile(r"gemm|gemv|splitkreduce", re.I)
NORM_PARTS = ("pow_tensor_scalar", "meanops", "rsqrt")


def kind_of(node_type):
    t = (node_type or "").lower()
    if "kernel" in t:
        return "kernel"
    if "memcpy" in t or "memset" in t:
        return "mem"
    if "event" in t:
        return "event"
    return "other"


def op_of(raw):
    """Coarse op class from the (mangled or demangled) kernel name."""
    s = (raw or "").lower()
    if GEMM_PAT.search(s):
        return "splitK" if "splitkreduce" in s else "gemm"
    if "flash" in s or "attention" in s or "fmha" in s:
        return "attn"
    if "softmax" in s:
        return "softmax"
    if "catarray" in s:
        return "cat"
    if any(p in s for p in NORM_PARTS):
        return "norm"
    if "silu" in s:
        return "silu"
    if "gelu" in s:
        return "gelu"
    if "clamp" in s or "relu" in s:
        return "relu"
    if "copy" in s:
        return "copy"
    if "aunary" in s:
        return "scale"
    if "binary" in s:
        return "mul"
    if "add" in s:
        return "add"
    return "ew"


SMALL = {"norm", "silu", "gelu", "relu", "copy", "scale", "mul", "add", "ew"}  # elementwise / tiny reductions


def demangle(names):
    names = [n or "" for n in names]
    try:
        out = subprocess.run(["c++filt"], input="\n".join(names), capture_output=True,
                             text=True, check=True, timeout=5).stdout.splitlines()
        if len(out) == len(names):
            return out
    except Exception:
        pass
    return names


# ---------------------------------------------------------------- graph model


def load(data, roles=None):
    """Return nodes {id: dict} and edges set, ids renumbered 1..N in topo order."""
    raw = {n["index"]: n for n in data["nodes"]}
    deps = {i: list(n["dependencies"]) for i, n in raw.items()}
    order, seen = [], set()
    ready = sorted(i for i in raw if not deps[i])
    indeg = {i: len(deps[i]) for i in raw}
    kids = {i: [] for i in raw}
    for i, ds in deps.items():
        for d in ds:
            kids[d].append(i)
    while ready:
        i = ready.pop(0)
        order.append(i)
        seen.add(i)
        for k in sorted(kids[i]):
            indeg[k] -= 1
            if indeg[k] == 0:
                ready.append(k)
                ready.sort()
    m = {old: new + 1 for new, old in enumerate(order)}
    # names demangled where the graph was captured (saved as "demangled"), else c++filt here
    full = [raw[o].get("demangled") or raw[o].get("kernel_name") or "" for o in order]
    todo = [i for i, f in enumerate(full) if f.startswith("_Z")]
    for i, d in zip(todo, demangle([full[i] for i in todo])):
        full[i] = d
    nodes = {}
    gi = 0
    for o, f in zip(order, full):
        n = raw[o]
        kind = kind_of(n["node_type"])
        op = op_of(n.get("kernel_name")) if kind == "kernel" else n["node_type"]
        label = {"mem": "memset" if "memset" in n["node_type"].lower() else "memcpy",
                 "event": "event"}.get(kind, op)
        if op == "gemm":
            label = roles[gi] if roles and gi < len(roles) else "gemm"
            gi += 1
        nodes[m[o]] = dict(id=m[o], kind=kind, op=op, label=label, members=[m[o]],
                           full=f if n.get("kernel_name") else n["node_type"])
    edges = {(m[d], m[i]) for i, ds in deps.items() for d in ds}
    return nodes, transitive_reduction(nodes, edges)


def succ(edges):
    s = {}
    for u, v in edges:
        s.setdefault(u, set()).add(v)
    return s


def transitive_reduction(nodes, edges):
    s = succ(edges)

    def reach(u, skip):
        st, seen = [w for w in s.get(u, ()) if (u, w) != skip], set()
        while st:
            w = st.pop()
            if w in seen:
                continue
            seen.add(w)
            st.extend(s.get(w, ()))
        return seen

    return {(u, v) for u, v in edges if v not in reach(u, (u, v))}


def collapse(nodes, edges):
    """Fold runs of >=2 consecutive small elementwise kernels into one box 'norm x8'.

    A run is a straight chain (each member has one producer and one consumer inside the
    run). GEMM-type, softmax, cat, memset and event nodes are never folded.
    """
    s, p = succ(edges), {}
    for u, v in edges:
        p.setdefault(v, set()).add(u)
    rep = {}
    for n in sorted(nodes):
        pr = p.get(n, set())
        if (nodes[n]["op"] in SMALL and len(pr) == 1):
            (u,) = pr
            if nodes[u]["op"] in SMALL and len(s.get(u, ())) == 1:
                rep[n] = rep[u]
                continue
        rep[n] = n
    groups = {}
    for n, r in rep.items():
        groups.setdefault(r, []).append(n)
    out = {}
    for r, ms in groups.items():
        base = dict(nodes[r])
        if len(ms) > 1:
            ops = {nodes[m]["op"] for m in ms}
            word = next((w for w in ("norm", "silu", "gelu") if w in ops), "ew")
            base.update(label=f"{word} x{len(ms)}", members=ms, op="run")
        out[r] = base
    e2 = {(rep[u], rep[v]) for u, v in edges if rep[u] != rep[v]}
    return out, e2


def read_graph_data(source: Any | Path) -> dict:
    """Takes: a graph-data dict, or a path to a saved graph_data.json.
    Gives: the graph-data dict."""
    if isinstance(source, dict):
        return source
    p = Path(source)
    if not p.exists():
        raise FileNotFoundError(p)
    return json.loads(p.read_text(encoding="utf-8"))


def to_digraph(source: Any | Path):
    """Takes: a graph-data dict or a path to graph_data.json.
    Gives: a networkx DiGraph (ids 1..N in execution order) where every node has `kind`
    (NodeKind) and `name` (short str), with transitive edges removed.
    Raises: ValueError if the input cannot be parsed; FileNotFoundError for a missing path."""
    import networkx as nx

    from cgviz.types import NodeKind

    try:
        nodes, edges = load(read_graph_data(source))
    except (KeyError, TypeError) as e:
        raise ValueError(f"not CUDA graph data: {e}") from e
    kinds = {"kernel": NodeKind.KERNEL, "event": NodeKind.EVENT, "other": NodeKind.OTHER}
    g = nx.DiGraph()
    for n, nd in nodes.items():
        kind = kinds.get(nd["kind"])
        if nd["kind"] == "mem":
            kind = NodeKind.MEMSET if "memset" in nd["full"].lower() else NodeKind.MEMCPY
        g.add_node(n, kind=kind, name=nd["label"])
    g.add_edges_from(edges)
    return g
