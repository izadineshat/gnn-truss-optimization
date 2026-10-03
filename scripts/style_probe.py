import re
import io
import sys
from collections import Counter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ZWJ = "\u200c"
FA = "\u0600-\u06FF"

text = open("amozeshi/roadmap.md", encoding="utf-8").read()
words = re.findall(f"[{FA}]+(?:{ZWJ}[{FA}]+)*", text)

c = Counter()
samples = {}


def mark(k, w):
    c[k] += 1
    samples.setdefault(k, []).append(w.replace(ZWJ, "~"))


for w in words:
    if "های" in w:
        mark("hay-joined" if ZWJ + "های" not in w else "hay-zwnj", w)
    if w.endswith("ها") or ZWJ + "ها" in w:
        mark("ha-zwnj" if ZWJ + "ها" in w else "ha-joined", w)
    if w.endswith("هی") or ZWJ + "ی" in w:
        mark("eye-zwnj" if ZWJ + "ی" in w else "eye-joined", w)
    if re.match("^" + FA + "*", w) and re.match("^(ن?)می[" + FA + "]", w):
        mark("mi-zwnj" if ZWJ in w else "mi-joined", w)
    if w.endswith("ترین"):
        mark("tarin-zwnj" if ZWJ in w else "tarin-joined", w)
    if w.endswith("سازی") or ZWJ + "سازی" in w:
        mark("sazi-zwnj" if ZWJ + "سازی" in w else "sazi-joined", w)
    if w.endswith("بندی") or ZWJ + "بندی" in w:
        mark("bandi-zwnj" if ZWJ + "بندی" in w else "bandi-joined", w)
    if w.endswith("شده") or ZWJ + "شده" in w:
        mark("shode-zwnj" if ZWJ + "شده" in w else "shode-joined", w)

for k in sorted(c):
    print("%4d  %-14s e.g. %s" % (c[k], k, ", ".join(samples[k][:5])))
