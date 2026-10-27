"""Build PDF appendices: full phonetic transcript of Vlad's turns + Vlad-vs-teacher target-word tables.

usage: appendix.py <report.html>
"""
import html, json, re, sys

OUT = "/tmp/ua-lesson/out"
report = sys.argv[1]

scribe = json.load(open(f"{OUT}/scribe.json"))["words"]
lv = json.load(open(f"{OUT}/ph_lv60.json"))
xl = json.load(open(f"{OUT}/ph_xlsr53.json"))
blind = {
    "Argon": {x["clip"]: x for x in json.load(open(f"{OUT}/blind_argon.json"))},
    "3.1 Pro": {x["clip"]: x for x in json.load(open(f"{OUT}/blind_pro31.json"))},
}

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


def norm(t):
    return re.sub(r"[^\w'’-]", "", t.lower()).replace("’", "'").strip("-")


def ipa(s):
    return "".join(s.split()) or "—"


def mmss(t):
    t = int(t)
    return f"{t // 60:02d}:{t % 60:02d}"


e = html.escape
HL = re.compile(r"(^один|надцять$|^дев'ять$|^дев'яносто$|десят$|^двадцять$|^тридцять$|^шість$|^сім$|^вісім$|^двісті$|"
                r"^сорок$|^років$|^роки$|^мені$|^мене$|^чотири|^не$|^чи$|^менше$|^більше$|^сто$)")

# index of every Scribe word (type=word, start>=740) inside the phone files — same order as phones.py
ph_idx, k = {}, 0
for i, w in enumerate(scribe):
    if w.get("type") == "word" and w["start"] >= 740:
        ph_idx[i] = k; k += 1
assert k == len(lv) == len(xl)

# rebuild Vlad's clips exactly as clips.py did (same ids c01..c99)
FILL = {"угу", "окей", "е", "е-е", "е-е-е", "ем", "а-а", "а-а-а", "м-м", "ну", "так"}
turns, cur = [], None
for i, w in enumerate(scribe):
    if w.get("type") != "word":
        continue
    if cur and w["speaker_id"] == cur["spk"] and w["start"] - cur["end"] < 1.5:
        cur["end"] = w["end"]; cur["idx"].append(i)
    else:
        cur = {"spk": w["speaker_id"], "start": w["start"], "end": w["end"], "idx": [i]}
        turns.append(cur)
clips = []
for t in turns:
    if t["spk"] != "speaker_0" or t["start"] < 740:
        continue
    if not [i for i in t["idx"] if scribe[i]["text"].lower().strip(".,!?-—…") not in FILL]:
        continue
    clips.append(t)
assert len(clips) == 99

parts = ["""
<section class="appx">
<h2 class="pb"><span class="n">A</span>Приложение: фонетическая расшифровка всех твоих реплик</h2>
<p class="t">99 реплик подряд. В каждой: слово из расшифровки, под ним — что услышали две акустические модели (IPA), ниже — две слепые фонетические записи Gemini. Жёлтым подсвечены слова, которые проверялись в разборе. Клик по номеру реплики открывает аудио (папка <b>clips/</b> рядом с PDF).</p>
<div class="legend">
  <div><span class="sw lvc">оранжевым</span> — wav2vec2 lv-60 &nbsp; <span class="sw xlc">синим</span> — wav2vec2 XLSR-53 &nbsp; «—» — модель ничего не распознала на этом отрезке</div>
  <div><b>Шпаргалка IPA:</b> ʲ — мягкость (dʲ = дь) · ɟ — мягкое д · tʃ — ч · ts — ц · ɕ — мягкое сь / ś · ʃ — ш · f — ф · v — в ·
  ɨ, ʌ, ɐ, ə — «ы»-подобные / редуцированные гласные · ɪ — ненапряжённое и · iː — долгое і · ː — долгота · ɾ — одноударное р</div>
</div>
"""]
for n, c in enumerate(clips, 1):
    cid = f"c{n:02d}"
    cells = []
    for i in c["idx"]:
        w = scribe[i]
        txt = w["text"]
        nt = norm(txt)
        sub = ""
        if nt.isdigit():
            sub = f'<span class="dg">{e(" ".join(words_of(int(nt))))}</span>' if int(nt) < 1000 else ""
            hl = True
        else:
            hl = bool(HL.search(nt))
        j = ph_idx.get(i)
        a = ipa(lv[j]["phones"]) if j is not None else "—"
        b = ipa(xl[j]["phones"]) if j is not None else "—"
        cells.append(f'<span class="w{" hl" if hl else ""}"><span class="o">{e(txt)}{sub}</span>'
                     f'<span class="a">{e(a)}</span><span class="b">{e(b)}</span></span>')
    bl = "".join(
        f'<div class="bl"><b>{m}:</b> {e(blind[m].get(cid, {}).get("phonetic", "—"))}</div>' for m in blind)
    start = min(scribe[i]["end"] - 0.6 if scribe[i]["end"] - scribe[i]["start"] > 3 else scribe[i]["start"] for i in c["idx"])
    parts.append(f'<div class="clip"><div class="ch"><a href="clips/{cid}.mp3">{cid}</a> <span class="t">{mmss(start)}</span></div>'
                 f'<div class="il">{"".join(cells)}</div>{bl}</div>')
parts.append("</section>")

# ---- Appendix B: target words, Vlad vs teacher
TARGETS = [
    ("один", r"^один$"), ("-надцять", r"надцять$"), ("двадцять / тридцять", r"^(двадцять|тридцять)$"),
    ("-десят", r"десят$"), ("дев'ять", r"^дев'ять$"), ("дев'яносто", r"^дев'яносто$"), ("шість", r"^шість$"),
    ("сім", r"^сім$"), ("вісім", r"^вісім$"), ("двісті", r"^двісті$"), ("сорок", r"^сорок$"),
    ("чотири", r"^чотири$"), ("років", r"^років$"), ("роки", r"^роки$"), ("мені", r"^мені$"),
    ("менше / більше", r"^(менше|більше)$"),
]
rows = {name: {"speaker_1": [], "speaker_0": []} for name, _ in TARGETS}
for j, w in enumerate(lv):
    if w["spk"] not in ("speaker_0", "speaker_1"):
        continue
    nt = norm(w["text"])
    lex = words_of(int(nt)) if nt.isdigit() and int(nt) < 1000 else [nt]
    for name, rx in TARGETS:
        if any(re.search(rx, x) for x in lex):
            rows[name][w["spk"]].append((w["t"], w["text"], len(lex) > 1, ipa(w["phones"]), ipa(xl[j]["phones"])))

parts.append("""
<section class="appx">
<h2 class="pb"><span class="n">B</span>Приложение: каждое проверяемое слово — ты и преподаватель</h2>
<p class="t">Все вхождения слов из разбора. Слева — преподаватель (носитель, контроль), справа — ты. * — слово внутри числа, записанного цифрами (IPA покрывает всё число). Сравнивать стоит не отдельные строки (модели шумят даже на носителе), а то, что повторяется у тебя и не повторяется у преподавателя.</p>
""")
for name, _ in TARGETS:
    r = rows[name]
    if not r["speaker_0"]:
        continue

    def col(items):
        if not items:
            return '<div class="none">нет примеров</div>'
        return "".join(
            f'<div class="r"><span class="t">{mmss(t)}</span> <span class="wd">{"*" if multi else ""}{e(txt)}</span>'
            f' <span class="a">{e(a)}</span> <span class="b">{e(b)}</span></div>' for (t, txt, multi, a, b) in items)
    parts.append(f'<div class="tw"><h3>{e(name)}</h3><div class="cols">'
                 f'<div><div class="cl">Преподаватель · {len(r["speaker_1"])}</div>{col(r["speaker_1"])}</div>'
                 f'<div><div class="cl">Влад · {len(r["speaker_0"])}</div>{col(r["speaker_0"])}</div></div></div>')
parts.append("</section>")

CSS = """
<style id="appx-css">
  .appx .legend { font-size: 8.4pt; color: var(--muted); background: var(--soft); border-radius: 6px; padding: 7px 10px; margin: 6px 0 10px; }
  .appx .legend div { margin: 2px 0; }
  .sw { font-family: "SF Mono", Menlo, monospace; padding: 0 3px; border-radius: 3px; }
  .lvc { color: #8a3a00; background: #fff4e5; } .xlc { color: #1f4f9f; background: #e8f0fc; }
  .clip { border-bottom: 1px solid var(--line); padding: 6px 0 5px; break-inside: avoid; }
  .ch { font-size: 8.6pt; margin-bottom: 3px; } .ch a { color: var(--blue); font-weight: 700; text-decoration: none; margin-right: 4px; }
  .il { display: flex; flex-wrap: wrap; gap: 3px 9px; }
  .w { display: inline-flex; flex-direction: column; padding: 1px 3px; border-radius: 3px; }
  .w.hl { background: #fff6cf; }
  .w .o { font-size: 9.6pt; font-weight: 600; }
  .w .dg { display: block; font-size: 7.4pt; font-weight: 400; color: var(--muted); }
  .w .a, .tw .a { font-family: "SF Mono", Menlo, monospace; font-size: 7.8pt; color: #8a3a00; }
  .w .b, .tw .b { font-family: "SF Mono", Menlo, monospace; font-size: 7.8pt; color: #1f4f9f; }
  .bl { font-size: 8.5pt; color: #3b4450; margin-top: 2px; } .bl b { color: var(--muted); font-weight: 650; }
  .tw { margin: 8px 0 10px; } .tw h3 { margin: 0 0 3px; font-size: 10.4pt; break-after: avoid; } .tw .r { break-inside: avoid; }
  .tw .cols { display: grid; grid-template-columns: 1fr 1fr; gap: 0 16px; }
  .tw .cl { font-size: 7.8pt; text-transform: uppercase; letter-spacing: .05em; color: var(--muted); font-weight: 650; border-bottom: 1.5px solid var(--ink); padding-bottom: 2px; margin-bottom: 2px; }
  .tw .r { font-size: 8.4pt; padding: 1px 0; border-bottom: 1px solid var(--line); }
  .tw .wd { font-weight: 600; } .tw .none { font-size: 8.4pt; color: var(--muted); }
</style>
"""
s = open(report).read()
s = re.sub(r'<style id="appx-css">.*?</style>\n?', "", s, flags=re.S)
s = s.replace("</head>", CSS + "</head>")
s = re.sub(r"<!-- APPENDIX:START -->.*<!-- APPENDIX:END -->",
           lambda _: "<!-- APPENDIX:START -->" + "\n".join(parts) + "<!-- APPENDIX:END -->", s, flags=re.S)
open(report, "w").write(s)
print("clips", len(clips), "| targets", {k: (len(v["speaker_1"]), len(v["speaker_0"])) for k, v in rows.items()})
