"""Phone recognition per Scribe turn; assigns recognised IPA phones to Scribe words.

usage: phones.py <model_id> <scribe.json> <wav16k> <out.json>
"""
import json, sys
import numpy as np, soundfile as sf, torch
from transformers import AutoProcessor, Wav2Vec2ForCTC

model_id, scribe, wav, out = sys.argv[1:5]
audio, sr = sf.read(wav, dtype="float32")
assert sr == 16000
dev = "mps" if torch.backends.mps.is_available() else "cpu"
proc = AutoProcessor.from_pretrained(model_id)
model = Wav2Vec2ForCTC.from_pretrained(model_id).to(dev).eval()
vocab = {v: k for k, v in proc.tokenizer.get_vocab().items()}
blank = proc.tokenizer.pad_token_id

words = [w for w in json.load(open(scribe))["words"] if w.get("type") == "word" and w["start"] >= 740]
# Scribe sometimes stretches a word over a silence; clamp absurd durations
for w in words:
    if w["end"] - w["start"] > 3:
        w["start"] = w["end"] - 0.6

turns, cur = [], None
for w in words:
    if cur and w["speaker_id"] == cur["spk"] and w["start"] - cur["end"] < 1.0 and w["end"] - cur["start"] < 25:
        cur["end"] = w["end"]; cur["words"].append(w)
    else:
        cur = {"spk": w["speaker_id"], "start": w["start"], "end": w["end"], "words": [w]}
        turns.append(cur)

res = []
for t in turns:
    s, e = max(0.0, t["start"] - 0.15), t["end"] + 0.15
    seg = audio[int(s * sr): int(e * sr)]
    if len(seg) < sr * 0.2:
        continue
    inp = proc(seg, sampling_rate=sr, return_tensors="pt").input_values.to(dev)
    with torch.no_grad():
        logits = model(inp).logits[0].float().cpu()
    ids = logits.argmax(-1).numpy()
    stride = len(seg) / sr / len(ids)
    phones, prev = [], None
    for i, tok in enumerate(ids):
        if tok != prev and tok != blank:
            phones.append((s + (i + 0.5) * stride, vocab[int(tok)]))
        prev = tok
    for w in t["words"]:
        ph = [p for (tt, p) in phones if w["start"] - 0.04 <= tt <= w["end"] + 0.04]
        res.append({"spk": w["speaker_id"], "t": round(w["start"], 2), "text": w["text"], "phones": " ".join(ph)})
json.dump(res, open(out, "w"), ensure_ascii=False, indent=0)
print(model_id, "turns", len(turns), "words", len(res))
