"""Output directory handling and writers for already-produced objects."""

from __future__ import annotations

import csv
import dataclasses
import json
from collections.abc import Sequence
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import networkx as nx
import numpy as np
from matplotlib.figure import Figure


def make_out_dir(command: str, base: Path | str = "out", now: datetime | None = None) -> Path:
    """Create and return out/<command>-<YYYYmmdd-HHMMSS>/ (suffixed if it exists)."""
    stamp = (now or datetime.now()).strftime("%Y%m%d-%H%M%S")
    root = Path(base)
    path = root / f"{command}-{stamp}"
    n = 1
    while path.exists():
        path = root / f"{command}-{stamp}-{n}"
        n += 1
    path.mkdir(parents=True)
    return path


def _plain(v: Any) -> Any:
    if isinstance(v, Enum):
        return v.value
    if isinstance(v, (str, int, float, bool)) or v is None:
        return v
    return str(v)


def write_graph_json(g: nx.DiGraph, path: Path) -> Path:
    """Write nodes (id, kind, name) and edges (src, dst) as JSON."""
    data = {
        "nodes": [
            {"id": _plain(n), "kind": _plain(a.get("kind")), "name": _plain(a.get("name"))}
            for n, a in g.nodes(data=True)
        ],
        "edges": [[_plain(u), _plain(v)] for u, v in g.edges()],
    }
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return path


def read_graph_json(path: Path) -> dict[str, Any]:
    """Read a graph.json back as a plain dict."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_grid_txt(chars: np.ndarray, path: Path) -> Path:
    """Write a char grid as plain text, one row per line."""
    lines = ["".join(str(c) for c in row) for row in np.asarray(chars)]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_grid_ans(chars: np.ndarray, colours: np.ndarray, path: Path) -> Path:
    """Write a char grid with 24-bit ANSI foreground colours.

    `colours` has shape (rows, cols, 3) with 0-255 RGB values.
    """
    chars = np.asarray(chars)
    colours = np.asarray(colours)
    if colours.shape[:2] != chars.shape:
        raise ValueError(f"colour shape {colours.shape} does not match grid {chars.shape}")
    out = []
    for r in range(chars.shape[0]):
        parts = []
        for c in range(chars.shape[1]):
            red, green, blue = (int(x) for x in colours[r, c][:3])
            parts.append(f"\x1b[38;2;{red};{green};{blue}m{chars[r, c]}")
        out.append("".join(parts) + "\x1b[0m")
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return path


def write_csv(rows: Sequence[Any], path: Path) -> Path:
    """Write a sequence of dataclass rows as CSV with a header."""
    if not rows:
        raise ValueError("no rows to write")
    fields = [f.name for f in dataclasses.fields(rows[0])]
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow(dataclasses.asdict(row))
    return path


def write_figure_png(fig: Figure, path: Path, dpi: int = 100) -> Path:
    """Save a Figure as PNG."""
    fig.savefig(path, dpi=dpi)
    return path
