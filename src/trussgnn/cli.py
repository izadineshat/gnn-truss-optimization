"""Command-line entry point: ``truss-fem``.

Runs the canonical tutorial truss and prints displacements, reactions, member
forces and stresses — the roadmap-step-4 deliverables without opening a plot.
"""

from __future__ import annotations

import argparse
import contextlib
import sys

import numpy as np

from trussgnn import __version__
from trussgnn.fem.truss import canonical_triangle, solve_truss


def _force_utf8_stdout() -> None:
    """Best-effort UTF-8 stdout so non-ASCII never crashes a cp1252 console."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            with contextlib.suppress(ValueError, OSError):  # pragma: no cover - platform specific
                reconfigure(encoding="utf-8", errors="replace")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="truss-fem",
        description="Solve the canonical 3-node truss and report forces/stresses.",
    )
    parser.add_argument(
        "--load", type=float, default=-100_000.0, help="downward load at the apex (N)"
    )
    parser.add_argument("--plot", action="store_true", help="also show the deformed-shape figure")
    parser.add_argument("--version", action="version", version=f"trussgnn {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    _force_utf8_stdout()
    args = build_parser().parse_args(argv)

    model = canonical_triangle()
    loads = np.zeros((model.num_nodes, 2))
    loads[2, 1] = args.load
    result = solve_truss(model, loads)

    print(f"trussgnn {__version__} - canonical 3-node truss, load {args.load:,.0f} N at node 2\n")
    print("Nodal displacements (m):")
    for n, (ux, uy) in enumerate(result.displacement):
        print(f"  node {n}: ux={ux:+.6e}  uy={uy:+.6e}")

    print("\nMember results:")
    print(f"  {'#':>2}  {'i-j':>5}  {'L (m)':>8}  {'N (kN)':>10}  {'sigma (MPa)':>12}  state")
    for m in range(model.num_elements):
        row = result.member_result(m)
        state = "tension" if row["axial_force_N"] > 0 else "compression"
        print(
            f"  {m:>2}  {row['node_i']}-{row['node_j']:<3}"
            f"  {row['length_m']:>8.4f}  {row['axial_force_N'] / 1e3:>10.3f}"
            f"  {row['stress_Pa'] / 1e6:>12.4f}  {state}"
        )

    print("\nSupport reactions (N), fixed DOFs only:")
    for n, (rx, ry) in enumerate(result.reactions):
        if abs(rx) > 1e-9 or abs(ry) > 1e-9:
            print(f"  node {n}: Rx={rx:+,.2f}  Ry={ry:+,.2f}")
    print(f"\nEquilibrium residual (relative): {result.equilibrium_error:.3e}")
    print(f"Max |stress|: {result.max_stress / 1e6:.4f} MPa")

    if args.plot:
        from trussgnn.plot import plot_member_stress

        plot_member_stress(result)
        import matplotlib.pyplot as plt

        plt.show()

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
