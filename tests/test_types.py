import dataclasses

import pytest

from cgviz.types import NcuRow, NodeKind, TimingRow


def test_nodekind_values():
    assert [k.value for k in NodeKind] == ["kernel", "memcpy", "memset", "event", "other"]
    assert NodeKind("memcpy") is NodeKind.MEMCPY


def test_rows_fields_and_frozen():
    t = TimingRow(size=256, eager_ms=1.0, graph_ms=0.5)
    n = NcuRow(size=256, ncu_ms_default=0.4, ncu_ms_unlocked=0.3)
    assert [f.name for f in dataclasses.fields(t)] == ["size", "eager_ms", "graph_ms"]
    assert [f.name for f in dataclasses.fields(n)] == ["size", "ncu_ms_default", "ncu_ms_unlocked"]
    with pytest.raises(dataclasses.FrozenInstanceError):
        t.size = 1  # type: ignore[misc]
