"""Single-member checks against hand calculations (roadmap golden rule #1).

A bar with ``E``, ``A``, ``L`` fixed at one end and pulled with ``F`` at the
other must satisfy ``u = F·L / (E·A)``, ``N = F`` and ``σ = F/A``.
"""

from __future__ import annotations

import numpy as np
import pytest

from trussgnn.fem.truss import TrussModel, element_stiffness, solve_truss

E = 200e9
A = 1e-4
L = 2.0


def _bar_model() -> TrussModel:
    return TrussModel(
        nodes=np.array([[0.0, 0.0], [L, 0.0]]),
        elements=np.array([[0, 1]]),
        elasticity=E,
        areas=np.array([A]),
        fixed_dofs=np.array([0, 1, 3]),  # node 0 pinned, node 1 held in y
    )


def test_element_stiffness_matches_k_ea_over_l() -> None:
    """k = EA/L, with the classic 2x2 single-DOF pattern embedded."""
    k = element_stiffness([0.0, 0.0], [L, 0.0], E, A)
    expected = E * A / L
    assert k.shape == (4, 4)
    assert k[0, 0] == pytest.approx(expected)
    assert k[0, 2] == pytest.approx(-expected)
    assert k[2, 2] == pytest.approx(expected)


def test_axial_bar_displacement_force_and_stress() -> None:
    """u = FL/EA = 100 N · 2 m / (200 GPa · 1e-4 m²) = 1e-5 m."""
    model = _bar_model()
    loads = np.array([[0.0, 0.0], [100.0, 0.0]])
    result = solve_truss(model, loads)

    expected_u = 100.0 * L / (E * A)
    assert result.displacement[1, 0] == pytest.approx(expected_u)
    assert result.displacement[1, 1] == pytest.approx(0.0)
    assert result.axial_forces[0] == pytest.approx(100.0)  # tension
    assert result.stresses[0] == pytest.approx(100.0 / A)  # 1 MPa
    assert result.element_strains[0] == pytest.approx(expected_u / L)


def test_axial_bar_reaction_balances_applied_load() -> None:
    """Reaction at the fixed end is -F; equilibrium residual is ~0."""
    model = _bar_model()
    loads = np.array([[0.0, 0.0], [100.0, 0.0]])
    result = solve_truss(model, loads)

    assert result.reactions[0, 0] == pytest.approx(-100.0)
    assert result.equilibrium_error < 1e-10


def test_compression_bar_has_negative_force_and_stress() -> None:
    """A pushed bar shows compression: N < 0, σ < 0 (roadmap sign convention)."""
    model = _bar_model()
    loads = np.array([[0.0, 0.0], [-100.0, 0.0]])
    result = solve_truss(model, loads)

    assert result.axial_forces[0] == pytest.approx(-100.0)
    assert result.stresses[0] < 0
    assert result.displacement[1, 0] == pytest.approx(-100.0 * L / (E * A))
