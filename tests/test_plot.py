"""Plot helpers return a Figure and draw without a display (Agg backend)."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")  # headless backend, no window popping in tests

import pytest
from matplotlib.figure import Figure

from trussgnn.fem.truss import TrussResult, solve_tutorial
from trussgnn.plot import plot_deformed, plot_member_stress


@pytest.fixture
def result() -> TrussResult:
    return solve_tutorial()


def test_plot_deformed_returns_figure(result: TrussResult) -> None:
    figure = plot_deformed(result)
    assert isinstance(figure, Figure)
    assert len(figure.axes) == 1


def test_plot_member_stress_returns_figure(result: TrussResult) -> None:
    figure = plot_member_stress(result)
    assert isinstance(figure, Figure)
    # one axes holding original + deformed members
    assert len(figure.axes[0].lines) >= 3


def test_plots_accept_existing_axes(result: TrussResult) -> None:
    import matplotlib.pyplot as plt

    figure, ax = plt.subplots()
    fig2 = plot_deformed(result, ax=ax)
    fig3 = plot_member_stress(result, ax=ax)
    assert fig2 is figure
    assert fig3 is figure
