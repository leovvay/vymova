"""Minimal Gemini client: upload audio via Files API, run generateContent.

usage:
  gem.py upload <audio> <out_uri_file>
  gem.py gen <model> <prompt_file> <out_json> [--file-uri URI | --inline AUDIO] [--json]
"""
import json, os, sys, time, urllib.request, mimetypes

KEY = os.environ["GEMINI_API_KEY"]
BASE = "https://generativelanguage.googleapis.com"


def req(url, data=None, headers=None, method=None, raw=False):
    h = {"x-goog-api-key": KEY}
    h.update(headers or {})
    r = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=1800) as resp:
            body = resp.read()
            return (resp.headers, body) if raw else json.loads(body)
    except urllib.error.HTTPError as e:
        sys.stderr.write(f"HTTP {e.code}: {e.read().decode()[:2000]}\n")
        sys.exit(1)


def upload(path, out):
    size = os.path.getsize(path)
    mime = "audio/mp3"
    hdrs, _ = req(
        f"{BASE}/upload/v1beta/files",
        data=json.dumps({"file": {"display_name": os.path.basename(path)}}).encode(),
        headers={
            "X-Goog-Upload-Protocol": "resumable",
            "X-Goog-Upload-Command": "start",
            "X-Goog-Upload-Header-Content-Length": str(size),
            "X-Goog-Upload-Header-Content-Type": mime,
            "Content-Type": "application/json",
        },
        method="POST",
        raw=True,
    )
    url = hdrs["x-goog-upload-url"]
    with open(path, "rb") as f:
        _, body = req(
            url,
            data=f.read(),
            headers={"X-Goog-Upload-Offset": "0", "X-Goog-Upload-Command": "upload, finalize"},
            method="POST",
            raw=True,
        )
    info = json.loads(body)["file"]
    name = info["name"]
    while info.get("state") == "PROCESSING":
        time.sleep(5)
        info = req(f"{BASE}/v1beta/{name}")
    print(info.get("state"), info["uri"])
    open(out, "w").write(info["uri"])


def gen(model, prompt_file, out, file_uri=None, inline=None, as_json=False):
    import base64

    parts = []
    if file_uri:
        parts.append({"file_data": {"mime_type": "audio/mp3", "file_uri": file_uri}})
    if inline:
        mime = mimetypes.guess_type(inline)[0] or "audio/mp3"
        parts.append({"inline_data": {"mime_type": mime, "data": base64.b64encode(open(inline, "rb").read()).decode()}})
    parts.append({"text": open(prompt_file).read()})
    body = {"contents": [{"role": "user", "parts": parts}]}
    if as_json:
        body["generationConfig"] = {"responseMimeType": "application/json"}
    t = time.time()
    resp = req(
        f"{BASE}/v1beta/models/{model}:generateContent",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    json.dump(resp, open(out + ".raw.json", "w"), ensure_ascii=False, indent=1)
    cands = resp.get("candidates") or []
    text = "".join(p.get("text", "") for p in (cands[0].get("content", {}).get("parts", []) if cands else []) if not p.get("thought"))
    open(out, "w").write(text)
    print(f"{model}: {time.time() - t:.0f}s, usage={resp.get('usageMetadata', {}).get('totalTokenCount')}, finish={cands[0].get('finishReason') if cands else resp.get('promptFeedback')}")


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "upload":
        upload(a[1], a[2])
    else:
        fu = a[a.index("--file-uri") + 1] if "--file-uri" in a else None
        il = a[a.index("--inline") + 1] if "--inline" in a else None
        gen(a[1], a[2], a[3], file_uri=fu, inline=il, as_json="--json" in a)
