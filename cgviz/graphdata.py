"""Turn a captured graph into a networkx DiGraph."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import networkx as nx


def to_digraph(source: Any | Path) -> nx.DiGraph:
    """Takes: a captured graph object or a path to a .dot dump.
    Gives: a DiGraph where every node has `kind` (NodeKind) and `name` (short str).
    Raises: ValueError if the input cannot be parsed; FileNotFoundError for a missing path.
    """
    raise NotImplementedError("TODO(veer)")
