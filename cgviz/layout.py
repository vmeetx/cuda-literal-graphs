"""Layered layout for small DAGs."""

from __future__ import annotations

from collections.abc import Hashable

import networkx as nx


def layered_layout(g: nx.DiGraph) -> dict[Hashable, tuple[float, float]]:
    """Takes: a DAG.
    Gives: node -> (x, y), layered top-to-bottom by dependency depth, deterministic
    (nodes sorted by id).
    Raises: ValueError if the graph has a cycle.
    """
    raise NotImplementedError("TODO(veer)")
