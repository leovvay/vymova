"""Калибровка акустики на речи носителей (FLEURS uk_ua, CC-BY-4.0). Только для разработки.

Считает, как часто распознаватели «искажают» ожидаемый звук у носителей, чтобы не принимать
эти искажения за ошибки студента. Нужны: DATA_DIR (кэш словаря), MODELS_DIR, GEMINI_API_KEY.

usage: build_calibration.py --out backend/vymova/analysis/acoustic/calibration.json [--n 400] [--split dev]
"""
import argparse
import collections
import csv
import json
import os
import tarfile
from pathlib import Path

import soundfile as sf
from huggingface_hub import hf_hub_download

from vymova.analysis.acoustic import lexicon
from vymova.analysis.acoustic.align import norm_word, substitutions, tokens
from vymova.analysis.acoustic.recognizer import MODELS, Recognizer

MIN_N = 20


def fleurs(split: str, n: int, cache: Path) -> list[tuple[Path, str]]:
    tsv = hf_hub_download("google/fleurs", f"data/uk_ua/{split}.tsv", repo_type="dataset", cache_dir=cache)
    tar = hf_hub_download("google/fleurs", f"data/uk_ua/audio/{split}.tar.gz", repo_type="dataset", cache_dir=cache)
    rows = []
    with open(tsv, encoding="utf-8") as f:
        for r in csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE):
            if len(r) > 3 and (r[1], r[3]) not in rows:
                rows.append((r[1], r[3]))
    rows = rows[:n]
    out_dir = cache / "uk_ua" / split
    out_dir.mkdir(parents=True, exist_ok=True)
    wanted = {name for name, _ in rows}
    with tarfile.open(tar) as t:
        for m in t:
            base = os.path.basename(m.name)
            if base in wanted and not (out_dir / base).exists():
                (out_dir / base).write_bytes(t.extractfile(m).read())
    return [(out_dir / name, text) for name, text in rows if (out_dir / name).exists()]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--n", type=int, default=400)
    ap.add_argument("--split", default="dev")
    ap.add_argument("--cache", default="/tmp/vymova-fleurs")
    args = ap.parse_args()
    utts = fleurs(args.split, args.n, Path(args.cache))
    ipa = lexicon.expected_ipa([norm_word(w) for _, t in utts for w in t.split()], os.environ["GEMINI_API_KEY"])
    expected = []
    for path, text in utts:
        ws = [norm_word(w) for w in text.split()]
        if all(ipa.get(w) for w in ws):
            expected.append((path, [p for w in ws for p in tokens(ipa[w])]))
    print(f"{len(utts)} utterances, {len(expected)} fully covered by the lexicon")
    result = {"source": f"FLEURS uk_ua {args.split}, {len(expected)} utterances (CC-BY-4.0)", "models": {}}
    for model_id in MODELS:
        rec = Recognizer(model_id)
        totals, subs = collections.Counter(), collections.Counter()
        for path, exp in expected:
            audio, sr = sf.read(str(path), dtype="float32")
            heard = tokens(" ".join(p for _, p in rec.phones(audio)))
            for ctx, h in substitutions(exp, heard):
                totals[ctx] += 1
                subs[(ctx, h)] += 1
        rec.close()
        rates = {f"{c}→{h}": round(k / totals[c], 4) for (c, h), k in subs.items() if totals[c] >= MIN_N and c != h}
        result["models"][model_id] = {"totals": {c: n for c, n in totals.items() if n >= MIN_N}, "rates": rates}
        print(model_id, "contexts:", len(result["models"][model_id]["totals"]), "o безуд.→a:",
              rates.get("o (безуд.)→a"))
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
