"""Data ingestion and normalization for tsetmc watch exports.

Handles SpreadsheetML (XML) and CSV formats, suffix-based number parsing
(B/M/K), and unit normalization to canonical scales.
"""

from __future__ import annotations

import csv
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd


def parse_number(s: str | None) -> float | None:
    """Parse '1,989.7 B', '-83.33', scientific notation, '-', etc."""
    if s is None:
        return None
    # Normalize: strip quotes, commas, spaces, handle special minus
    s = str(s).strip().replace("'", "").replace("−", "-").replace(",", "")
    if not s or s in ("-", "—", "NaN"):
        return None

    mult = 1.0
    u = s[-1].upper()
    if u == "B":
        mult, s = 1e9, s[:-1]
    elif u == "M":
        mult, s = 1e6, s[:-1]
    elif u == "K":
        mult, s = 1e3, s[:-1]
    elif u == "T":  # Tera / Trillion
        mult, s = 1e12, s[:-1]

    try:
        return float(s.strip()) * mult
    except ValueError:
        return None


def parse_spreadsheetml(path: Path) -> list[list[str]]:
    """Fast stdlib-only SpreadsheetML parser. Honors cell indexes."""
    tree = ET.parse(path)
    root = tree.getroot()
    rows: list[list[str]] = []
    # Namespaces are often absent or variable in these exports, search by local name
    for row_el in root.iter():
        if not row_el.tag.endswith("}Row"):
            continue
        cells: list[str] = []
        for cell_el in row_el:
            if not cell_el.tag.endswith("}Cell"):
                continue
            # Materialize sparse cells using Index
            idx_attr = cell_el.attrib.get("{urn:schemas-microsoft-com:office:spreadsheet}Index")
            if idx_attr:
                idx = int(idx_attr)
                while len(cells) < idx - 1:
                    cells.append("")
            data_el = cell_el.find("{urn:schemas-microsoft-com:office:spreadsheet}Data")
            text = "".join(data_el.itertext()) if data_el is not None else ""
            cells.append(text.strip())
        if cells:
            rows.append(cells)
    return rows


def normalize_industry_name(name: str) -> tuple[str, int | None]:
    """'استخراج کانه های فلزی (17)' -> ('استخراج کانه های فلزی', 17)"""
    match = re.search(r"\s*\((\d+)\)\s*$", name)
    if match:
        return name[: match.start()].strip(), int(match.group(1))
    return name.strip(), None


def load_watch_file(path: Path, is_industry: bool = True) -> pd.DataFrame:
    """Load XLS (SpreadsheetML) or CSV into a normalized DataFrame."""
    if path.suffix.lower() == ".csv":
        df_raw = pd.read_csv(path, encoding="utf-8-sig")
        rows = [df_raw.columns.tolist()] + df_raw.values.tolist()
    else:
        rows = parse_spreadsheetml(path)

    if not rows:
        return pd.DataFrame()

    header = [re.sub(r"\s+", " ", h).strip() for h in rows[0]]
    # Make duplicate headers unique so pandas doesn't fail
    seen = {}
    unique_header = []
    for h in header:
        if h in seen:
            seen[h] += 1
            unique_header.append(f"{h}_{seen[h]}")
        else:
            seen[h] = 0
            unique_header.append(h)
    header = unique_header

    data = rows[1:]

    # For 08-29 stray column edge case:
    df = pd.DataFrame(data)
    if df.shape[1] > len(header):
        df = df.iloc[:, : len(header)]
    elif df.shape[1] < len(header):
        header = header[: df.shape[1]]
    df.columns = header

    # Cleanup and numeric parse
    for col in df.columns:
        df[col] = df[col].apply(lambda x: parse_number(str(x)) if x is not None else None)

    # Special handling for names (first column)
    name_col = header[0]
    df[name_col] = [r[0] for r in data]  # restore original strings

    if is_industry:
        # Normalize industry names and extract counts
        names_counts = [normalize_industry_name(str(n)) for n in df[name_col]]
        df[name_col] = [pair[0] for pair in names_counts]
        df["تعداد نماد"] = [pair[1] for pair in names_counts]

    return df
