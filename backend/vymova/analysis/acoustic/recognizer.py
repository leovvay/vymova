"""wav2vec2 (espeak-cv-ft) → фоны по словам. Модели грузятся по одной, Linear-слои квантуются в int8."""
import gc
import json
from pathlib import Path

from ...config import paths

MODELS = ["facebook/wav2vec2-lv-60-espeak-cv-ft", "facebook/wav2vec2-xlsr-53-espeak-cv-ft"]
SR, EDGE, MAX_SEG = 16000, 0.04, 25.0


def model_dir(model_id: str) -> Path:
    return paths().models_dir / model_id.split("/")[1]


def available() -> bool:
    try:
        import torch  # noqa: F401
        import transformers  # noqa: F401
    except ImportError:
        return False
    return all(model_dir(m).exists() for m in MODELS)


class Recognizer:
    def __init__(self, model_id: str):
        import torch
        from transformers import Wav2Vec2FeatureExtractor, Wav2Vec2ForCTC

        d = model_dir(model_id)
        self.fe = Wav2Vec2FeatureExtractor.from_pretrained(d)
        model = Wav2Vec2ForCTC.from_pretrained(d).eval()
        engines = torch.backends.quantized.supported_engines
        if "qnnpack" in engines and "fbgemm" not in engines:
            torch.backends.quantized.engine = "qnnpack"
        self.model = torch.quantization.quantize_dynamic(model, {torch.nn.Linear}, dtype=torch.qint8)
        vocab = json.loads((d / "vocab.json").read_text(encoding="utf-8"))
        self.id2tok = {v: k for k, v in vocab.items()}
        self.blank = vocab.get("<pad>", 0)

    def phones(self, audio) -> list[tuple[float, str]]:
        """[(время центра кадра от начала отрезка, фон)]"""
        import torch

        inp = self.fe(audio, sampling_rate=SR, return_tensors="pt").input_values
        with torch.no_grad():
            ids = self.model(inp).logits[0].argmax(-1).tolist()
        stride = len(audio) / SR / max(1, len(ids))
        out, prev = [], None
        for i, t in enumerate(ids):
            if t != prev and t != self.blank:
                tok = self.id2tok.get(t, "")
                if tok and not tok.startswith("<"):
                    out.append(((i + 0.5) * stride, tok))
            prev = t
        return out

    def close(self) -> None:
        del self.model
        gc.collect()


def _segments(word_spans: list[tuple[int, float, float]]) -> list[list[tuple[int, float, float]]]:
    """Режет реплику на куски ≤ MAX_SEG по границам слов."""
    segs, cur = [], []
    for w in word_spans:
        if cur and w[2] - cur[0][1] > MAX_SEG:
            segs.append(cur)
            cur = []
        cur.append(w)
    if cur:
        segs.append(cur)
    return segs


def phones_per_word(model_id: str, wav16k: Path, turns: list[list[tuple[int, float, float]]]) -> dict[int, list[str]]:
    """turns — реплики как списки (индекс слова, начало, конец). Возвращает {индекс слова: [фоны]}."""
    import soundfile as sf

    rec = Recognizer(model_id)
    out: dict[int, list[str]] = {}
    try:
        with sf.SoundFile(str(wav16k)) as f:
            for turn in turns:
                for seg in _segments(turn):
                    s, e = max(0.0, seg[0][1] - 0.15), seg[-1][2] + 0.15
                    f.seek(int(s * SR))
                    audio = f.read(int((e - s) * SR), dtype="float32")
                    if len(audio) < SR * 0.2:
                        continue
                    ph = [(s + t, p) for t, p in rec.phones(audio)]
                    for i, ws, we in seg:
                        out[i] = [p for t, p in ph if ws - EDGE <= t <= we + EDGE]
    finally:
        rec.close()
    return out
