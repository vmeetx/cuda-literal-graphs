"""Plots for timing and ncu rows."""

from __future__ import annotations

from collections.abc import Sequence

from matplotlib.figure import Figure

from cgviz.types import NcuRow, TimingRow


def plot_rows(rows: Sequence[TimingRow] | Sequence[NcuRow]) -> Figure:
    """Takes: timing rows or ncu rows.
    Gives: a Figure plotting them against size.
    Raises: ValueError if rows is empty.
    """
    raise NotImplementedError("TODO(veer)")
