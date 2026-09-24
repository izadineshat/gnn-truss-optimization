"""Probe tsetmc watch exports (HTML-as-.xls and csv)."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

FILES = [
    Path(r"C:\Users\Reza\Downloads\group-watch-2026-09-06.xls"),
    Path(r"C:\Users\Reza\Downloads\industries-watch-2026-09-06.xls"),
    Path(r"C:\Users\Reza\Downloads\industries-watch-2026-08-30.csv"),
]

HEAD_BYTES = 1200


def main() -> int:
    for path in FILES:
        print("=" * 80)
        print(f"FILE: {path.name}  exists={path.exists()}  size={path.stat().st_size if path.exists() else '-'}")
        print("=" * 80)
        if not path.exists():
            continue
        with open(path, "rb") as fh:
            head = fh.read(HEAD_BYTES)
        print("magic head:", head[:200])
        if path.suffix.lower() == ".csv":
            try:
                df = pd.read_csv(path, encoding="utf-8-sig")
            except Exception as e:  # noqa: BLE001
                print(f"csv error: {e!r}")
                continue
            print(f"shape={df.shape}")
            with pd.option_context("display.max_columns", None, "display.width", 300, "display.max_colwidth", 30):
                print(df.head(3).to_string())
            continue

        # try html tables first (tsetmc exports are HTML)
        try:
            tables = pd.read_html(path)
            print(f"read_html -> {len(tables)} tables")
            for i, df in enumerate(tables):
                print(f"\n--- table[{i}] shape={df.shape}")
                print("columns:", list(df.columns))
                with pd.option_context("display.max_columns", None, "display.width", 300, "display.max_colwidth", 30):
                    print(df.head(3).to_string())
                    print("...")
                    print(df.tail(2).to_string())
        except Exception as e:  # noqa: BLE001
            print(f"read_html failed: {e!r}")
            try:
                df = pd.read_excel(path, engine="xlrd")
                print(f"xlrd ok shape={df.shape}")
                with pd.option_context("display.max_columns", None, "display.width", 300):
                    print(df.head(3).to_string())
            except Exception as e2:  # noqa: BLE001
                print(f"xlrd failed: {e2!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())