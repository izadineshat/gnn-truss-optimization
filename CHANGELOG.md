# تاریخچهی تغییرات

قالب این فایل [Keep a Changelog](https://keepachangelog.com/fa-IR/1.1.0/) است و
نسخهها از [Semantic Versioning](https://semver.org/lang/fa/) پیروی میکنند.

## [0.1.0] — ساختاردهی اولیه (2026-?)

### افزودهشده
- ساختار `src-layout` با پکیج `trussgnn` (زیرپکیجهای `fem`, `graph`, `data`, `models`, `optimize`, `utils`).
- پورت کامل اسکریپت آموزشی `truss_analysis.py` به API قابلتست:
  - `TrussModel` / `TrussResult`، اسمبل ماتریس سختی، حل سیستم، عکسالعمل تکیهگاه،
    نیروی داخلی و تنش هر عضو، چک تعادل (`equilibrium_error`).
- تبدیل خرپا به گراف: `edge_index`, `adjacency`, `degree`, `laplacian`,
  `normalized_laplacian`, `edge_attributes`, `truss_to_graph`.
- پیکربندی ابزارها: `pyproject.toml` (uv/hatchling)، `ruff`، `mypy`، `pytest`، `coverage`، `pre-commit`.
- تستهای pytest اعتبارسنجیشده با محاسبهی دستی (میلهی تکی، خرپای مثلثی، گراف، CLI).
- دستور CLI: `truss-fem` (اجرای مسئلهی نمونه و گزارش نیرو/تنش/واکنش).
- مستندات دوزبانه: `README.md` (فارسی)، `README.en.md`، `docs/architecture.md`، `CHANGELOG.md`.
- پیکربندی VS Code (`settings.json`, `launch.json`, `extensions.json`) و `configs/example.yaml`.
- CI با GitHub Actions (تست، lint، type-check) روی Python 3.10–3.12 و Windows/Ubuntu.

### تغییر دادهشده
- `.gitignore` تکمیل شد (کش uv، دادهها، شکلها).
- `.vscode/launch.json` بهروزرسانی شد (مسیر پورت `trussgnn.cli` و پیکربندی pytest).

### یادداشت پورت
- اسکریپتهای آموزشی (`week1/`, `single_bar_exercise/`, `amozeshi/`, فایلهای ریشه) دستنخورده
  باقی ماندند تا روند یادگیری حفظ شود؛ پکیج نسخهی مهندسیشدهی همان مفاهیم است.

[0.1.0]: https://github.com/USER/gnn-truss-optimization/releases/tag/v0.1.0