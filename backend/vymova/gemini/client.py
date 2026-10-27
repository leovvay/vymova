"""REST-клиент Gemini: загрузка аудио и генерация JSON с повторами."""
import json
import logging
import os
import time
from pathlib import Path
from typing import Any

import httpx

from ..errors import StepError

BASE = "https://generativelanguage.googleapis.com"
log = logging.getLogger("vymova.gemini")


def _delays() -> list[float]:
    return [float(x) for x in os.environ.get("VYMOVA_GEMINI_DELAYS", "10,30,90").split(",") if x]


FATAL_FINISH = {"SAFETY", "RECITATION", "PROHIBITED_CONTENT", "BLOCKLIST", "SPII", "LANGUAGE"}


def _check(r: httpx.Response) -> None:
    if r.status_code in (400, 401, 403) and ("API_KEY" in r.text or "PERMISSION_DENIED" in r.text or r.status_code != 400):
        raise StepError("Gemini отклонил ключ. Проверьте его в «Настройках».", retry=False)
    if r.status_code == 400:
        raise StepError("Gemini отклонил запрос (ошибка 400). Повтор не поможет — сообщите разработчику.", retry=False)
    if r.status_code == 404:
        raise StepError("Модель Gemini недоступна для этого ключа. Проверьте выбор моделей в «Настройках».", retry=False)


def upload(path: Path, key: str) -> str:
    size = path.stat().st_size
    with httpx.Client(timeout=600) as c:
        r = c.post(f"{BASE}/upload/v1beta/files", headers={
            "x-goog-api-key": key, "X-Goog-Upload-Protocol": "resumable", "X-Goog-Upload-Command": "start",
            "X-Goog-Upload-Header-Content-Length": str(size), "X-Goog-Upload-Header-Content-Type": "audio/mp3",
            "Content-Type": "application/json"}, json={"file": {"display_name": path.name}})
        _check(r)
        r.raise_for_status()
        url = r.headers["x-goog-upload-url"]
        with open(path, "rb") as f:
            r = c.post(url, headers={"X-Goog-Upload-Offset": "0", "X-Goog-Upload-Command": "upload, finalize"},
                       content=f.read())
        r.raise_for_status()
        info = r.json()["file"]
        for _ in range(120):
            if info.get("state") != "PROCESSING":
                break
            time.sleep(5)
            info = c.get(f"{BASE}/v1beta/{info['name']}", headers={"x-goog-api-key": key}).json()
    if info.get("state") != "ACTIVE":
        raise StepError("Gemini не смог обработать аудио урока.")
    return info["uri"]


def generate_json(model: str, parts: list[dict], key: str, schema_hint: str = "") -> Any:
    """Генерация с responseMimeType=application/json. Повторы при 429/5xx/битом JSON/не-STOP."""
    body = {"contents": [{"role": "user", "parts": parts}],
            "generationConfig": {"responseMimeType": "application/json"}}
    delays, last = _delays(), "неизвестная ошибка"
    for attempt in range(len(delays) + 1):
        try:
            r = httpx.post(f"{BASE}/v1beta/models/{model}:generateContent", json=body,
                           headers={"x-goog-api-key": key}, timeout=600)
            _check(r)
            if r.status_code == 200:
                data = r.json()
                cands = data.get("candidates") or []
                finish = cands[0].get("finishReason") if cands else (data.get("promptFeedback") or {}).get("blockReason")
                if finish == "STOP":
                    text = "".join(p.get("text", "") for p in cands[0]["content"]["parts"] if not p.get("thought"))
                    out = json.loads(text)
                    u = data.get("usageMetadata", {})
                    log.info("gemini %s ok: tokens in=%s out=%s", model, u.get("promptTokenCount"), u.get("candidatesTokenCount"))
                    return out
                if finish in FATAL_FINISH:
                    raise StepError(f"Gemini отказался отвечать ({finish}).", retry=False)
                last = f"ответ оборван ({finish})"
            else:
                last = f"ошибка {r.status_code}"
        except (httpx.HTTPError, json.JSONDecodeError, KeyError) as e:
            last = type(e).__name__
        log.warning("gemini %s attempt %d: %s", model, attempt + 1, last)
        if attempt < len(delays):
            time.sleep(delays[attempt])
    # клиент уже сделал свои повторы — раннер не должен умножать платные вызовы
    raise StepError(f"Gemini не ответил как нужно ({last}). Нажмите «Повторить».", retry=False)
