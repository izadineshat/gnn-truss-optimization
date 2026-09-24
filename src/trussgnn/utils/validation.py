"""Input validation helpers shared by FEM and graph code."""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray


def as_coordinates(nodes: ArrayLike) -> NDArray[np.float64]:
    """Coerce node coordinates to a finite ``(n, 2)`` float64 array.

    Accepts lists, tuples or arrays; a single node given as ``[x, y]`` is
    reshaped to ``(1, 2)``. Raises ``ValueError`` on non-2D or non-finite input.
    """
    arr = np.asarray(nodes, dtype=np.float64)
    if arr.ndim == 1 and arr.shape[0] == 2:
        arr = arr.reshape(1, 2)
    if arr.ndim != 2 or arr.shape[1] != 2:
        raise ValueError(f"node coordinates must have shape (n, 2), got {arr.shape}")
    if arr.shape[0] == 0:
        raise ValueError("at least one node is required")
    if not np.all(np.isfinite(arr)):
        raise ValueError("node coordinates must be finite")
    return arr


def as_connectivity(elements: ArrayLike) -> NDArray[np.int64]:
    """Coerce member connectivity to an integer ``(m, 2)`` array of node ids."""
    arr = np.asarray(elements)
    if arr.ndim == 1 and arr.shape[0] == 2:
        arr = arr.reshape(1, 2)
    if arr.ndim != 2 or arr.shape[1] != 2:
        raise ValueError(f"element connectivity must have shape (m, 2), got {arr.shape}")
    if arr.shape[0] == 0:
        raise ValueError("at least one element is required")
    if not np.issubdtype(arr.dtype, np.integer) and not np.all(np.equal(np.mod(arr, 1), 0)):
        raise ValueError("element node ids must be integers")
    return arr.astype(np.int64)


def as_positive_scalar(value: float, name: str) -> float:
    """Validate that ``value`` is a finite positive scalar and return it as float."""
    val = float(value)
    if not np.isfinite(val) or val <= 0:
        raise ValueError(f"{name} must be a finite positive number, got {value}")
    return val
