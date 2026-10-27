import json, sys

src, dst = sys.argv[1], sys.argv[2]
d = json.load(open(src))
words = d.get("words", [])

def ts(s):
    s = int(s)
    return f"{s // 60:02d}:{s % 60:02d}"

turns, cur = [], None
for w in words:
    if w.get("type") == "spacing":
        if cur:
            cur["text"] += w["text"]
        continue
    spk = w.get("speaker_id", "?")
    text = w["text"] if w.get("type") == "word" else f" {w['text']} "
    if cur is None or cur["spk"] != spk:
        cur = {"spk": spk, "start": w.get("start", 0), "text": text}
        turns.append(cur)
    else:
        cur["text"] += text

with open(dst, "w") as f:
    for t in turns:
        f.write(f"[{ts(t['start'])}] {t['spk']}: {' '.join(t['text'].split())}\n")

stats = {}
for w in words:
    if w.get("type") == "word":
        s = stats.setdefault(w.get("speaker_id", "?"), [0, 0.0])
        s[0] += 1
        s[1] += w["end"] - w["start"]
print("lang:", d.get("language_code"), d.get("language_probability"))
print("turns:", len(turns))
for k, (n, sec) in sorted(stats.items()):
    print(f"{k}: {n} words, {sec / 60:.1f} min")
