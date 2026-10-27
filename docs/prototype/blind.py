import base64, json, os, sys, time, urllib.request
KEY = os.environ["GEMINI_API_KEY"]
model, manifest, out = sys.argv[1:4]
clips = json.load(open(manifest))
PROMPT = """You are a phonetician. Below are short audio clips of ONE adult non-native learner speaking (mostly) Ukrainian during a lesson; some clips are spontaneous chat and may contain words from other Slavic languages. Occasionally another voice (the teacher) intrudes briefly — mark that as [other] and do not transcribe it.

For EACH clip produce a NARROW phonetic transcription in Cyrillic of exactly what the learner pronounces — NOT the dictionary spelling of the word he probably meant.
- Mark the stressed vowel with an acute accent on every word of 2+ syllables.
- Mark palatalised (soft) consonants with ' (e.g. д'е vs де, т' vs т, ц' vs ц, р'і vs ри).
- Write unstressed vowels exactly as heard: distinguish а / о, е / и / і / є.
- Write word-final consonants exactly as heard (т', ть, ч', ц', ць, ў, ф, л …). Mark long consonants by doubling (ц':).
- Write fillers (е-е) and false starts as heard.
- If a word clearly is Russian, Belarusian or Polish, still just write what you hear.
Do not guess what the speaker intended; do not normalise to standard Ukrainian. Accuracy matters more than readability.

Return JSON only: [{"clip":"c01","phonetic":"...","non_ukrainian_words":["..."],"notable_ru":"short note in Russian on any clearly audible non-standard pronunciation, or empty"}]"""
parts = [{"text": PROMPT}]
for c in clips:
    parts.append({"text": f"\nClip {c['clip']}:"})
    parts.append({"inline_data": {"mime_type": "audio/mp3", "data": base64.b64encode(open(c["path"], "rb").read()).decode()}})
body = {"contents": [{"role": "user", "parts": parts}], "generationConfig": {"responseMimeType": "application/json"}}
r = urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                           data=json.dumps(body).encode(), headers={"x-goog-api-key": KEY, "Content-Type": "application/json"})
t = time.time()
try:
    resp = json.loads(urllib.request.urlopen(r, timeout=1800).read())
except urllib.error.HTTPError as e:
    sys.exit(f"HTTP {e.code}: {e.read().decode()[:1500]}")
c0 = resp["candidates"][0]
text = "".join(p.get("text", "") for p in c0["content"]["parts"] if not p.get("thought"))
open(out, "w").write(text)
print(model, f"{time.time()-t:.0f}s", c0.get("finishReason"), resp.get("usageMetadata", {}).get("totalTokenCount"), "items:", len(json.loads(text)))
