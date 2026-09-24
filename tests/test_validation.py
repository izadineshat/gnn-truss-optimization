"""Tests for shared validation helpers."""

from __future__ import annotations

import numpy as np
import pytest

from trussgnn.utils.validation import as_connectivity, as_coordinates, as_positive_scalar


def test_as_coordinates_accepts_2x2_and_single_tuple() -> None:
    matrix = as_coordinates([[0, 0], [4, 0]])
    assert matrix.shape == (2, 2)
    single = as_coordinates((5.0, 3.0))
    assert single.shape == (1, 2)


@pytest.mark.parametrize("bad", [[[0, 0, 0]], [[0], [1]], [[np.nan, 0]], [[np.inf, 0]]])
def test_as_coordinates_rejects_bad_shapes(bad: list[list[float]]) -> None:
    with pytest.raises(ValueError):
        as_coordinates(bad)


def test_as_coordinates_rejects_empty() -> None:
    with pytest.raises(ValueError):
        as_coordinates([])


def test_as_connectivity_rejects_empty_and_bad_shapes() -> None:
    with pytest.raises(ValueError):
        as_connectivity([])
    with pytest.raises(ValueError):
        as_connectivity([[0, 1, 2]])


def test_as_connectivity_rejects_non_integer_ids() -> None:
    with pytest.raises(ValueError):
        as_connectivity([[0.5, 1.0]])


def test_as_connectivity_accepts_single_pair_and_float_integers() -> None:
    single = as_connectivity((0, 1))
    assert single.shape == (1, 2)
    cast = as_connectivity(np.array([[0.0, 1.0]]))
    assert np.issubdtype(cast.dtype, np.integer)


@pytest.mark.parametrize("bad", [0.0, -1.0, float("nan"), float("inf")])
def test_as_positive_scalar_rejects_non_positive(bad: float) -> None:
    with pytest.raises(ValueError):
        as_positive_scalar(bad, "x")


def test_as_positive_scalar_returns_float() -> None:
    assert as_positive_scalar(2, "x") == 2.0
