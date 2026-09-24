"""Shared pytest fixtures."""

from __future__ import annotations

import numpy as np
import pytest

from trussgnn.fem.truss import TrussModel, canonical_triangle


@pytest.fixture
def triangle() -> TrussModel:
    """The canonical tutorial truss (nodes 0 and 1 pinned)."""
    return canonical_triangle()


@pytest.fixture
def triangle_load() -> np.ndarray:
    """100 kN downward load at the apex (node 2)."""
    loads = np.zeros((3, 2))
    loads[2, 1] = -100_000.0
    return loads
