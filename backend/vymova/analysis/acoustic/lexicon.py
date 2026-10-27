"""Reference word pronunciation: Wiktionary (en.wiktionary, Ukrainian section), else Gemini. Disk cache."""
import json
import logging
import os
import re
import threading
from concurrent.futures import ThreadPoolExecutor
from html import unescape

import httpx

from ... import gemini
from ...config import paths

log = logging.getLogger("vymova.lexicon")
_lock = threading.Lock()
UA = {"User-Agent": "vymova/0.1 (https://github.com/leovvay/vymova)"}
_UKR = re.compile(r'<h2[^>]*id="Ukrainian"[^>]*>(.*?)(?:<h2[ >]|$)', re.S)
_IPA = re.compile(r'<span class="IPA[^"]*"[^>]*>([\[/][^<]+)</span>')
UKR_LETTERS = re.compile(r"^[абвгґдеєжзиіїйклмнопрстуфхцчшщьюя'-]+$")
GEMINI_PROMPT = """Give the standard Ukrainian literary pronunciation (orthoepic norm) of each word in IPA.
Use: primary stress ˈ before the stressed syllable; ʲ for palatalised consonants; ɪ for и, i for і, ɛ for е, ɔ for о;
ʋ for в before vowels and u̯ for в at the end of a syllable; ɦ for г; t͡s, t͡ʃ for ц, ч (ч is hard); no vowel reduction.
If a word is not Ukrainian (Russian, Polish, English…), return null for it.
Return JSON only: {"word": "ipa or null", ...}
Words: """


def _load() -> dict:
    f = paths().lexicon_cache
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


def _save(cache: dict) -> None:
    f = paths().lexicon_cache
    tmp = f.with_suffix(".tmp")
    tmp.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, f)


def _merge(entries: dict) -> None:
    with _lock:
        cache = _load()
        cache.update(entries)
        _save(cache)


def wiktionary(word: str) -> str | None:
    try:
        r = httpx.get(f"https://en.wiktionary.org/api/rest_v1/page/html/{word}", headers=UA, timeout=20,
                      follow_redirects=True)
    except httpx.HTTPError:
        return None
    if r.status_code != 200:
        return None
    sec = _UKR.search(r.text)
    m = _IPA.search(sec.group(1)) if sec else None
    return unescape(m.group(1)).strip("[]/") if m else None


def _pick_fast(key: str) -> str:
    have = set(gemini.available(key))
    return next((m for m in ("gemini-3.8-flash", "gemini-3.5-flash", "gemini-2.5-flash") if m in have),
                None) or gemini.pick_main(key)


def expected_ipa(words: list[str], gemini_key: str) -> dict[str, str | None]:
    """{word: IPA or None (not Ukrainian)}; words arrive already normalised (align.norm_word)."""
    want = sorted({w for w in words if w and UKR_LETTERS.match(w)})
    with _lock:
        cache = _load()
    todo = [w for w in want if w not in cache]
    if todo:
        with ThreadPoolExecutor(max_workers=8) as ex:
            wik = dict(zip(todo, ex.map(wiktionary, todo)))
        _merge({w: {"ipa": ipa, "source": "wiktionary"} for w, ipa in wik.items() if ipa})
        missing = [w for w in todo if not wik[w]]
        log.info("lexicon: %d new words, %d from wiktionary, %d via gemini", len(todo), len(todo) - len(missing),
                 len(missing))
        if missing:
            model = _pick_fast(gemini_key)

            def ask(batch: list[str]) -> None:
                got = gemini.generate_json(model, [{"text": GEMINI_PROMPT + json.dumps(batch, ensure_ascii=False)}],
                                           gemini_key)
                got = got if isinstance(got, dict) else {}
                _merge({w: {"ipa": got.get(w), "source": "gemini"} for w in batch})

            with ThreadPoolExecutor(max_workers=4) as ex:
                list(ex.map(ask, [missing[i:i + 40] for i in range(0, len(missing), 40)]))
        with _lock:
            cache = _load()
    return {w: (cache.get(w) or {}).get("ipa") for w in want}
