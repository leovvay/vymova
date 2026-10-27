import json
m = {c["clip"]: c for c in json.load(open("clips/manifest.json"))}
a = {x["clip"]: x for x in json.load(open("out/blind_argon.json"))}
b = {x["clip"]: x for x in json.load(open("out/blind_pro31.json"))}
for k, c in m.items():
    print(f"{k} {c['time']} ASR: {c['asr']}")
    print("   A4 :", a.get(k, {}).get("phonetic"), "|", a.get(k, {}).get("notable_ru", ""))
    print("   P31:", b.get(k, {}).get("phonetic"), "|", b.get(k, {}).get("notable_ru", ""))
