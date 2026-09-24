"""Linear-elastic 2D truss analysis (direct stiffness method).

Port of the educational script ``/truss_analysis.py`` into a reusable,
testable API. The math is identical to the original teaching code — a
three-node triangle with a downward load — generalized to any planar truss.

Supports:

- global stiffness assembly from ``E``, ``A`` per member,
- partition into free / fixed degrees of freedom,
- displacement solution, reaction recovery and equilibrium check,
- internal axial force and stress per member,
- deformed-coordinate computation for later plotting.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from numpy.typing import ArrayLike, NDArray

from trussgnn.utils.validation import as_connectivity, as_coordinates

FloatArray = NDArray[np.float64]


@dataclass(frozen=True)
class TrussModel:
    """Geometry + material definition of a 2D pin-jointed truss.

    Attributes:
        nodes: ``(n_nodes, 2)`` array of node coordinates ``[x, y]`` in metres.
        elements: ``(n_elements, 2)`` integer array of node-id pairs ``(i, j)``.
        elasticity: Young's modulus ``E`` in pascals (default: steel, 200 GPa).
        areas: per-member cross-sectional area in m² (default: 0.01 m²).
            A scalar is broadcast to every member.
        fixed_dofs: sorted array of constrained DOF indices
            (``2*i`` -> node ``i`` x, ``2*i+1`` -> node ``i`` y).
    """

    nodes: FloatArray  # (n_nodes, 2)
    elements: NDArray[np.int64]  # (n_elements, 2)
    elasticity: float = 200e9
    areas: FloatArray = field(default_factory=lambda: np.array([0.01]))  # m^2
    fixed_dofs: NDArray[np.int64] = field(default_factory=lambda: np.array([], dtype=np.int64))

    def __post_init__(self) -> None:
        nodes = as_coordinates(self.nodes)
        elements = as_connectivity(self.elements)
        areas = np.asarray(self.areas, dtype=np.float64)
        if areas.ndim == 0:
            areas = np.full(elements.shape[0], float(areas))
        fixed = np.asarray(self.fixed_dofs, dtype=np.int64).reshape(-1)

        n_nodes = nodes.shape[0]
        n_dofs = 2 * n_nodes

        if elements.size and int(elements.max()) >= n_nodes:
            raise ValueError(
                f"element node id {int(elements.max())} out of range for {n_nodes} nodes"
            )
        if elements.min() < 0:
            raise ValueError("element node ids must be non-negative")
        if areas.shape != (elements.shape[0],):
            raise ValueError(
                f"areas must have one value per element ({elements.shape[0]}), got {areas.shape}"
            )
        if self.elasticity <= 0:
            raise ValueError(f"elasticity must be positive, got {self.elasticity}")
        if np.any(areas <= 0):
            raise ValueError("areas must be positive")
        if fixed.size and (fixed.min() < 0 or fixed.max() >= n_dofs):
            raise ValueError(f"fixed_dofs entries must be in [0, {n_dofs})")

        # dataclass is frozen: rebuild the normalized fields instead of mutating
        object.__setattr__(self, "nodes", nodes)
        object.__setattr__(self, "elements", elements)
        object.__setattr__(self, "areas", areas)
        object.__setattr__(self, "fixed_dofs", np.unique(fixed))

    @property
    def num_nodes(self) -> int:
        return int(self.nodes.shape[0])

    @property
    def num_elements(self) -> int:
        return int(self.elements.shape[0])

    @property
    def num_dofs(self) -> int:
        return 2 * self.num_nodes

    @property
    def free_dofs(self) -> NDArray[np.int64]:
        """All DOFs not present in ``fixed_dofs`` (unsorted)."""
        mask = np.ones(self.num_dofs, dtype=bool)
        mask[self.fixed_dofs] = False
        return np.flatnonzero(mask)


def element_stiffness(p_i: ArrayLike, p_j: ArrayLike, elasticity: float, area: float) -> FloatArray:
    """4x4 stiffness of a single truss member in global coordinates.

    ``k = (E·A / L) · λ ⊗ λ`` where ``λ = [-c, -s, c, s]`` with
    ``c = cos θ`` and ``s = sin θ``.
    """
    i = np.asarray(p_i, dtype=np.float64)
    j = np.asarray(p_j, dtype=np.float64)
    delta = j - i
    length = float(np.linalg.norm(delta))
    if length <= 0:
        raise ValueError("member has zero length")
    c, s = delta[0] / length, delta[1] / length
    lam = np.array([-c, -s, c, s], dtype=np.float64)
    return (elasticity * area / length) * np.outer(lam, lam)


def assemble_global_stiffness(model: TrussModel) -> FloatArray:
    """Assemble the global ``(2n, 2n)`` stiffness matrix.

    Mirrors the pedagogical double loop of the original script: each member's
    4x4 contribution is scattered into the DOF rows/columns of its two nodes.
    """
    n_dofs = model.num_dofs
    k_global = np.zeros((n_dofs, n_dofs), dtype=np.float64)
    for (i, j), area in zip(model.elements, model.areas, strict=True):
        k_e = element_stiffness(model.nodes[i], model.nodes[j], model.elasticity, area)
        dofs = (2 * int(i), 2 * int(i) + 1, 2 * int(j), 2 * int(j) + 1)
        idx = np.ix_(dofs, dofs)
        k_global[idx] += k_e
    # restore exact symmetry lost to floating-point scatter
    k_global = 0.5 * (k_global + k_global.T)
    return k_global


def _apply_loads(model: TrussModel, loads: ArrayLike) -> FloatArray:
    """Node loads -> global force vector; repeated node ids accumulate."""
    node_loads = np.asarray(loads, dtype=np.float64)
    if node_loads.shape != (model.num_nodes, 2):
        raise ValueError(f"loads must have shape ({model.num_nodes}, 2), got {node_loads.shape}")
    f = node_loads.reshape(-1)
    # validate free-DOF loading only (fixed-DOF forces are reactions)
    if np.any(f[model.fixed_dofs] != 0.0):
        raise ValueError("loads applied on fixed DOFs are not allowed (they are reactions)")
    return f


@dataclass(frozen=True)
class TrussResult:
    """Complete analysis output for one load case.

    Attributes:
        displacement: ``(n_nodes, 2)`` nodal displacements in metres.
        reactions: ``(n_nodes, 2)`` support reactions in newtons.
        axial_forces: ``(n_elements,)`` internal member forces (tension +, compression -) in N.
        stresses: ``(n_elements,)`` axial stresses (Pa) = N / A.
        element_strains: ``(n_elements,)`` axial strain = N / (E·A).
        deformed_nodes: ``(n_nodes, 2)`` displaced coordinates = nodes + displacement.
        equilibrium_error: ``‖Σ F_ext + Σ R‖ / max(1, ‖Σ F_ext‖)`` — vector-equilibrium
            check (must be ~0: external loads and support reactions cancel as vectors).
    """

    model: TrussModel
    displacement: FloatArray  # (n_nodes, 2)
    reactions: FloatArray  # (n_nodes, 2)
    axial_forces: FloatArray  # (n_elements,)
    stresses: FloatArray  # (n_elements,)
    element_strains: FloatArray  # (n_elements,)
    deformed_nodes: FloatArray  # (n_nodes, 2)
    equilibrium_error: float = 0.0

    @property
    def max_stress(self) -> float:
        """Largest absolute axial stress across all members (Pa)."""
        return float(np.max(np.abs(self.stresses))) if self.stresses.size else 0.0

    def member_result(self, member: int) -> dict[str, float]:
        """Human-readable summary of one member: force, stress, strain."""
        i, j = self.model.elements[member]
        length = float(np.linalg.norm(self.model.nodes[j] - self.model.nodes[i]))
        return {
            "node_i": int(i),
            "node_j": int(j),
            "length_m": length,
            "axial_force_N": float(self.axial_forces[member]),
            "stress_Pa": float(self.stresses[member]),
            "strain": float(self.element_strains[member]),
        }


def solve_truss(model: TrussModel, loads: ArrayLike) -> TrussResult:
    """Solve one load case with the direct stiffness method.

    Steps (in the order the educational script taught them):

    1. assemble the global stiffness matrix,
    2. partition into free / fixed DOFs and solve ``K_ff · u_f = F_f``,
    3. recover reactions ``R = K_fx · u_x`` on fixed DOFs,
    4. recover internal member forces and stresses,
    5. equilibrium check ``Σ F_ext + Σ R ≈ 0``.
    """
    k_global = assemble_global_stiffness(model)
    f_global = _apply_loads(model, loads)

    free = model.free_dofs
    fixed = model.fixed_dofs

    u = np.zeros(model.num_dofs, dtype=np.float64)
    if free.size:
        k_ff = k_global[np.ix_(free, free)]
        f_f = f_global[free]
        try:
            u[free] = np.linalg.solve(k_ff, f_f)
        except np.linalg.LinAlgError as exc:
            raise np.linalg.LinAlgError(
                "singular free stiffness matrix: the truss is not stable "
                "(add supports / members or remove rigid-body modes)"
            ) from exc

    # reactions: R_fixed = K_fx u (K_fx = K[fixed, :] with free cols zero -> full product)
    reactions_flat = k_global[fixed, :] @ u if fixed.size else np.zeros(0, dtype=np.float64)

    displacement = u.reshape(-1, 2)  # (n_nodes, 2)

    # internal forces: N = E·A/L · ((u_j - u_i) · (cosθ, sinθ))  per roadmap step 4
    axial = np.zeros(model.num_elements, dtype=np.float64)
    for m, (i, j) in enumerate(model.elements):
        delta = model.nodes[j] - model.nodes[i]
        length = float(np.linalg.norm(delta))
        direction = delta / length
        u_ij = displacement[j] - displacement[i]
        axial[m] = (model.elasticity * model.areas[m] / length) * float(direction @ u_ij)

    stresses = axial / model.areas
    strains = axial / (model.elasticity * model.areas)

    reactions = np.zeros((model.num_nodes, 2), dtype=np.float64)
    reactions.reshape(-1)[fixed] = reactions_flat

    # equilibrium: external loads + support reactions must cancel as vectors
    #   Σ F_ext + Σ R = 0   (component-wise, across all nodes)
    residual = f_global.reshape(-1, 2).sum(axis=0) + reactions.sum(axis=0)
    denom = max(1.0, float(np.linalg.norm(f_global.reshape(-1, 2).sum(axis=0))))
    equilibrium_error = float(np.linalg.norm(residual)) / denom

    return TrussResult(
        model=model,
        displacement=displacement,
        reactions=reactions,
        axial_forces=axial,
        stresses=stresses,
        element_strains=strains,
        deformed_nodes=model.nodes + displacement,
        equilibrium_error=equilibrium_error,
    )


def canonical_triangle() -> TrussModel:
    """The tutorial truss from ``/truss_analysis.py``: three nodes, steel, 0.01 m².

    ``nodes[0]=(0,0)``, ``nodes[1]=(4,0)``, ``nodes[2]=(2,3)`` with members
    (0,1), (1,2), (2,0); nodes 0 and 1 are pinned. Naming a canonical example
    keeps the ported teaching script and the test suite in lockstep.
    """
    return TrussModel(
        nodes=np.array([[0.0, 0.0], [4.0, 0.0], [2.0, 3.0]]),
        elements=np.array([[0, 1], [1, 2], [2, 0]]),
        elasticity=200e9,
        areas=np.array([0.01, 0.01, 0.01]),
        fixed_dofs=np.array([0, 1, 2, 3]),
    )


def solve_tutorial(plot: bool = False) -> TrussResult:
    """Run the classic tutorial problem and (optionally) plot the deformed shape.

    Reproduces ``truss_analysis.py`` under a 100 kN downward load at node 2.
    """
    model = canonical_triangle()
    loads = np.zeros((3, 2))
    loads[2, 1] = -100_000.0
    result = solve_truss(model, loads)

    if plot:
        from trussgnn.plot import plot_deformed

        plot_deformed(result)

    return result
