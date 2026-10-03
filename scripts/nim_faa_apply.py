"""Fix joined Persian words (missing half-space/ZWNJ) in prose Markdown files.

Convention inferred from the author's own amozeshi/roadmap.md:
  plural ها/های, ezafe ـه‌ی, می/نمی verbal prefix, superlative ـترین,
  known compounds -> half-space. Aleph-final stems (خرپاها, دریاها) stay joined.

Usage:
  python scripts/nim_faa_apply.py            # dry-run: list every change
  python scripts/nim_faa_apply.py --write    # apply to files
"""
import io
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ZWJ = "\u200c"
FA = "\u0620-\u063A\u0641-\u064A\u0671-\u06D3\u06D5\uFB8E\uFE70-\uFE71\uFE73"
HALF = "\u00b7"  # display marker for ZWNJ in the report

FILES = [
    "README.md",
    "CHANGELOG.md",
    "docs/architecture.md",
    "docs/scaffolding-notes.md",
]

DICT = {
    "بهینهسازی": "بهینه" + ZWJ + "سازی",
    "شبکههای": "شبکه" + ZWJ + "های",
    "قالببندی": "قالب" + ZWJ + "بندی",
    "فعالسازی": "فعال" + ZWJ + "سازی",
    "پورتشده": "پورت" + ZWJ + "شده",
    "دستنخورده": "دست" + ZWJ + "نخورده",
    "مهندسیشدهی": "مهندسی" + ZWJ + "شده" + ZWJ + "ی",
    "قدمبهقدم": "قدم" + ZWJ + "به" + ZWJ + "قدم",
    "نسخهی": "نسخه" + ZWJ + "ی",
    "تاریخچهی": "تاریخچه" + ZWJ + "ی",
    "استفادهی": "استفاده" + ZWJ + "ی",
    "میلهی": "میله" + ZWJ + "ی",
    "اندازهی": "اندازه" + ZWJ + "ی",
    "پیشفرض": "پیش" + ZWJ + "فرض",
    "عکسالعمل": "عکس" + ZWJ + "العمل",
    "تکیهگاه": "تکیه" + ZWJ + "گاه",
    "تکیهگاههای": "تکیه" + ZWJ + "گاه" + ZWJ + "های",
    "تغییرشکلیافته": "تغییرشکل" + ZWJ + "یافته",
    "مقیاسپذیری": "مقیاس" + ZWJ + "پذیری",
    "بارگذاری": None,  # standard joined
}

# words that merely LOOK like می+verb or ها plural but must not be split
MI_EXCL = {"میانگین", "میله", "میوه", "میان", "میزان", "میدان", "میهمان",
           "میمون", "مینا", "میخ", "می", "نیم", "بیمه", "لیمو", "سیمان",
           "دایمی", "موقتی"}
PLURAL_EXCL = {"تنها", "بها", "آنها", "اینها", "بهای", "موها", "خواها",
               "چیزها", "چیزهای", "بسیاری", "گوناگون"}
TARIN_EXCL = {"بهترین", "بیشترین", "کمترین"}

WORD = re.compile("[" + FA + "]+" + "(?:" + ZWJ + "[" + FA + "]+)*")


def fix_word(w):
    if ZWJ in w:
        return None
    if w in DICT:
        return DICT[w]
    m = re.match("^(ن?)می([" + FA + "]+)$", w)
    if m and w not in MI_EXCL:
        return m.group(1) + "می" + ZWJ + m.group(2)
    for suf in ("های", "ها"):
        if w.endswith(suf) and len(w) > len(suf):
            stem = w[: -len(suf)]
            if w in PLURAL_EXCL or stem in PLURAL_EXCL:
                return None
            if stem.endswith("ا"):
                return None  # خرپاها, دریاها: aleph does not accept ZWNJ
            return stem + ZWJ + suf
    if w.endswith("ترین") and w not in TARIN_EXCL and len(w) > 6:
        return w[:-4] + ZWJ + "ترین"
    return None


def fix_text(text):
    changes = {}

    def repl(m):
        w = m.group(0)
        fixed = fix_word(w)
        if fixed:
            changes.setdefault((w, fixed), 0)
            changes[(w, fixed)] += 1
            return fixed
        return w

    return WORD.sub(repl, text), changes


def vis(s):
    return s.replace(ZWJ, HALF)


def main():
    write = "--write" in sys.argv
    total = 0
    for path in FILES:
        try:
            text = open(path, encoding="utf-8").read()
        except FileNotFoundError:
            print("!! missing:", path)
            continue
        new, changes = fix_text(text)
        if changes:
            n = sum(changes.values())
            total += n
            print("=== %s — %d fixes ===" % (path, n))
            for (src, dst), c in sorted(changes.items(), key=lambda x: -x[1]):
                print("  %2dx  %s  →  %s" % (c, vis(src), vis(dst)))
            print()
        if write and new != text:
            open(path, "w", encoding="utf-8", newline="\n").write(new)
    print(("APPLIED" if write else "DRY-RUN") + ": %d replacements in %d files"
          % (total, len(FILES)))


if __name__ == "__main__":
    main()
