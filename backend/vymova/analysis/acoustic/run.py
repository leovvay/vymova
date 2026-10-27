"""The "Acoustics" step: phones of student turns against the dictionary reference, corrected by calibration."""
import json
from pathlib import Path

from ...transcription import spoken, words
from . import lexicon, recognizer
from .align import norm_word, tokens
from .findings import count, verdicts

CALIBRATION = Path(__file__).parent / "calibration.json"


def run(lesson_dir: Path, transcript: dict, folders: dict[str, str], gemini_key: str, enabled: bool) -> None:
    out_dir = lesson_dir / "acoustic"
    out_dir.mkdir(exist_ok=True)
    if not enabled or not recognizer.available():
        reason = "выключена в настройках" if not enabled else "модели не установлены"
        for folder in folders.values():
            (out_dir / f"{folder}.json").write_text(json.dumps({"skipped": True, "reason_ru": reason},
                                                               ensure_ascii=False), encoding="utf-8")
        return
    by_i = {w.i: w for w in words(transcript)}
    manifests = {f: json.loads((lesson_dir / "clips" / f / "manifest.json").read_text(encoding="utf-8"))
                 for f in folders.values()}
    def lex(i: int) -> list[str]:
        return [norm_word(x) for x in spoken(norm_word(by_i[i].text))] if i in by_i else []

    ipa = lexicon.expected_ipa([w for m in manifests.values() for c in m for i in c["word_idx"] for w in lex(i)],
                               gemini_key)
    turns = [[(i, by_i[i].start, by_i[i].end) for i in c["word_idx"] if i in by_i]
             for m in manifests.values() for c in m]
    heard_by_model = {m: recognizer.phones_per_word(m, lesson_dir / "audio16k.wav", turns) for m in recognizer.MODELS}
    cal = json.loads(CALIBRATION.read_text(encoding="utf-8")) if CALIBRATION.exists() else {}
    for folder, manifest in manifests.items():
        per_model = {}
        for model_id, heard in heard_by_model.items():
            pairs = []
            for c in manifest:
                for i in c["word_idx"]:
                    ws = lex(i)
                    if ws and all(ipa.get(w) for w in ws) and heard.get(i):
                        exp = [p for w in ws for p in tokens(ipa[w])]
                        pairs.append(({"clip": c["clip"], "word": by_i[i].text}, exp, tokens(" ".join(heard[i]))))
            per_model[model_id] = count(pairs)
        phones = {str(i): {m: heard_by_model[m].get(i, []) for m in recognizer.MODELS}
                  for c in manifest for i in c["word_idx"]}
        result = {"skipped": False, "findings": verdicts(per_model, cal),
                  "expected": {by_i[i].text: " ".join(ipa.get(w) or "?" for w in lex(i))
                               for c in manifest for i in c["word_idx"] if i in by_i},
                  "phones": phones}
        (out_dir / f"{folder}.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
