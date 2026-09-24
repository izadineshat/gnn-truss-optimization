"""Probe candidate stock-market / order-flow files for structure."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

FILES = {
    "downloads_table.csv": Path(r"C:\Users\Reza\Downloads\table.csv"),
    "downloads_export.xlsx": Path(r"C:\Users\Reza\Downloads\export.xlsx"),
    "downloads_group-watch-2026-09-06.xls": Path(r"C:\Users\Reza\Downloads\group-watch-2026-09-06.xls"),
    "downloads_industries-watch-2026-09-06.xls": Path(r"C:\Users\Reza\Downloads\industries-watch-2026-09-06.xls"),
    "stock_ga_export__1_.xlsx": Path(r"H:\stock_ga\export__1_.xlsx"),
}


def probe(path: Path) -> None:
    print("=" * 80)
    print(f"FILE: {path.name}  exists={path.exists()}  size={path.stat().st_size if path.exists() else '-'}")
    print("=" * 80)
    if not path.exists():
        return
    try:
        if path.suffix.lower() == ".csv":
            df = pd.read_csv(path, encoding="utf-8-sig")
            print(f"shape={df.shape}")
            print("columns:", list(df.columns))
            with pd.option_context("display.max_columns", None, "display.width", 250, "display.max_colwidth", 40):
                print(df.head(5).to_string())
            return
        book = pd.ExcelFile(path)
        print(f"sheets: {book.sheet_names}")
        for sheet in book.sheet_names[:3]:
            try:
                df = book.parse(sheet)
            except Exception as e:  # noqa: BLE001
                print(f"  parse error for {sheet}: {e}")
                continue
            print(f"\n--- sheet '{sheet}' shape={df.shape}")
            print("columns:", list(df.columns))
            with pd.option_context("display.max_columns", None, "display.width", 250, "display.max_colwidth", 30):
                print(df.head(3).to_string())
    except Exception as e:  # noqa: BLE001
        print(f"ERROR: {e!r}")


def main() -> int:
    for name, path in FILES.items():
        probe(path)
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())