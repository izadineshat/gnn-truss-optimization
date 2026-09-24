"""trussgnn — graph-neural-network driven optimization of 2D trusses.

The package is organised after the learning roadmap in ``amozeshi/roadmap.md``:

``trussgnn.fem``
    Finite-element core: stiffness assembly, displacement/force/stress recovery.
``trussgnn.graph``
    Truss -> graph conversion (``edge_index``, adjacency, degree, Laplacian).
``trussgnn.data``
    Dataset generation: random trusses + FEM ground truth.
``trussgnn.models``
    Graph neural networks (roadmap step 7).
``trussgnn.optimize``
    Weight minimization driven by the trained surrogate (roadmap step 8).
"""

from __future__ import annotations

from trussgnn.fem.truss import (
    TrussModel,
    TrussResult,
    assemble_global_stiffness,
    solve_truss,
)
from trussgnn.graph.convert import truss_to_graph

__version__ = "0.1.0"

__all__ = [
    "TrussModel",
    "TrussResult",
    "__version__",
    "assemble_global_stiffness",
    "solve_truss",
    "truss_to_graph",
]
