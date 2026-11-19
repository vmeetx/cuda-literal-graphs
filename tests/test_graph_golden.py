"""Golden-file tests for the literal graph drawing (cgviz/braille.py, legacy).

Run with UPDATE_GOLDEN=1 to accept a deliberate layout change.
"""

import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
from cgviz import braille as graphdraw  # noqa: E402

ROLES = ["Q", "K", "V", "QK", "PV", "O", "gate", "up", "down"]
GOLDEN = Path(__file__).parent / "golden"


def picture(preset):
    data = json.loads((Path(__file__).parent / "fixtures/graphs" / f"{preset}.json").read_text())
    cells, _, _ = graphdraw.draw(data, 100, 30, roles=ROLES)
    return graphdraw.to_text(cells) + "\n"


@pytest.mark.parametrize("preset", ["decode", "prefill"])
def test_golden(preset):
    got = picture(preset)
    path = GOLDEN / f"{preset}_100x30.txt"
    if os.environ.get("UPDATE_GOLDEN") or not path.exists():
        path.write_text(got, encoding="utf-8")
    assert got == path.read_text(encoding="utf-8")


@pytest.mark.parametrize("preset", ["decode", "prefill"])
def test_fits_100x30(preset):
    lines = picture(preset).rstrip("\n").split("\n")
    assert len(lines) <= 30 and max(len(x) for x in lines) <= 100


def test_gemm_never_collapsed():
    data = json.loads((Path(__file__).parent / "fixtures/graphs/decode.json").read_text())
    nodes, edges = graphdraw.load(data, ROLES)
    cn, _ = graphdraw.collapse(nodes, edges)
    for nd in cn.values():
        if len(nd["members"]) > 1:
            assert all(nodes[m]["op"] in graphdraw.SMALL for m in nd["members"])
