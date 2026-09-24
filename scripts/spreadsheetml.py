"""Parse tsetmc SpreadsheetML watch exports (`*.xls` = XML Workbook).

Stdlib-only parser. Exposes raw rows/cells for inspection.
"""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# SpreadsheetML namespaces
NS = {
    "ss": "urn:schemas-microsoft-com:office:spreadsheet",
    "x": "urn:schemas-microsoft-com:office:excel",
}


def parse_spreadsheetml(path: Path) -> list[list[str]]:
    """Return rows x cells of strings (stripped). Cell indexes are materialized."""
    tree = ET.parse(path)
    root = tree.getroot()
    rows: list[list[str]] = []
    for row_el in root.iter("{urn:schemas-microsoft-com:office:spreadsheet}Row"):
        cells: list[str] = []
        for cell_el in row_el:
            if not cell_el.tag.endswith("}Cell"):
                continue
            # honor Index attribute (sparse rows)
            idx = int(cell_el.attrib.get("Index", len(cells) + 1))
            while len(cells) < idx - 1:
                cells.append("")
            data_el = cell_el.find("{urn:schemas-microsoft-com:office:spreadsheet}Data")
            text = "".join(data_el.itertext()) if data_el is not None else ""
            cells.append(text.strip())
        rows.append(cells)
    return rows


def dump_summary(path: Path, max_rows: int = 12) -> None:
    rows = parse_spreadsheetml(path)
    print(f"FILE: {path.name}  total_rows={len(rows)}")
    for i, row in enumerate(rows[:max_rows]):
        print(f"  row[{i:>3}] ({len(row)} cells): {row}")


def main() -> int:
    files = [
        Path(r"C:\Users\Reza\Downloads\industries-watch-2026-09-06.xls"),
        Path(r"C:\Users\Reza\Downloads\group-watch-2026-09-06.xls"),
        Path(r"C:\Users\Reza\Downloads\group-watch-2026-08-30.xls"),
        Path(r"C:\Users\Reza\Downloads\industries-watch-2026-08-29.xls"),
        Path(r"C:\Users\Reza\Downloads\industries-watch-2026-08-25.xls"),
        Path(r"C:\Users\Reza\Downloads\industries-watch-2026-08-24.xls"),
    ]
    for f in files:
        dump_summary(f)
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())