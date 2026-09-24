"""Tutorial truss tests: assembly, symmetry, equilibrium and hand-checked forces."""

from __future__ import annotations

import numpy as np
import pytest

from trussgnn.fem.truss import (
    TrussModel,
    assemble_global_stiffness,
    canonical_triangle,
    solve_truss,
    solve_tutorial,
)

# --- hand calculation for the canonical truss (100 kN down at apex) -----------
# Members: (0,1) horizontal L=4, (2,0) and (1,2) length L=sqrt(4+9)=sqrt(13).
# Apex node 2 has members at angles ±atan(3/2) from horizontal. Vertical
# equilibrium of the apex: 2·N·sin(θ) = -100 kN -> N = -100e3 / (2·(3/√13))
L_DIAG = float(np.hypot(2.0, 3.0))
SIN_THETA = 3.0 / L_DIAG
N_DIAGONAL = -100_000.0 / (2.0 * SIN_THETA)


def test_global_stiffness_is_symmetric_and_singular_free(triangle: TrussModel) -> None:
    k = assemble_global_stiffness(triangle)
    assert k.shape == (6, 6)
    assert np.allclose(k, k.T)

    free = triangle.free_dofs
    k_ff = k[np.ix_(free, free)]
    assert np.linalg.matrix_rank(k_ff) == free.size
    assert np.all(np.linalg.eigvalsh(k_ff) > 0)


def test_row_sums_of_stiffness_are_zero(triangle: TrussModel) -> None:
    """Translational rigid-body modes -> every row of K sums to zero."""
    k = assemble_global_stiffness(triangle)
    assert np.allclose(k.sum(axis=1), 0.0, atol=1e-3)
    assert np.allclose(k.sum(axis=0), 0.0, atol=1e-3)


def test_tutorial_displacements_are_small_and_downward(
    triangle: TrussModel, triangle_load: np.ndarray
) -> None:
    result = solve_truss(triangle, triangle_load)
    assert result.displacement[2, 1] < 0  # apex moves down
    assert result.displacement[2, 0] == pytest.approx(0.0, abs=1e-12)  # symmetry
    assert np.all(result.displacement[:2] == 0.0)  # supports


def test_diagonal_members_are_in_compression(
    triangle: TrussModel, triangle_load: np.ndarray
) -> None:
    """Hand check: both inclined members carry N = -F / (2·sinθ)."""
    result = solve_truss(triangle, triangle_load)
    assert result.axial_forces[1] == pytest.approx(N_DIAGONAL, rel=1e-9)
    assert result.axial_forces[2] == pytest.approx(N_DIAGONAL, rel=1e-9)
    assert result.axial_forces[1] < 0 and result.axial_forces[2] < 0


def test_symmetric_members_have_equal_force_and_stress(
    triangle: TrussModel, triangle_load: np.ndarray
) -> None:
    """Golden rule #1: a symmetric truss under a symmetric load has equal twins."""
    result = solve_truss(triangle, triangle_load)
    assert result.axial_forces[1] == pytest.approx(result.axial_forces[2])
    assert result.stresses[1] == pytest.approx(result.stresses[2])


def test_horizontal_member_carries_no_force(
    triangle: TrussModel, triangle_load: np.ndarray
) -> None:
    """The bottom chord is unstressed for a purely vertical apex load."""
    result = solve_truss(triangle, triangle_load)
    assert result.axial_forces[0] == pytest.approx(0.0, abs=1e-6)


def test_support_reactions_sum_to_applied_load(
    triangle: TrussModel, triangle_load: np.ndarray
) -> None:
    """ΣR_y = +100 kN upward; horizontal reactions cancel by symmetry."""
    result = solve_truss(triangle, triangle_load)
    assert result.reactions[:, 1].sum() == pytest.approx(100_000.0, rel=1e-9)
    assert result.reactions[0, 0] == pytest.approx(-result.reactions[1, 0], rel=1e-9)
    assert result.equilibrium_error < 1e-9


def test_stress_equals_force_over_area(triangle: TrussModel, triangle_load: np.ndarray) -> None:
    result = solve_truss(triangle, triangle_load)
    assert np.allclose(result.stresses, result.axial_forces / triangle.areas)
    assert np.allclose(result.deformed_nodes, triangle.nodes + result.displacement)
    assert result.max_stress == pytest.approx(float(np.max(np.abs(result.stresses))))


def test_member_result_reports_length_and_state(
    triangle: TrussModel, triangle_load: np.ndarray
) -> None:
    result = solve_truss(triangle, triangle_load)
    diagonal = result.member_result(1)
    assert diagonal["length_m"] == pytest.approx(L_DIAG)
    assert diagonal["axial_force_N"] == pytest.approx(N_DIAGONAL)
    chord = result.member_result(0)
    assert chord["length_m"] == pytest.approx(4.0)


def test_scale_invariance_of_stress_under_load_scaling(triangle: TrussModel) -> None:
    """Linear elasticity: doubling the load doubles forces and stresses exactly."""
    base = np.zeros((3, 2))
    base[2, 1] = -100_000.0
    doubled = base * 2.0
    r1 = solve_truss(triangle, base)
    r2 = solve_truss(triangle, doubled)
    assert np.allclose(r2.axial_forces, 2 * r1.axial_forces, rtol=1e-9)
    assert np.allclose(r2.displacement, 2 * r1.displacement, rtol=1e-9)


def test_areas_scalar_is_broadcast_to_all_members() -> None:
    model = TrussModel(
        nodes=np.array([[0.0, 0.0], [4.0, 0.0], [2.0, 3.0]]),
        elements=np.array([[0, 1], [1, 2], [2, 0]]),
        areas=np.array(0.01),
        fixed_dofs=np.array([0, 1, 2, 3]),
    )
    assert model.areas.shape == (3,)
    assert np.allclose(model.areas, 0.01)


def test_solve_tutorial_end_to_end_matches_canonical_model() -> None:
    result = solve_tutorial()
    reference = solve_truss(canonical_triangle(), np.array([[0, 0], [0, 0], [0, -100_000.0]]))
    assert np.allclose(result.displacement, reference.displacement)
    assert result.equilibrium_error < 1e-9
    assert result.stresses[1] < 0
