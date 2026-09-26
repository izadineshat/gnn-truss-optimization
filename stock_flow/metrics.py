"""Order-flow analytics, composite scoring, and screening filter flags."""

from __future__ import annotations

import numpy as np
import pandas as pd


def percentile_rank(s: pd.Series) -> pd.Series:
    """Compute percentile rank [0..100] robust to NaNs."""
    valid = s.dropna()
    if len(valid) <= 1:
        return pd.Series(50.0, index=s.index)
    ranks = valid.rank(pct=True) * 100.0
    res = pd.Series(np.nan, index=s.index)
    res[valid.index] = ranks
    return res.fillna(50.0)


def compute_symbol_scores(df: pd.DataFrame) -> pd.DataFrame:
    """Compute composite order-flow score and filter pass counts for symbol watch."""
    out = df.copy()

    # Core indicators (fallback to 0 if col missing)
    def g(col: str) -> pd.Series:
        return out[col] if col in out.columns else pd.Series(0.0, index=out.index)

    # 1. Percentile ranks
    pr_inflow = percentile_rank(g("money_inflow_real"))
    pr_week = percentile_rank(g("money_inflow_week"))
    pr_net = percentile_rank(g("order_imbalance"))
    pr_buy_pow = percentile_rank(g("real_buy_power"))
    pr_liq_ratio = percentile_rank(g("value_ratio_1m"))
    pr_ret_m = percentile_rank(g("ret_month_pct"))

    # Weighted composite score (0-100)
    out["امتیاز جریان سفارش"] = (
        0.30 * pr_inflow
        + 0.20 * pr_week
        + 0.20 * pr_net
        + 0.15 * pr_buy_pow
        + 0.10 * pr_liq_ratio
        + 0.05 * pr_ret_m
    ).round(1)

    # 2. Filter rules (8 gates)
    f_liq = g("value_ratio_1m") >= 1.0
    f_inflow = g("money_inflow_real") > 0
    f_week = g("money_inflow_week") > 0
    f_net = g("order_imbalance") > 0
    f_bp = g("real_buy_power") > 1.0
    f_ret_w = g("ret_week_pct") > 0
    f_ret_m = g("ret_month_pct") > 0
    f_pe = (g("pe") > 0) & (g("pe") <= 25.0)

    out["تعداد فیلتر عبوری"] = (
        f_liq.astype(int)
        + f_inflow.astype(int)
        + f_week.astype(int)
        + f_net.astype(int)
        + f_bp.astype(int)
        + f_ret_w.astype(int)
        + f_ret_m.astype(int)
        + f_pe.astype(int)
    )

    out["وضعیت فیلتر"] = out["تعداد فیلتر عبوری"].apply(
        lambda n: f"✔ تایید کامل ({n}/8)" if n >= 6 else (f"🟡 متوسط ({n}/8)" if n >= 4 else f"❌ ضعیف ({n}/8)")
    )

    return out.sort_values(by="امتیاز جریان سفارش", ascending=False).reset_index(drop=True)


def compute_industry_scores(df: pd.DataFrame) -> pd.DataFrame:
    """Compute composite order-flow score for industry groups."""
    out = df.copy()

    def g(col: str) -> pd.Series:
        return out[col] if col in out.columns else pd.Series(0.0, index=out.index)

    pr_in = percentile_rank(g("ورود پول"))
    pr_in5 = percentile_rank(g("ورود پول ۵ روزه"))
    pr_net = percentile_rank(g("برآیند سفارش ها"))
    pr_bp = percentile_rank(g("قدرت خرید"))
    pr_val20 = percentile_rank(g("ارزش به میانگین ۲۰ روزه"))
    pr_ret = percentile_rank(g("بازدهی گروه (هموزن)"))

    out["امتیاز جریان سفارش"] = (
        0.30 * pr_in
        + 0.20 * pr_net
        + 0.20 * pr_in5
        + 0.15 * pr_bp
        + 0.10 * pr_val20
        + 0.05 * pr_ret
    ).round(1)

    return out.sort_values(by="امتیاز جریان سفارش", ascending=False).reset_index(drop=True)
