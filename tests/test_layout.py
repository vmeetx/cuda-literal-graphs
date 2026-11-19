import pytest

from cgviz.layout import layered_layout


def test_diamond_layers_and_determinism(diamond):
    pos = layered_layout(diamond)
    assert set(pos) == set(diamond.nodes)
    # Top-to-bottom: larger y is higher. The join must sit below both branches.
    assert pos[3][1] < pos[1][1] and pos[3][1] < pos[2][1]
    assert layered_layout(diamond) == pos
