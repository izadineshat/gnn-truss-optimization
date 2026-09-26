"""Build order-flow comparison reports from tsetmc watch exports."""
import json
from datetime import datetime

import pandas as pd

# Add parent directory of stock_flow to PATH
import sys
from pathlib import Path
PACKAGE_PARENT = Path(__file__).parent.parent
if str(PACKAGE_PARENT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_PARENT))

import stock_flow.io as io
import stock_flow.metrics as metrics
import stock_flow.jalali as jalali


# ----------------------------------------------------------------------
# 1. CONFIGURATION (input paths)
# ----------------------------------------------------------------------
CHECKS_DIR = Path(r"C:\Users\Reza\Downloads")

INDUSTRY_WATCH_FILES = [
    ("2026-08-24", CHECKS_DIR / "industries-watch-2026-08-24.xls"),
    ("2026-08-25", CHECKS_DIR / "industries-watch-2026-08-25.xls"),
    ("2026-08-29", CHECKS_DIR / "industries-watch-2026-08-29.xls"),
    ("2026-09-06", CHECKS_DIR / "industries-watch-2026-09-06.xls"),
]

SYMBOL_WATCH_0906 = ("2026-09-06", CHECKS_DIR / "group-watch-2026-09-06.xls")
SYMBOL_WATCH_0830 = ("2026-08-30", CHECKS_DIR / "group-watch-2026-08-30.xls")

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------
# 2. NUMBER SCALE HELPERS
# ----------------------------------------------------------------------
INDUSTRIES_COL_UNITS = {
    # واحد → مقدار multiplicator برای تبدیل به واحد معرفی شده
    # 'حجم': 1e3  # B → میلیارد سهم
}
SYMBOL_COL_SIDES = {
    # ریال → میلیارد تومان
    "money_inflow_real": 1e10,
    "money_inflow_week": 1e10,
    "money_inflow_month": 1e10,
    "order_buy_value": 1e10,
    "order_imbalance": 1e10,
    "avg_value_1m": 1e10,
    "avg_value_3m": 1e10,
    "treasurer": 1e10,
}
SYMBOL_COL_VOLUMES = {
    # سهم → میلیون سهم
    "vol_shares": 1e-6,  # 1e10 rial price; but استخراج کانه های فلزی هزینه ارز/ریال? تومان / ریال? We'll just treat as nominal شاخص
    # Percentage/simple → keep as-is
}


# ----------------------------------------------------------------------
# 3. LOADERS
# ----------------------------------------------------------------------
def load_industry_watch(path: Path) -> pd.DataFrame:
    """Load industry watch file with unit normalization."""
    df = io.load_watch_file(path, is_industry=True)
    # Drop any leading NaN columns due to ragged rows (the duplicate trailing col)
    df = df.iloc[:, :33]  # safe cut if padding
    # name دعبده I: use first column as name
    names = df.iloc[:, 0].tolist()
    df["اسم صنعت"] = names
    return df


def load_symbol_watch(path: Path, date_tag: str) -> pd.DataFrame:
    """Load symbol watch with unit normalization and date labeling."""
    df = io.load_watch_file(path, is_industry=False)
    if df.empty:
        return df
    # Restore original Persian name from the first column for reindexing
    df["نماد"] = df.iloc[:, 0].tolist()
    # تایید تعداد ستون‌ها بر اساس مدل 30 ستی/72 ستونی
    if len(df.columns) == 30:
        # فیلتر برای 30 ستونی (09-06) همان مدل
        pass
    elif len(df.columns) == 72:
        # فیلتر برای مجددا بودن 72 ستونی (08-30) یُمانی
        pass
    # Add date column
    df["تاریخ"] = date_tag
    # Normalization ریال به میلیارد تومان
    for col, scale in SYMBOL_COL_SIDES.items():
        if col in df.columns:
            df[col] = df[col] * scale
    # حجم برای سهم: هر عدد در شمارش؟ از تومن/ریال؟ تومان/ریال نه, تومان؟ تومن = شمامل. واحد را فرض کنیم تومان
    # اما قیمت به واحد ریال است. تومان/ریال = 10 => 1 میلیارد تومان = 1e4 میلیون تومان.
    # در واقع 1 میلیارد تومان = 1e10 ریال
    # پس scaleFactor ریال→همت = 1e13
    large_scales = {
        "treasurer": 1e13,  # ارزش بازار، ارزش معاملات بزرگ → همت
        "trade_value": 1e13,  # ارزش معاملات
        "order_buy_value": 1e13,  # ارزش سفارش خرید
        "avg_value_1m": 1e13,  # میانگین ماهانه ارزش معاملات
        "avg_value_3m": 1e13,  # میانگین سه ماهه
        "money_inflow_monthly_cum": 1e13,  # جمع ورود پول ماهانه
        "money_inflow_quarter_cum": 1e13,  # جمع ورود سه ماهه
    }
    for col, scale in large_scales.items():
        if col in df.columns:
            df[col] = df[col] * scale
    # محاسبه شاخص‌های میانگین نقدینگی: ارزش به میانگین ماهانه
    # (کد اصلی نسبت درصد را از قبل دارد، نیازی به دستکاری نیست)
    # درصد آخرين قیمت: adjust if stored as decimal
    if "last_pct" in df.columns:
        df["last_pct"] = pd.to_numeric(df["last_pct"], errors="coerce") * 100.0 if df["last_pct"].dtype == "float64" else df["last_pct"]
    # درصد بازده: convert to percent
    # ret_week_pct, ret_month_pct likely as percent already but rename برن symbol alter
    if "ret_week_pct" in df.columns:
        df["ret_week_pct"] = (df["ret_week_pct"] * 100.0 if isinstance(df["ret_week_pct"].iloc[0], float) else df["ret_week_pct"])
    # Back to original column-naming for display
    # rename to Persian-friendly keys for output
    col_maps = [
        ("symbol", "نماد"),
        ("last_price", "آخرین قیمت (ریال)"),
        ("last_pct", "درصد آخرين قیمت (%)"),
        ("close_price", "قیمت پایاني (ریال)"),
        ("ret_week_pct", "بازدهي هفتگي (%)"),
        ("ret_month_pct", "بازدهي ماهاني (%)"),
        ("trade_value", "ارزش معاملات (میلیارد تومان)"),
        ("vol_shares", "حجم معاملات (میلیون سهم)"),
        ("money_inflow_real", "ورود پول حقيقي (میلیارد تومان)"),
        ("money_inflow_week", "ورود پول هفتگي (میلیارد تومان)"),
        ("money_inflow_month", "ورود پول ماهاني (میلیارد تومان)"),
        ("order_imbalance", "برآورد سفارشها (میلیارد تومان)"),
        ("real_buy_power", "قدرت خرید حقيقي"),
        ("buy_power_5d", "قدرت خرید ۵روزه"),
        ("buy_power_20d", "قدرت خرید ۲۰روزه"),
        ("avg_value_1m", "میانگين ماهانه ارزش معاملات (همت)"),
        ("value_ratio_1m", "ارزش به میانگين ماهانه"),
        ("pe", "P/E"),
        ("volatility_pct", "نوسان (%)"),
        ("mcap", "ارزش بازار (همت)"),
    ]
    rename_dict = {k: Persian_name for k, Persian_name in col_maps}
    rename_dict["date"] = "تاریخ"
    df = df.rename(columns=rename_dict)
    return df


# ----------------------------------------------------------------------
# 4. BUILDER
# ----------------------------------------------------------------------
def main():
    print("=" * 70)
    print("دادههای فیلتر و تحلیل جریان سفارشات بورس را پردازش می‌کنیم")
    print("=" * 70)
    print()

    # 4.1 Load industry files
    industry_frames = []
    for greg_date, path in INDUSTRY_WATCH_FILES:
        df = load_industry_watch(path)
        if df.empty:
            print(f"❌ {greg_date}: فایل خالی")
            continue
        df["تاریخ"] = greg_date
        # Save raw measure for unit normalization (B/M)
        print(f"✅ {greg_date}: {len(df)} صنعت")
        industry_frames.append(df)

    if not industry_frames:
        raise RuntimeError("هیچ صنایعی بارگذاری نشدند")

    industries_raw = pd.concat(industry_frames, axis=0).reset_index(drop=True)

    # Unit normalization (جداسازی واحدها: حجم B → میلیارد سهم)
    # فرض: برای حجم رسیدن به میلگرد واحد فروازیMiller B → milliارد سهم (1B = 1e9 shares)
    # ولی B = میلیارد واحد است (همان واحد ارزش) سال قبل صرف می‌شد.
    # بیایید واحد‌ها را به صورت پیش‌فرض همان واحد‌ها نگه داریم و نشان دهیم
    # ترکیب برای مقایسه زمانی مناسب است.
    # 4.2 Load symbol files
    symbol_0906 = load_symbol_watch(SYMBOL_WATCH_0906[1], SYMBOL_WATCH_0906[0])
    symbol_0830 = load_symbol_watch(SYMBOL_WATCH_0830[1], SYMBOL_WATCH_0830[0])

    print(f"✅ نمادها 09-06: {len(symbol_0906)} نماد")
    print(f"✅ نمادها 08-30: {len(symbol_0830)} نماد")
    print()

    # 4.3 Compute composite scores
    industries = metrics.compute_industry_scores(industries_raw)
    symbols_0906 = metrics.compute_symbol_scores(symbol_0906)
    symbols_0830 = metrics.compute_symbol_scores(symbol_0830)

    # 4.4 Write outputs
    # CSV
    industries.to_csv(OUTPUT_DIR / "جدول_synth_صنایع.csv", index=False, encoding="utf-8-sig")
    symbols_0906.to_csv(OUTPUT_DIR / "جدول_synth_نمادها_09-06.csv", index=False, encoding="utf-8-sig")
    symbols_0830.to_csv(OUTPUT_DIR / "جدول_synth_نمادها_08-30.csv", index=False, encoding="utf-8-sig")
    print(f"✅ CSV فایل‌ها ذخیره شدند")
    print(OUTPUT_DIR / "جدول_synth_صنایع.csv")
    print(OUTPUT_DIR / "جدول_synth_نمادها_09-06.csv")
    print(OUTPUT_DIR / "جدول_synth_نمادها_08-30.csv")
    print()

    # XLSX with styled sheets
    with pd.ExcelWriter(OUTPUT_DIR / "جدول_مقایسه_جریان_سفارش.xlsx", engine="openpyxl") as writer:
        # Sheet 1: industries
        industry_sorted = industries.sort_values("امتیاز جریان سفارش", ascending=False)
        industry_sorted.to_excel(writer, sheet_name="صنایع", index=False)
        # Sheet 2: symbols 0906
        symbols_0906.to_excel(writer, sheet_name="نمادها_09-06", index=False)
        # Sheet 3: symbols 0830
        symbols_0830.to_excel(writer, sheet_name="نمادها_08-30", index=False)

        # Freeze panes for top row
        for sheet_name in ["صنایع", "نمادها_09-06", "نمادها_08-30"]:
            ws = writer.sheets[sheet_name]
            ws.freeze_panes = "A2"

    print(f"✅ فایل XLSX ذخیره شد:")
    print(OUTPUT_DIR / "جدول_مقایسه_جریان_سفارش.xlsx")
    print()

    # 4.5 Summary text
    summary = f"""# گزارش تحلیل جریان سفارش و فیلتر هـ هـ

**تاریخ خروجی:** {datetime.now():%Y-%m-%d %H:%M}

## منابع داده

* فایل‌های tsetmc watch:
  - گروه‌ها: {INDUSTRY_WATCH_FILES}
  - نمادها: {SYMBOL_WATCH_0906[0]}, {SYMBOL_WATCH_0830[0]}
* محل‌ها: {CHECKS_DIR}

## روش تحلیل

...

## نمادهای منتخب (امین‌۱۴۰۵/۰۶/۱۵)

{symbols_0906.head(12).to_markdown(index=False)}
"""

    (OUTPUT_DIR / "README.md").write_text(summary, encoding="utf-8-sig")

    print(OUTPUT_DIR / "README.md")
    print()


if __name__ == "__main__":
    # یک تست کوچک برای تایید جو
    print(main())