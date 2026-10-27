"""Голосовые отпечатки (x-vector WavLM-SV) для подсказки имён между уроками."""
import json
import threading
from pathlib import Path

from ..config import paths
from ..jsonio import write_json
from ..transcription import group, words

MODEL_DIR_NAME = "wavlm-base-plus-sv"
MAX_TOTAL, MAX_SEG, MIN_SEG = 60.0, 10.0, 1.5
_lock = threading.Lock()


def available() -> bool:
    try:
        import torch  # noqa: F401
        import transformers  # noqa: F401
    except ImportError:
        return False
    return (paths().models_dir / MODEL_DIR_NAME).exists()


def _segments(transcript: dict, speaker_id: str) -> list[tuple[float, float]]:
    turns = [t for t in group(words(transcript)) if t.speaker == speaker_id and t.end - t.start >= MIN_SEG]
    out, total = [], 0.0
    for t in sorted(turns, key=lambda t: t.end - t.start, reverse=True):
        end = min(t.end, t.start + MAX_SEG)
        out.append((t.start, end))
        total += end - t.start
        if total >= MAX_TOTAL:
            break
    return out


def _load():
    from transformers import AutoFeatureExtractor, WavLMForXVector

    d = paths().models_dir / MODEL_DIR_NAME
    return AutoFeatureExtractor.from_pretrained(d), WavLMForXVector.from_pretrained(d).eval()


def embed(wav16k: Path, segments: list[tuple[float, float]], fe=None, model=None) -> list[float] | None:
    """Среднее нормированных x-vector по сегментам; None, если речи нет."""
    if not segments:
        return None
    import soundfile as sf
    import torch

    if model is None:
        fe, model = _load()
    with _lock:
        vecs = []
        with sf.SoundFile(str(wav16k)) as f:
            for s, e in segments:
                f.seek(int(s * 16000))
                chunk = f.read(int((e - s) * 16000), dtype="float32")
                inp = fe(chunk, sampling_rate=16000, return_tensors="pt")
                with torch.no_grad():
                    v = model(**inp).embeddings[0]
                vecs.append(torch.nn.functional.normalize(v, dim=-1))
    mean = torch.nn.functional.normalize(torch.stack(vecs).mean(0), dim=-1)
    return [round(float(x), 6) for x in mean]


def lesson_embeddings(lesson_dir: Path, transcript: dict, speaker_ids: list[str]) -> dict[str, list[float]]:
    """Считает и кэширует отпечатки голосов урока в voice_embeddings.json."""
    cache = lesson_dir / "voice_embeddings.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    out = {}
    if available():
        fe, model = _load()
        for spk in speaker_ids:
            v = embed(lesson_dir / "audio16k.wav", _segments(transcript, spk), fe, model)
            if v:
                out[spk] = v
        del fe, model
    write_json(cache, out)
    return out


def cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b)) / ((sum(x * x for x in a) ** 0.5) * (sum(y * y for y in b) ** 0.5) or 1)
