"""Plotting helpers (matplotlib).

Kept in a separate module so the FEM core stays import-light: ``matplotlib`` is
imported lazily inside the functions. Member colour encodes tension (positive,
red) versus compression (negative, blue) — roadmap step 4.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:  # pragma: no cover - typing only
    from matplotlib.figure import Figure

    from trussgnn.fem.truss import TrussResult


def plot_deformed(result: TrussResult, scale: float = 500.0, ax: object | None = None) -> Figure:
    """Plot original vs. deformed shape, ported from ``truss_analysis.py``.

    Args:
        result: output of :func:`trussgnn.fem.truss.solve_truss`.
        scale: displacement exaggeration factor (the tutorial used 500).
        ax: optional existing ``matplotlib.axes.Axes`` to draw into.

    Returns:
        The matplotlib ``Figure`` holding the plot.
    """
    import matplotlib.pyplot as plt

    model = result.model
    nodes = model.nodes
    deformed = model.nodes + result.displacement * scale

    created = ax is None
    if created:
        _, ax = plt.subplots(figsize=(10, 6))
    assert ax is not None

    for i, j in model.elements:
        ax.plot(  # type: ignore[attr-defined]
            [nodes[i, 0], nodes[j, 0]],
            [nodes[i, 1], nodes[j, 1]],
            "k--",
            alpha=0.35,
            linewidth=1.0,
        )
    for i, j in model.elements:
        ax.plot(  # type: ignore[attr-defined]
            [deformed[i, 0], deformed[j, 0]],
            [deformed[i, 1], deformed[j, 1]],
            "r-o",
            linewidth=2.0,
        )
    ax.set_title(f"Truss analysis — deformed shape (scale ×{scale:g})")  # type: ignore[attr-defined]
    ax.set_xlabel("X (m)")  # type: ignore[attr-defined]
    ax.set_ylabel("Y (m)")  # type: ignore[attr-defined]
    ax.grid(True)  # type: ignore[attr-defined]
    ax.axis("equal")  # type: ignore[attr-defined]
    if created:
        plt.tight_layout()
    return ax.figure  # type: ignore[attr-defined,no-any-return]


def plot_member_stress(result: TrussResult, ax: object | None = None) -> Figure:
    """Colour members by axial stress sign: tension (red) vs compression (blue)."""
    import matplotlib.pyplot as plt
    from matplotlib.colors import Normalize

    model = result.model
    stresses = result.stresses
    limit = float(np.max(np.abs(stresses))) if stresses.size else 1.0
    normalizer = Normalize(vmin=-limit, vmax=limit)

    created = ax is None
    if created:
        _, ax = plt.subplots(figsize=(10, 6))
    assert ax is not None

    cmap = plt.get_cmap("coolwarm")
    for m, (i, j) in enumerate(model.elements):
        ax.plot(  # type: ignore[attr-defined]
            [model.nodes[i, 0], model.nodes[j, 0]],
            [model.nodes[i, 1], model.nodes[j, 1]],
            color=cmap(normalizer(stresses[m])),
            linewidth=3.0,
        )
    ax.scatter(model.nodes[:, 0], model.nodes[:, 1], c="k", zorder=3)  # type: ignore[attr-defined]
    ax.set_title("Axial stress (red = tension, blue = compression)")  # type: ignore[attr-defined]
    ax.set_xlabel("X (m)")  # type: ignore[attr-defined]
    ax.set_ylabel("Y (m)")  # type: ignore[attr-defined]
    ax.axis("equal")  # type: ignore[attr-defined]
    ax.grid(True, alpha=0.3)  # type: ignore[attr-defined]
    if created:
        plt.tight_layout()
    return ax.figure  # type: ignore[attr-defined,no-any-return]


__all__ = ["plot_deformed", "plot_member_stress"]
