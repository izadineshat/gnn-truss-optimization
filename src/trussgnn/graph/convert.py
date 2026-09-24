"""Truss -> graph helpers used by roadmap step 6.

A 2D truss is an undirected graph: nodes are joints with feature ``[x, y]``,
members are edges with feature ``[A_i]``. ``edge_index`` follows the
PyTorch Geometric convention (two rows: source / target).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from trussgnn.utils.validation import as_connectivity, as_coordinates


def edge_index(elements: NDArray[np.int64]) -> NDArray[np.int64]:
    """Return the two-row ``edge_index`` (bidirectional, PyG convention).

    Each member ``(i, j)`` appears twice: ``(i, j)`` and ``(j, i)``, mirroring
    the hand-written example in ``week1/truss_week1.py``.
    """
    forward = elements.T  # (2, E) from (E, 2)
    backward = forward[::-1, :]
    return np.concatenate([forward, backward], axis=1)


def adjacency_matrix(
    elements: NDArray[np.int64], num_nodes: int | None = None
) -> NDArray[np.int64]:
    """Binary adjacency ``A`` with ``A[i, j] = 1`` iff a member joins i and j."""
    elements = as_connectivity(elements)
    if num_nodes is None:
        num_nodes = int(elements.max()) + 1
    adj = np.zeros((num_nodes, num_nodes), dtype=np.int64)
    for i, j in elements:
        adj[i, j] = 1
        adj[j, i] = 1
    return adj


def degree_matrix(elements: NDArray[np.int64], num_nodes: int | None = None) -> NDArray[np.int64]:
    """Diagonal degree matrix ``D`` (count of incident members per node)."""
    adj = adjacency_matrix(elements, num_nodes)
    return np.diag(adj.sum(axis=1))


def laplacian_matrix(
    elements: NDArray[np.int64], num_nodes: int | None = None
) -> NDArray[np.int64]:
    """Unnormalized graph Laplacian ``L = D - A`` (row sums are zero)."""
    adj = adjacency_matrix(elements, num_nodes)
    return np.diag(adj.sum(axis=1)) - adj


def normalized_laplacian(
    elements: NDArray[np.int64], num_nodes: int | None = None
) -> NDArray[np.float64]:
    """Symmetric normalized Laplacian ``L_sym = I - D^{-1/2} A D^{-1/2}``.

    Nodes of degree zero keep a zero row/column (as in SciPy's
    ``normalized_laplacian``).
    """
    adj = adjacency_matrix(elements, num_nodes).astype(np.float64)
    deg = adj.sum(axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        inv_sqrt = np.where(deg > 0, 1.0 / np.sqrt(deg), 0.0)
    eye = np.eye(adj.shape[0])
    return eye - (inv_sqrt[:, None] * adj) * inv_sqrt[None, :]


def edge_attributes(elements: NDArray[np.int64], areas: NDArray[np.float64]) -> NDArray[np.float64]:
    """Per-edge feature matrix for PyG ``edge_attr``, one row per directed edge.

    Row order follows :func:`edge_index` (each member twice: forward, then
    backward), matching the tutorial's hand-built ``edge_attr``.
    """
    column = np.asarray(areas, dtype=np.float64).reshape(-1, 1)
    # forward edges (members 0..E-1), then backward edges (members 0..E-1)
    return np.concatenate([column, column], axis=0)


@dataclass(frozen=True)
class TrussGraph:
    """Graph view of a truss, ready for a GNN (roadmap step 6).

    Attributes:
        x: ``(n_nodes, 2)`` node features ``[x, y]``.
        edge_index: ``(2, 2·E)`` bidirectional edge list.
        edge_attr: ``(2·E, 1)`` area per directed edge.
        adjacency: binary adjacency matrix.
        laplacian: unnormalized Laplacian.
        normalized_laplacian: symmetric normalized Laplacian.
    """

    x: NDArray[np.float64]
    edge_index: NDArray[np.int64]
    edge_attr: NDArray[np.float64]
    adjacency: NDArray[np.int64]
    laplacian: NDArray[np.int64]
    normalized_laplacian: NDArray[np.float64]


def truss_to_graph(
    nodes: NDArray[np.float64], elements: NDArray[np.int64], areas: NDArray[np.float64]
) -> TrussGraph:
    """Build the full graph view of a truss in one call."""
    elements = as_connectivity(elements)
    nodes = as_coordinates(nodes)
    return TrussGraph(
        x=nodes.astype(np.float64),
        edge_index=edge_index(elements),
        edge_attr=edge_attributes(elements, areas),
        adjacency=adjacency_matrix(elements, nodes.shape[0]),
        laplacian=laplacian_matrix(elements, nodes.shape[0]),
        normalized_laplacian=normalized_laplacian(elements, nodes.shape[0]),
    )
