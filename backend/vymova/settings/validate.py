import httpx

TIMEOUT = 20


def check_elevenlabs(key: str) -> str | None:
    try:
        r = httpx.get("https://api.elevenlabs.io/v1/user/subscription", headers={"xi-api-key": key}, timeout=TIMEOUT)
    except httpx.HTTPError:
        return "Нет связи с ElevenLabs. Проверьте интернет и попробуйте ещё раз."
    if r.status_code == 200:
        return None
    if r.status_code in (401, 403):
        return "ElevenLabs отклонил ключ. Проверьте, что он скопирован целиком."
    return f"ElevenLabs ответил ошибкой {r.status_code}. Попробуйте позже."


def check_gemini(key: str) -> str | None:
    try:
        r = httpx.get("https://generativelanguage.googleapis.com/v1beta/models",
                      headers={"x-goog-api-key": key}, params={"pageSize": 1}, timeout=TIMEOUT)
    except httpx.HTTPError:
        return "Нет связи с Gemini. Проверьте интернет и попробуйте ещё раз."
    if r.status_code == 200:
        return None
    if r.status_code in (400, 401, 403):
        return "Gemini отклонил ключ. Проверьте, что он скопирован целиком и что Gemini API включён."
    return f"Gemini ответил ошибкой {r.status_code}. Попробуйте позже."
