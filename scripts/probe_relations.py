"""Second-pass reconnaissance: relate files, verify duplicates, list all sheets/columns."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from spreadsheetml import parse_spreadsheetml  # noqa: E402

DOWNLOADS = Path(r"C:\Users\Reza\Downloads")


def signature(rows: list[list[str]]) -> str:
    return "|".join(rows[1][:4]) if len(rows) > 1 else ""


def main() -> int:
    # 1. Relation between the industries CSV and the XLS snapshots
    csv_path = DOWNLOADS / "industries-watch-2026-08-30.csv"
    df_csv = pd.read_csv(csv_path, encoding="utf-8-sig")
    print(f"CSV {csv_path.name}: shape={df_csv.shape}")
    print("CSV first data row (first 4 fields):", list(df_csv.iloc[0][:4]))

    for name in [
        "industries-watch-2026-09-06.xls",
        "industries-watch-2026-08-29.xls",
        "industries-watch-2026-08-25.xls",
        "industries-watch-2026-08-24.xls",
    ]:
        rows = parse_spreadsheetml(DOWNLOADS / name)
        print(f"  {name}: rows={len(rows)} first_data={rows[1][:4] if len(rows) > 1 else None}")

    # 2. Symbol watch files
    for name in ["group-watch-2026-09-06.xls", "group-watch-2026-08-30.xls"]:
        rows = parse_spreadsheetml(DOWNLOADS / name)
        hdr = rows[0]
        syms = [r[0] for r in rows[1:] if r and r[0]]
        print(f"\n{name}: {len(rows)-1} data rows, {len(hdr)} cols")
        print(f"  first 12 symbols: {syms[:12]}")
        print(f"  last 5 symbols: {syms[-5:]}")

    # 3. export.xlsx (symbol status feed) full dump
    xl = pd.ExcelFile(DOWNLOADS / "export.xlsx")
    df = xl.parse(xl.sheet_names[0])
    print(f"\nexport.xlsx shape={df.shape}")
    with pd.option_context("display.max_rows", None, "display.width", 200):
        print(df.to_string())

    # 4. trading journal probe
    jpath = DOWNLOADS / "ژورنال-معاملاتی-ستارگان-ترید-آپدیت.xlsx"
    if jpath.exists():
        xl2 = pd.ExcelFile(jpath)
        print(f"\njournal sheets: {xl2.sheet_names}")
        for s in xl2.sheet_names[:4]:
            d = xl2.parse(s)
            print(f"  sheet '{s}' shape={d.shape} cols={list(d.columns)[:12]}")

    # 5. Symbol-level overlap between the two watch dates
    r1 = parse_spreadsheetml(DOWNLOADS / "group-watch-2026-09-06.xls")
    r2 = parse_spreadsheetml(DOWNLOADS / "group-watch-2026-08-30.xls")
    s1 = {r[0] for r in r1[1:] if r and r[0]}
    s2 = {r[0] for r in r2[1:] if r and r[0]}
    print(f"\nsymbol overlap: {len(s1 & s2)}  only-09-06={len(s1-s2)}  only-08-30={len(s2-s1)}")
    print("only 09-06:", sorted(s1 - s2))
    print("only 08-30:", sorted(s2 - s1))
    return 0


if __name__ == "__main__":
    sys.exit(main())