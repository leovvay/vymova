import httpx

from ..errors import StepError
from .client import BASE, _check

MAIN = ["gemini-4-argon", "gemini-3.1-pro-preview", "gemini-2.5-pro"]


def available(key: str) -> list[str]:
    if not key:
        raise StepError("Не задан ключ Gemini. Откройте «Настройки».", retry=False)
    r = httpx.get(f"{BASE}/v1beta/models", headers={"x-goog-api-key": key}, params={"pageSize": 1000}, timeout=30)
    _check(r)
    r.raise_for_status()
    return [m["name"].removeprefix("models/") for m in r.json().get("models", [])
            if "generateContent" in m.get("supportedGenerationMethods", [])]


def pick_blind_models(key: str, override: list[str] | None = None) -> list[str] | None:
    """Blind-check models. Default: one model (the main one). Settings may name one model or two distinct models;
    with two, a pattern is confirmed only when both hear it."""
    have = set(available(key))
    if override and 1 <= len(override) <= 2 and len(set(override)) == len(override) and set(override) <= have:
        return list(override)
    main = next((m for m in MAIN if m in have), None)
    return [main] if main else None


def pick_main(key: str) -> str:
    have = set(available(key))
    for m in MAIN:
        if m in have:
            return m
    raise StepError("Для этого ключа нет подходящей модели Gemini (нужна Pro-модель).", retry=False)
