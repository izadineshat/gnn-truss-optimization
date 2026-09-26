"""Unit normalization for industry symbol watch data."""
from __future__ import annotations

import holidays_ir


def explore_columns() -> list[str]:
    """Return list of expected core columns in industry and symbol watches."""
    IND_CORE_COLS = [
        "حجم",
        "ارزش",
        "ارزش خرید حقیقی",
        "ارزش فروش حقیقی",
        "ارزش سفارش های خرید",
        "ارزش سفارش های فروش",
        "برآیند سفارش ها",
        "سرانه خرید",
        "سرانه فروش",
        "قدرت خرید",
        "درصد خرید حقیقی",
        "درصد فروش حقیقی",
        "ورود پول",
        "ارزش معاملات",
        "بازدهی گروه",
        "سرانه خرید ۵ روزه",
        "سرانه خرید ۲۰ روزه",
        "قدرت خرید ۵ روزه",
        "قدرت خرید ۲۰ روزه",
        "ورود پول ۵ روزه",
        "ورود پول ۲۰ روزه",
    ]

    # Use industry as prototype; later width will be finalized.
    return IND_CORE_COLS