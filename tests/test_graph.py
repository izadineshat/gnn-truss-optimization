"""Graph-conversion tests (roadmap step 6), mirroring week1/truss_week1.py."""

from __future__ import annotations

import numpy as np
import pytest

from trussgnn.graph.convert import (
    adjacency_matrix,
    degree_matrix,
    edge_attributes,
    edge_index,
    laplacian_matrix,
    normalized_laplacian,
    truss_to_graph,
)

NODES = np.array([[0.0, 0.0], [4.0, 0.0], [2.0, 3.0]])
ELEMENTS = np.array([[0, 1], [1, 2], [2, 0]])
AREAS = np.array([0.002, 0.0015, 0.001])


def test_edge_index_is_bidirectional_and_matches_tutorial() -> None:
    """Same layout as the hand-written edge_index in week1/truss_week1.py."""
    expected = np.array([[0, 1, 2, 1, 2, 0], [1, 2, 0, 0, 1, 2]])
    assert np.array_equal(edge_index(ELEMENTS), expected)
    assert edge_index(ELEMENTS).shape == (2, 6)


def test_adjacency_of_triangle_is_complete_graph() -> None:
    expected = np.array([[0, 1, 1], [1, 0, 1], [1, 1, 0]])
    assert np.array_equal(adjacency_matrix(ELEMENTS), expected)


def test_degree_matrix_has_degree_two_nodes() -> None:
    assert np.array_equal(np.diag(degree_matrix(ELEMENTS)), np.array([2, 2, 2]))


def test_laplacian_row_sums_are_zero() -> None:
    """L = D - A; a constant vector is in its null space."""
    lap = laplacian_matrix(ELEMENTS)
    assert np.array_equal(lap, np.array([[2, -1, -1], [-1, 2, -1], [-1, -1, 2]]))
    assert np.allclose(lap.sum(axis=1), 0)
    assert np.allclose(lap @ np.ones(3), 0)


def test_normalized_laplacian_eigenvalues_in_range() -> None:
    """For a connected graph, eigenvalues of L_sym lie in [0, 2]."""
    nlap = normalized_laplacian(ELEMENTS)
    eigenvalues = np.linalg.eigvalsh(nlap)
    assert eigenvalues[0] == pytest.approx(0.0, abs=1e-12)
    assert eigenvalues.max() <= 2.0 + 1e-12
    assert np.allclose(nlap, nlap.T)


def test_isolated_node_keeps_zero_row_in_normalized_laplacian() -> None:
    """A degree-0 node must not produce NaNs (division guarded)."""
    elements = np.array([[0, 1]])
    nlap = normalized_laplacian(elements, num_nodes=3)
    assert np.all(np.isfinite(nlap))
    # SciPy convention: an isolated vertex keeps a diagonal of 1 in L_sym
    assert np.allclose(nlap[2], [0.0, 0.0, 1.0])


def test_edge_attributes_repeat_each_area_twice() -> None:
    attrs = edge_attributes(ELEMENTS, AREAS)
    assert attrs.shape == (6, 1)
    assert np.allclose(attrs.ravel(), [0.002, 0.0015, 0.001, 0.002, 0.0015, 0.001])


def test_truss_to_graph_bundles_everything() -> None:
    graph = truss_to_graph(NODES, ELEMENTS, AREAS)
    assert graph.x.shape == (3, 2)
    assert np.allclose(graph.x, NODES)
    assert graph.edge_index.shape == (2, 6)
    assert graph.edge_attr.shape == (6, 1)
    assert graph.adjacency.shape == (3, 3)
    assert graph.laplacian.shape == (3, 3)
    assert graph.normalized_laplacian.shape == (3, 3)


def test_graph_view_is_consistent_with_fem_model() -> None:
    """The truss->graph route and the FEM route must agree on node/edge counts."""
    from trussgnn.fem.truss import canonical_triangle

    model = canonical_triangle()
    graph = truss_to_graph(model.nodes, model.elements, model.areas)
    assert graph.x.shape[0] == model.num_nodes
    assert graph.edge_index.shape[1] == 2 * model.num_elements


def test_number_of_edges_equals_sum_of_degrees() -> None:
    graph = truss_to_graph(NODES, ELEMENTS, AREAS)
    assert graph.edge_index.shape[1] == int(graph.adjacency.sum())
