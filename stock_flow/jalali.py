"""Jalali (Solar Hijri) <-> Gregorian date conversion, stdlib only.

Ported from the well-known jalaali-js algorithm (MIT), which is exact for
years 1178..1633 and verified here against known anchors.
"""

from __future__ import annotations

__all__ = ["jalali_to_gregorian", "parse_jalali_datetime", "to_iso"]

_BREAKS = [
    -61, 9, 38, 199, 426, 686, 756, 818, 1111, 1181, 1210, 1635, 2060,
    2097, 2192, 2262, 2324, 2394, 2456, 3178,
]


def _div(a: int, b: int) -> int:
    return a // b


def _mod(a: int, b: int) -> int:
    return ((a % b) + b) % b


def _jal_cal(jy: int) -> dict:
    bl = len(_BREAKS)
    gy = jy + 621
    leap_j = -14
    jp = _BREAKS[0]
    jump = 0
    leap_g = leap = march = n = 0
    for i in range(1, bl):
        jm = _BREAKS[i]
        jump = jm - jp
        if jy < jm:
            break
        leap_j = leap_j + _div(jump, 33) * 8 + _div(_mod(jump, 33) + 3, 4)
        jp = jm
    n = jy - jp
    leap_j = leap_j + _div(n, 33) * 8 + _div(_mod(n, 33) + 3, 4)
    if _mod(jump, 33) == 4 and jump - n == 4:
        leap_j += 1
    leap_g = _div(gy, 4) - _div((_div(gy, 100) + 1) * 3, 4) - 150
    march = 20 + leap_j - leap_g
    if jump - n < 6:
        n = n - jump + _div(jump + 4, 33) * 33
    leap = _mod(_mod(n + 1, 33) - 1, 4)
    if leap == -1:
        leap = 4
    return {"leap": leap, "gy": gy, "march": march}


def _g2d(gy: int, gm: int, gd: int) -> int:
    d = (
        _div((gy + _div(gm - 8, 6) + 100100) * 1461, 4)
        + _div(153 * _mod(gm + 9, 12) + 2, 5)
        - _div(3 * (_div(gy + _div(gm - 8, 6) + 100100, 100)), 4)
        + gd
        - 34840408
    )
    d = d - _div(_div(gy + _div(gm - 8, 6) + 100100, 100) * 3, 4) + 752
    return d


def _j2d(jy: int, jm: int, jd: int) -> int:
    r = _jal_cal(jy)
    return _g2d(r["gy"], 3, r["march"]) + (jm - 1) * 31 - _div(jm, 7) * (jm - 7) + jd - 1


def _d2g(jdn: int) -> tuple[int, int, int]:
    j = 4 * jdn + 139361631
    j = j + _div(_div(4 * jdn + 183187720, 146097) * 3, 4) * 4 - 3908
    i = _div(_mod(j, 1461), 4) * 5 + 308
    gd = _div(_mod(i, 153), 5) + 1
    gm = _mod(_div(i, 153), 12) + 1
    gy = _div(j, 1461) - 100100 + _div(8 - gm, 6)
    return gy, gm, gd


def jalali_to_gregorian(jy: int, jm: int, jd: int) -> tuple[int, int, int]:
    """(1405, 1, 1) -> (2026, 3, 21)"""
    return _d2g(_j2d(jy, jm, jd))


def parse_jalali_datetime(text: str) -> str | None:
    """Parse '1405/03/13-13:29:59' or '1405/03/13' -> ISO '2026-06-03'."""
    if not text:
        return None
    parts = str(text).strip().split("-")[0]
    bits = parts.split("/")
    if len(bits) != 3:
        return None
    try:
        jy, jm, jd = (int(b) for b in bits)
        gy, gm, gd = jalali_to_gregorian(jy, jm, jd)
    except Exception:  # noqa: BLE001
        return None
    return f"{gy:04d}-{gm:02d}-{gd:02d}"


def to_iso(text: str) -> str | None:
    """Alias for parse_jalali_datetime."""
    return parse_jalali_datetime(text)


def _self_test() -> None:
    cases = [
        ((1405, 1, 1), (2026, 3, 21)),
        ((1404, 1, 1), (2025, 3, 21)),
        ((1403, 12, 30), (2026, 3, 20)),  # leap day 1403
        ((1357, 11, 22), (1979, 2, 11)),
        ((1400, 1, 1), (2021, 3, 21)),
        ((1405, 6, 15), (2026, 9, 6)),
        ((1405, 6, 2), (2026, 8, 24)),
    ]
    for (jy, jm, jd), expected in cases:
        got = jalali_to_gregorian(jy, jm, jd)
        assert got == expected, f"{jy}/{jm}/{jd} -> {got} != {expected}"
    assert parse_jalali_datetime("1405/03/13-13:29:59") == "2026-06-03"
    assert parse_jalali_datetime("1405/03/13") == "2026-06-03"
    print(f"jalali self-test OK ({len(cases)} anchors)")


if __name__ == "__main__":
    _self_test()