import json
from pathlib import Path

import httpx

from ..errors import StepError

URL = "https://api.elevenlabs.io/v1/speech-to-text"


def transcribe(path: Path, key: str, num_speakers: int | None = None) -> dict:
    """Verbatim Scribe v2 transcription with speakers. The language is not set, to avoid "Ukrainising" inserted phrases."""
    if not key:
        raise StepError("Не задан ключ ElevenLabs. Откройте «Настройки».", retry=False)
    data = {"model_id": "scribe_v2", "diarize": "true", "timestamps_granularity": "word", "tag_audio_events": "true"}
    if num_speakers:
        data["num_speakers"] = str(num_speakers)
    try:
        with open(path, "rb") as f:
            r = httpx.post(URL, headers={"xi-api-key": key}, data=data,
                           files={"file": (path.name, f, "application/octet-stream")}, timeout=1500)
    except httpx.HTTPError as e:
        raise StepError("Нет связи с ElevenLabs. Проверьте интернет и нажмите «Повторить».") from e
    if r.status_code in (401, 403):
        raise StepError("ElevenLabs отклонил ключ. Проверьте его в «Настройках».", retry=False)
    if r.status_code == 429:
        raise StepError("ElevenLabs: превышен лимит запросов или закончились кредиты.")
    if r.status_code != 200:
        raise StepError(f"ElevenLabs вернул ошибку {r.status_code}. Нажмите «Повторить» позже.")
    out = r.json()
    if not out.get("words"):
        raise StepError("ElevenLabs не нашёл речи в записи.", retry=False)
    json.dumps(out)  # check serialisability before writing
    return out
