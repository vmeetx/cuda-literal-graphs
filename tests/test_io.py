import csv
from datetime import datetime

import numpy as np
import pytest
from matplotlib.figure import Figure

from cgviz import io
from cgviz.types import TimingRow


def test_make_out_dir_name_and_collision(tmp_path):
    now = datetime(2026, 1, 2, 3, 4, 5)
    a = io.make_out_dir("demo", base=tmp_path, now=now)
    b = io.make_out_dir("demo", base=tmp_path, now=now)
    assert a.name == "demo-20260102-030405" and a.is_dir()
    assert b != a and b.is_dir()


def test_graph_json_roundtrip(tmp_path, diamond):
    p = io.write_graph_json(diamond, tmp_path / "graph.json")
    data = io.read_graph_json(p)
    assert len(data["nodes"]) == 4
    assert {n["kind"] for n in data["nodes"]} == {"kernel"}
    assert [n["name"] for n in data["nodes"]] == ["gemm", "relu", "gemm", "add"]
    assert sorted(map(tuple, data["edges"])) == [(0, 1), (0, 2), (1, 3), (2, 3)]


def test_grid_txt_and_ans(tmp_path):
    chars = np.array([["a", "b"], ["c", "d"]])
    colours = np.zeros((2, 2, 3), dtype=np.uint8)
    colours[0, 0] = (255, 0, 0)
    txt = io.write_grid_txt(chars, tmp_path / "grid.txt").read_text(encoding="utf-8")
    assert txt == "ab\ncd\n"
    ans = io.write_grid_ans(chars, colours, tmp_path / "grid.ans").read_text(encoding="utf-8")
    assert "\x1b[38;2;255;0;0ma" in ans
    assert ans.count("\x1b[0m") == 2


def test_grid_ans_shape_mismatch(tmp_path):
    with pytest.raises(ValueError):
        io.write_grid_ans(np.array([["a"]]), np.zeros((2, 2, 3)), tmp_path / "x.ans")


def test_csv(tmp_path):
    rows = [TimingRow(256, 1.0, 0.5), TimingRow(512, 2.0, 1.0)]
    p = io.write_csv(rows, tmp_path / "timing.csv")
    with p.open() as fh:
        got = list(csv.DictReader(fh))
    assert got[0] == {"size": "256", "eager_ms": "1.0", "graph_ms": "0.5"}
    assert len(got) == 2
    with pytest.raises(ValueError):
        io.write_csv([], tmp_path / "empty.csv")


def test_figure_png(tmp_path):
    fig = Figure()
    fig.add_subplot().plot([0, 1], [0, 1])
    p = io.write_figure_png(fig, tmp_path / "figure.png")
    assert p.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
