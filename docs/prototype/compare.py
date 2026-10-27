"""Group recognised phones of target words by speaker (student / teacher / other student) for both models."""
import json, re, sys

UNITS = ["нуль", "один", "два", "три", "чотири", "п'ять", "шість", "сім", "вісім", "дев'ять"]
TEENS = ["десять", "одинадцять", "дванадцять", "тринадцять", "чотирнадцять", "п'ятнадцять", "шістнадцять", "сімнадцять", "вісімнадцять", "дев'ятнадцять"]
TENS = ["", "", "двадцять", "тридцять", "сорок", "п'ятдесят", "шістдесят", "сімдесят", "вісімдесят", "дев'яносто"]
HUNDS = ["", "сто", "двісті", "триста", "чотириста", "п'ятсот", "шістсот", "сімсот", "вісімсот", "дев'ятсот"]


def words_of(n):
    if n < 10:
        return [UNITS[n]]
    out = []
    if n >= 100:
        out.append(HUNDS[n // 100]); n %= 100
    if 10 <= n < 20:
        out.append(TEENS[n - 10])
    else:
        if n >= 20:
            out.append(TENS[n // 10])
        if n % 10:
            out.append(UNITS[n % 10])
    return out


TARGETS = {
    "один": r"^один$", "-надцять": r"надцять$", "дев'ять": r"^дев'ять$", "дев'яносто": r"^дев'яносто$",
    "-десят": r"десят$", "шість": r"^шість$", "сім": r"^сім$", "вісім": r"^вісім$", "двісті": r"^двісті$",
    "сорок": r"^сорок$", "років": r"^років$", "роки": r"^роки$", "мені": r"^мені$", "чотири": r"^чотири$",
    "двадцять/тридцять": r"^(двадцять|тридцять)$", "менше/більше": r"^(менше|більше)$",
}
NAME = {"speaker_0": "Влад", "speaker_1": "Викл", "speaker_2": "Студ2"}

models = {k: json.load(open(p)) for k, p in (a.split("=") for a in sys.argv[1:])}
base = next(iter(models.values()))
rows = {}
for i, w in enumerate(base):
    txt = re.sub(r"[^\w'’-]", "", w["text"].lower()).replace("’", "'").strip("-")
    lex = words_of(int(txt)) if txt.isdigit() and int(txt) < 1000 else [txt]
    for tname, rx in TARGETS.items():
        if any(re.search(rx, x) for x in lex):
            phones = {m: models[m][i]["phones"] for m in models}
            rows.setdefault(tname, []).append((NAME[w["spk"]], w["t"], w["text"], len(lex) > 1, phones))

for tname, items in rows.items():
    print(f"\n######## {tname}")
    for spk in ("Викл", "Влад", "Студ2"):
        for (s, t, text, multi, ph) in items:
            if s != spk:
                continue
            mark = "*" if multi else " "
            print(f"{s:5} {int(t)//60:02d}:{int(t)%60:02d} {mark}{text:16} " + " || ".join(f"{m}: {p}" for m, p in ph.items()))
