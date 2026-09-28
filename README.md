# 🏗️ بهینهسازی خرپا با شبکههای عصبی گرافی (GNN)

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Licence](https://img.shields.io/badge/Licence-MIT-green)](LICENSE)
[![FEM](https://img.shields.io/badge/FEM-Tests-yellow)](https://github.com/izadineshat/gnn-truss-optimization)

> یک پروژهی آموزشی **قدمبهقدم** برای اینکه به کامپیوتر یاد بدهیم شکل و مقطع اعضای یک خرپا را
> طوری طراحی کند که **سبکترین وزن** را داشته باشد ولی **زیر بار خراب نشود**.

مسیر آموزشی کامل به فارسی در [`amozeshi/roadmap.md`](amozeshi/roadmap.md) نوشته شده —
این مخزن همان مسیر ۸ گامی را در قالب یک پروژهی نرمافزاری استاندارد پیاده میکند.
نسخهی انگلیسی این راهنما: [`README.en.md`](README.en.md)

---

## 🗺️ نقشهی راه

| گام | مبحث | جایگاه در پروژه | وضعیت |
|:---:|---|---|:---:|
| ۱ | بردار، ماتریس، `F = K·u` | `week1/` | ✅ |
| ۲ | میلهی تکی `k = EA/L` | `single_bar_exercise/` | ✅ |
| ۳ | اسمبل ماتریس سختی، حل سیستم | `src/trussgnn/fem/` | ✅ (پورتشده) |
| ۴ | نیروی داخلی، تنش، عکسالعمل تکیهگاه | `src/trussgnn/fem/truss.py` | ✅ (پورتشده + تست) |
| ۵ | بارگذاری چندگانه، تولید داده | `src/trussgnn/data/` | 🔜 |
| ۶ | خرپا بهصورت گراف (`edge_index`, لاپلاسین) | `src/trussgnn/graph/` | ✅ |
| ۷ | **GNN** (پیامگذاری روی گراف) | `src/trussgnn/models/` | 🔜 |
| ۸ | **بهینهسازی با GNN** 🎯 | `src/trussgnn/optimize/` | 🔜 |

## 📁 ساختار پروژه

```
gnn-truss-optimization/
├── amozeshi/                # نقشهی راه آموزشی فارسی (سند مرجع)
├── week1/                   # تمرینهای گام ۱ (مبانی ماتریس و گراف)
├── single_bar_exercise/     # تمرین گام ۲ (میلهی تکی)
├── src/trussgnn/            # ← پکیج اصلی (کد جدید و پورتشده)
│   ├── fem/                 #   هستهی اجزای محدود (گام ۳ و ۴)
│   ├── graph/               #   تبدیل خرپا به گراف (گام ۶)
│   ├── data/                #   تولید داده (گام ۵)
│   ├── models/              #   شبکههای عصبی گرافی (گام ۷)
│   └── optimize/            #   بهینهسازی (گام ۸)
├── tests/                   # تستهای pytest (اعتبارسنجی با محاسبهی دستی)
├── notebooks/               # یادداشتهای Jupyter
├── configs/                 # پیکربندی آزمایشها (YAML)
├── scripts/                 # اسکریپتهای کمکی اجرایی
└── docs/                    # مستندات فنی
```

## 🚀 اجرای سریع

```bash
# ۱. نصب وابستگیها (محیط مجازی با uv ساخته میشود)
uv sync

# ۲. اجرای تحلیل خرپای مثلثی نمونه
uv run truss-fem

# ۳. اجرای همهی تستها
uv run pytest

# ۴. اجرای نسخهی گرافیکی (رسم سازهی تغییرشکلیافته)
uv run python -c "import trussgnn.plot; from trussgnn.fem.truss import solve_tutorial; solve_tutorial(plot=True)"
```

### مثال: تحلیل خرپای مثلثی

```python
import numpy as np
from trussgnn.fem.truss import TrussModel, solve_truss

model = TrussModel(
    nodes=np.array([[0.0, 0.0], [4.0, 0.0], [2.0, 3.0]]),
    elements=np.array([[0, 1], [1, 2], [2, 0]]),
    fixed_dofs=np.array([0, 1, 2, 3]),
)
loads = np.zeros((3, 2))
loads[2, 1] = -100_000.0          # 100 kN رو به پایین روی رأس

result = solve_truss(model, loads)
print(result.displacement)         # جابجایی گرهها (متر)
print(result.axial_forces)         # نیروی داخلی هر عضو (نیوتن)
print(result.stresses)             # تنش هر عضو (پاسکال)
```

## ✅ تستها و کیفیت کد

پروژه از ابتدا **مستندمحور** طراحی شده: جوابهای عددی با محاسبهی دستی اعتبارسنجی
میشوند (اصل طلایی شماره ۱ در نقشهی راه).

| ابزار | کار | دستور |
|---|---|---|
| pytest | تستهای واحد | `uv run pytest` |
| coverage | پوشش کد | `uv run coverage run -m pytest && uv run coverage report` |
| ruff | lint + قالببندی | `uv run ruff check . && uv run ruff format --check .` |
| mypy | بررسی نوع (strict) | `uv run mypy src` |
| pre-commit | هوکهای پیش از هر کامیت | `uv run pre-commit run --all-files` |

## 🔧 توسعه

```bash
uv sync --dev --all-extras    # نصب همهی وابستگیهای توسعه
uv run pre-commit install     # فعالسازی هوکهای پیش از کامیت
```

مسیر یادگیری در [`amozeshi/roadmap.md`](amozeshi/roadmap.md) است؛ گام بعدی
**گام ۵ (تولید داده)** است.

## 📄 مجوز

MIT — برای استفادهی آموزشی آزاد است.