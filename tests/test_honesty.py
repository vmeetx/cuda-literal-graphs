"""Honesty: the provenance header, the single-stream note, and no timing words in the UI."""

import io
import json
import tokenize
from pathlib import Path

from cgviz import draw, presets, show, walk
from cgviz.provenance import KERNEL_NOTE, SINGLE_STREAM_NOTE, Provenance

ROOT = Path(__file__).resolve().parents[1]


def test_header_contains_stream_count_and_context():
    h = Provenance(streams=3, gpu="GPU X", cuda="13.0", cublas="13.1.0",
                   shapes=["1x1024 @ 1024x1024"]).header()
    assert h.startswith("captured graph · 3 streams during capture · GPU X · CUDA 13.0")
    assert "cuBLAS 13.1.0" in h and "shapes: 1x1024 @ 1024x1024" in h
    assert SINGLE_STREAM_NOTE not in h


def test_single_stream_note():
    h = Provenance(streams=1).header()
    assert "1 stream during capture" in h
    assert h.splitlines()[-1] == SINGLE_STREAM_NOTE


def test_unknown_stream_count_is_marked_not_guessed():
    assert "? streams during capture" in Provenance().header()


def _string_literals(path):
    with open(path, "rb") as fh:
        for tok in tokenize.tokenize(fh.readline):
            if tok.type == tokenize.STRING:
                yield tok.string


def test_no_ui_string_says_parallel():
    """Only the single-stream note (wording the user specified) may say "parallel"; the
    README explains forks and is not UI."""
    hits = []
    for f in sorted((ROOT / "cgviz").glob("*.py")):
        for s in _string_literals(f):
            if "parallel" in s.lower() and SINGLE_STREAM_NOTE not in s:
                hits.append((f.name, s[:60]))
    assert not hits, hits


def test_captions_have_no_timing_words():
    data = json.loads((ROOT / "tests/fixtures/graphs/decode.json").read_text())
    lay, *_ = draw.layout(data, presets.ROLES["decode"], 120)
    a, _, cn, ce = draw.layout(data, presets.ROLES["decode"], 120, prefer=(lay.orient,),
                               node_gap=show.NODE_GAP[lay.orient])
    caps = {f.caption for f in walk.Walk(a, cn, ce).frames()}
    assert any(walk.FORK_NOTE in c for c in caps)
    for c in caps:
        for word in ("parallel", "concurrent", "simultaneous", "at the same time", "faster"):
            assert word not in c.lower(), c


def test_walk_pace_is_the_same_at_every_node():
    data = json.loads((ROOT / "tests/fixtures/graphs/decode.json").read_text())
    lay, *_ = draw.layout(data, presets.ROLES["decode"], 120)
    a, _, cn, ce = draw.layout(data, presets.ROLES["decode"], 120, prefer=(lay.orient,),
                               node_gap=show.NODE_GAP[lay.orient])
    w = walk.Walk(a, cn, ce)
    frames = w.frames()
    stops = {}
    for f in frames:
        for n in f.highlight:
            stops[n] = stops.get(n, 0) + 1
    final = w.final
    lengths = {k: v for k, v in stops.items() if k != final}
    assert len(set(lengths.values())) == 1, lengths


def test_static_output_is_called_captured_graph(capsys):
    from cgviz import cli

    data = json.loads((ROOT / "tests/fixtures/graphs/diamond.json").read_text())
    a = cli.build_parser().parse_args(["diamond", "--cols", "120"])
    out = cli.show_graph(a, data, presets.ROLES["diamond"], "diamond", prov=Provenance(streams=3))
    assert out.startswith("captured graph · 3 streams during capture")
    assert KERNEL_NOTE in out
