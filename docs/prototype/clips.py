import json, subprocess, sys
src, audio, outdir = sys.argv[1:4]
d = json.load(open(src))
FILL = {"угу", "окей", "е", "е-е", "е-е-е", "ем", "а-а", "а-а-а", "м-м", "ну", "так"}
turns, cur = [], None
for w in d["words"]:
    if w.get("type") != "word":
        continue
    if cur and w["speaker_id"] == cur["spk"] and w["start"] - cur["end"] < 1.5:
        cur["end"] = w["end"]; cur["words"].append(w["text"])
    else:
        cur = {"spk": w["speaker_id"], "start": w["start"], "end": w["end"], "words": [w["text"]]}
        turns.append(cur)
keep = []
for t in turns:
    if t["spk"] != "speaker_0" or t["start"] < 740:
        continue
    content = [x for x in t["words"] if x.lower().strip(".,!?-—…") not in FILL]
    if not content:
        continue
    keep.append(t)
manifest = []
for i, t in enumerate(keep, 1):
    cid = f"c{i:02d}"
    s, e = max(0, t["start"] - 0.3), t["end"] + 0.4
    path = f"{outdir}/{cid}.mp3"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{s:.2f}", "-to", f"{e:.2f}", "-i", audio, "-ac", "1", "-ar", "16000", "-b:a", "64k", path], check=True)
    mm = int(t["start"])
    manifest.append({"clip": cid, "time": f"{mm//60:02d}:{mm%60:02d}", "dur": round(e - s, 1), "asr": " ".join(t["words"]), "path": path})
json.dump(manifest, open(f"{outdir}/manifest.json", "w"), ensure_ascii=False, indent=1)
print(len(manifest), "clips, total", round(sum(m["dur"] for m in manifest)), "s")
for m in manifest: print(m["clip"], m["time"], m["dur"], m["asr"][:90])
