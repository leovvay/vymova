import httpx

from ..errors import StepError
from .client import BASE, _check

BLIND_PAIRS = [("gemini-4-argon", "gemini-3.1-pro-preview"),
               ("gemini-3.1-pro-preview", "gemini-3.8-flash"),
               ("gemini-2.5-pro", "gemini-3.8-flash")]
MAIN = ["gemini-4-argon", "gemini-3.1-pro-preview", "gemini-2.5-pro"]


def available(key: str) -> list[str]:
    if not key:
        raise StepError("Не задан ключ Gemini. Откройте «Настройки».", retry=False)
    r = httpx.get(f"{BASE}/v1beta/models", headers={"x-goog-api-key": key}, params={"pageSize": 1000}, timeout=30)
    _check(r)
    r.raise_for_status()
    return [m["name"].removeprefix("models/") for m in r.json().get("models", [])
            if "generateContent" in m.get("supportedGenerationMethods", [])]


def pick_blind_pair(key: str, override: list[str] | None = None) -> tuple[str, str] | None:
    have = set(available(key))
    if override and len(override) == 2 and override[0] != override[1] and set(override) <= have:
        return override[0], override[1]
    return next((p for p in BLIND_PAIRS if set(p) <= have), None)


def pick_main(key: str) -> str:
    have = set(available(key))
    for m in MAIN:
        if m in have:
            return m
    raise StepError("Для этого ключа нет подходящей модели Gemini (нужна Pro-модель).", retry=False)
