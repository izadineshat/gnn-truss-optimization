# 🧱 ساختاردهی اولیهی پروژه — یادداشتهای پیادهسازی

این سند خلاصهی کاری است که در مرحلهی «ساختاردهی اولیه» انجام شد و تصمیمهایی که
با کاربر گرفته شد. جزئیات فنی در `docs/architecture.md` و مسیر آموزشی در
`amozeshi/roadmap.md` است.

## تصمیمهای کلیدی (تأیید کاربر)

| موضوع | انتخاب | دلیل |
|---|---|---|
| چیدمان | src-layout با پکیج `trussgnn` | تستها همان چیزی را ایمپورت کنند که کاربر نصب میکند |
| ابزار محیط | `uv` + `pyproject.toml` | سریع، قفل `uv.lock` دارد، extras برای torch دارد |
| زبان مستندات | دوزبانه (README فارسی + README.en.md) | هم مخاطب آموزشی فارسی و هم انتشار عمومی |

## آنچه ساخته شد

- پکیج `src/trussgnn` با زیرپکیجهای `fem / graph / data / models / optimize / utils / plot / cli`.
- پورت `truss_analysis.py` به API قابلتست (`trace` شامل جابجایی، واکنش، نیرو، تنش، تعادل).
- تبدیل خرپا به گراف (`edge_index`, A, D, L, L_sym) هماهنگ با تمرین گام ۶.
- خط لولهی کیفیت: ruff, mypy (strict), pytest (46 تست), coverage (90%), pre-commit, CI (GitHub Actions).
- مستندات: README دوزبانه، docs/architecture.md، CHANGELOG.md.
- تنظیمات VS Code و فایل نمونهی آزمایشها (configs/example.yaml).

## نکات عملیاتی

- **کش uv داخل پروژه است**: `UV_CACHE_DIR=H:\gnn-truss-optimization\.uv-cache` و
  `UV_PYTHON_INSTALL_DIR=...\.uv-python` تنظیم شد چون sandbox به مسیر پیشفرض
  (`AppData`) دسترسی ندارد. هر دو در gitignore هستند. اگر حجمشان آزاردهنده شد،
  میتوانید بعد از هر `uv sync` یک بار پاکشان کنید (دوباره ساخته میشوند).
- **Windows/CLI**: `truss-fem` خروجی stdout را به UTF-8 تغییر میدهد تا روی کنسول
  cp1252 با کاراکترهای غیر-ASCII نشکند.
- **pytest cache**: برای پرهیز از خطای دسترسی sandbox، cache غیرفعال است
  (`-p no:cacheprovider`).
- **اسکریپتهای آموزشی** (`week1/`, `single_bar_exercise/`, `amozeshi/`, فایلهای ریشه)
  عمداً دستنخورده ماندند تا روند یادگیری حفظ شود؛ only پورتِ مهندسیشدهی مفاهیم
  در پکیج قرار گرفت.
