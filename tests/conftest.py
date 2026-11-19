import json
from pathlib import Path

import networkx as nx
import pytest

from cgviz.types import NodeKind

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def diamond() -> nx.DiGraph:
    data = json.loads((FIXTURES / "diamond.json").read_text())
    g = nx.DiGraph()
    for n in data["nodes"]:
        g.add_node(n["id"], kind=NodeKind(n["kind"]), name=n["name"])
    g.add_edges_from(tuple(e) for e in data["edges"])
    return g
