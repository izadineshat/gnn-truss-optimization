"""Dry-run half-space (ZWNJ) checker for Persian prose files."""
import re
import sys
import io
import os

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ZWJ = "\u200c"
FA = r"[\u0600-\u06FF\uFB8E\uFEFB-\uFEFC]"

FILES = [
    "README.md",
    "CHANGELOG.md",
    "docs/architecture.md",
    "docs/scaffolding-notes.md",
    "amozeshi/roadmap.md",
]

WORD_RE = re.compile(f"[{FA[1:-1]}{ZWJ}]+")

PLURAL_EXC = {"بها", "تنها", "آنها", "اینها", "ماتها", "دوها"}
TRIV_EXC = {"بهترین", "بی‌نهایت", "میانترین"}


def fix_token(tok):
    """Return (fixed, rule) or None."""
    if ZWJ in tok:
        return None

    # R1: joined plural ها/های (stem >=1 letter, not an exception word)
    for suf in ("های", "ها"):
        if tok.endswith(suf) and len(tok) > len(suf):
            stem = tok[: -len(suf)]
            if not re.fullmatch(f"{FA}+", stem):
                break
            if stem + suf in PLURAL_EXC or stem in {"تنها", "بها"}:
                break
            return f"{stem}{ZWJ}{suf}", "plural"

    # R2: mi-/nemi- verbal prefix
    m = re.match(rf"^(ن?)می({FA}.+)$", tok)
    if m:
        neg, stem = m.group(1), m.group(2)
        return f"{neg}می{ZWJ}{stem}", "mi-prefix"

    # R3: superlative ترین
    if tok.endswith("ترین") and len(tok) > 6:
        stem = tok[:-4]
        if stem == "به":
            return None
        return f"{stem}{ZWJ}ترین", "tarin"

    return None


DICTIONARY = {
    "بهینهسازی": "بهینه‌سازی",
    "شبکههای": "شبکه‌های",
    "قالببندی": "قالب‌بندی",
    "فعالسازی": "فعال‌سازی",
    "پورتشده": "پورت‌شده",
    "پورتشده+": "پورت‌شده",
    "مهندسیشده": "مهندسی‌شده",
    "مهندسیشدهی": "مهندسی‌شده‌ی",
    "قدمبهقدم": "قدم‌به‌قدم",
    "نسخهی": "نسخه‌ی",
    "تاریخچهی": "تاریخچه‌ی",
    "استفادهی": "استفاده‌ی",
    "میلهی": "میله‌ی",
    "پیشفرض": "پیش‌فرض",
    "تغييرپذير": None,
}


def main():
    total = {}
    for path in FILES:
        if not os.path.exists(path):
            print(f"!! missing: {path}")
            continue
        text = open(path, encoding="utf-8").read()
        counts = {}
        for tok in WORD_RE.findall(text):
            fixed = None
            rule = None
            if tok in DICTIONARY and DICTIONARY[tok]:
                fixed, rule = DICTIONARY[tok], "dict"
            else:
                res = fix_token(tok)
                if res:
                    fixed, rule = res
            if fixed and fixed != tok:
                key = f"{tok} → {fixed}  [{rule}]"
                counts[key] = counts.get(key, 0) + 1
        if counts:
            print(f"=== {path} ===")
            for k in sorted(counts, key=lambda x: -counts[x]):
                print(f"  {counts[k]:3d}x  {k}")
            print()
        total[path] = sum(counts.values())
    print("TOTAL candidates per file:", total)


if __name__ == "__main__":
    main()
