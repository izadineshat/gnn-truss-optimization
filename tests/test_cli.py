"""CLI smoke tests for ``truss-fem``."""

from __future__ import annotations

import numpy as np

from trussgnn.cli import main


def test_cli_runs_and_reports_stresses(capsys) -> None:  # type: ignore[no-untyped-def]
    code = main(["--load", "-100000"])
    out = capsys.readouterr().out
    assert code == 0
    assert "trussgnn" in out
    assert "N (kN)" in out
    assert "compression" in out


def test_cli_lists_support_reactions(capsys) -> None:  # type: ignore[no-untyped-def]
    main(["--load", "-100000"])
    out = capsys.readouterr().out
    assert "Rx=" in out and "Ry=" in out
    assert "Equilibrium residual" in out


def test_build_parser_has_version_flag() -> None:
    from trussgnn.cli import build_parser

    parser = build_parser()
    with np.testing.assert_raises(SystemExit):
        parser.parse_args(["--version"])
