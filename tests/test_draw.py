import pytest
from matplotlib.figure import Figure
from matplotlib.text import Text

from cgviz.draw import draw_graph

MIN_FONT_PT = 14


@pytest.mark.xfail(strict=False, reason="TODO(veer)")
def test_returns_figure_without_small_text(diamond):
    pos = {0: (1.0, 2.0), 1: (0.0, 1.0), 2: (2.0, 1.0), 3: (1.0, 0.0)}
    fig = draw_graph(diamond, pos)
    assert isinstance(fig, Figure)
    texts = [t for t in fig.findobj(Text) if t.get_text().strip()]
    assert all(t.get_fontsize() >= MIN_FONT_PT for t in texts)
