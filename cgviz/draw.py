"""Draw a graph as a matplotlib Figure."""

from __future__ import annotations

from collections.abc import Hashable

import networkx as nx
from matplotlib.figure import Figure


def draw_graph(g: nx.DiGraph, pos: dict[Hashable, tuple[float, float]]) -> Figure:
    """Takes: a DiGraph with `kind`/`name` attributes and node positions.
    Gives: a Figure with thick shapes, numbered nodes and no small text.
    Raises: KeyError if a node has no position.
    """
    raise NotImplementedError("TODO(veer)")
