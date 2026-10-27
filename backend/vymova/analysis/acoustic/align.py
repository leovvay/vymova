"""IPA → грубые классы звуков и выравнивание ожидаемого произношения с услышанным."""
import re
from dataclasses import dataclass

VOWELS = {"a", "o", "e", "ə", "i", "ɪ", "ɨ", "u"}
_VOWEL_MAP = {"a": "a", "ɑ": "a", "ɐ": "a", "ʌ": "a", "æ": "a", "ä": "a", "o": "o", "ɔ": "o", "ɒ": "o", "ɵ": "o",
              "e": "e", "ɛ": "e", "ə": "ə", "ɚ": "ə", "ɜ": "ə", "ᵻ": "ə", "i": "i", "ɪ": "ɪ", "ɨ": "ɨ", "y": "ɨ",
              "ɯ": "ɨ", "ʉ": "ɨ", "u": "u", "ʊ": "u", "œ": "e", "ø": "e"}
_CONS_MAP = {"ɾ": "r", "ɹ": "r", "ʁ": "r", "ɫ": "l", "ɭ": "l", "ɬ": "l", "β": "v", "ʋ": "w", "ʍ": "w", "ɸ": "f", "h": "ɦ",
             "χ": "x", "g": "ɡ", "ʝ": "j", "S": "ʃ", "Z": "ʒ", "ɖ": "d", "ʈ": "t", "ɳ": "n", "ɽ": "r", "ɻ": "r",
             "ʂ": "ʃ", "ʐ": "ʒ"}
_PALATAL = {"ɲ": "nʲ", "ʎ": "lʲ", "ɟ": "dʲ", "c": "tʲ", "ɕ": "sʲ", "ʑ": "zʲ", "ç": "sʲ", "tɕ": "tʃʲ", "dʑ": "dʒʲ"}
_MULTI = ["tʃ", "dʒ", "ts", "dz", "tɕ", "dʑ", "tS", "dZ"]
_DROP = set("ˌː:.[]^̪̞̃ʰˤ͡‍0123456789\"'()⁽⁾/") | {"̩", "̝", "̊"}
VOICING = [("b", "p"), ("d", "t"), ("ɡ", "k"), ("z", "s"), ("ʒ", "ʃ"), ("v", "f"), ("dz", "ts"), ("dʒ", "tʃ"), ("ɦ", "x")]
_PAIR = {frozenset(p) for p in VOICING} | {frozenset(("w", "v")), frozenset(("w", "f")), frozenset(("w", "u"))}


@dataclass(frozen=True)
class Ph:
    sym: str
    stressed: bool = False


def tokens(ipa: str) -> list[Ph]:
    """Грубая токенизация IPA (и словаря, и вывода моделей). Ударение помечается у первой гласной после ˈ."""
    s = ipa.replace("u̯", "w").replace("i̯", "j").replace("͡", "").replace("‍", "")
    out: list[Ph] = []
    stress_next, i = False, 0
    while i < len(s):
        ch = s[i]
        if ch == "ˈ":
            stress_next, i = True, i + 1
            continue
        if ch in _DROP or ch.isspace():
            i += 1
            continue
        unit = next((m for m in _MULTI if s.startswith(m, i)), ch)
        i += len(unit)
        unit = {"tS": "tʃ", "dZ": "dʒ"}.get(unit, unit)
        if unit == "ʲ":
            if out and out[-1].sym not in VOWELS and not out[-1].sym.endswith("ʲ"):
                out[-1] = Ph(out[-1].sym + "ʲ", out[-1].stressed)
            continue
        if unit in _PALATAL:
            out.append(Ph(_PALATAL[unit]))
            continue
        if unit in _VOWEL_MAP:
            out.append(Ph(_VOWEL_MAP[unit], stress_next))
            stress_next = False
            continue
        out.append(Ph(_CONS_MAP.get(unit, unit)))
    vowels = [k for k, p in enumerate(out) if p.sym in VOWELS]
    if len(vowels) == 1 and not out[vowels[0]].stressed and "ˈ" not in ipa:
        out[vowels[0]] = Ph(out[vowels[0]].sym, True)
    return out


def _cost(a: str, b: str) -> float:
    if a == b:
        return 0.0
    if (a in VOWELS) == (b in VOWELS) and a in VOWELS:
        return 1.0
    ba, bb = a.rstrip("ʲ"), b.rstrip("ʲ")
    if ba == bb or frozenset((ba, bb)) in _PAIR:
        return 1.0
    return 2.0


def align(expected: list[Ph], heard: list[Ph], gap: float = 1.5) -> list[tuple[Ph | None, Ph | None]]:
    """Needleman–Wunsch. Возвращает пары (ожидаемый, услышанный); None — вставка/выпадение."""
    n, m = len(expected), len(heard)
    D = [[0.0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        D[i][0] = i * gap
    for j in range(1, m + 1):
        D[0][j] = j * gap
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            D[i][j] = min(D[i - 1][j - 1] + _cost(expected[i - 1].sym, heard[j - 1].sym),
                          D[i - 1][j] + gap, D[i][j - 1] + gap)
    out: list[tuple[Ph | None, Ph | None]] = []
    i, j = n, m
    while i > 0 or j > 0:
        if i > 0 and j > 0 and D[i][j] == D[i - 1][j - 1] + _cost(expected[i - 1].sym, heard[j - 1].sym):
            out.append((expected[i - 1], heard[j - 1])); i, j = i - 1, j - 1
        elif i > 0 and D[i][j] == D[i - 1][j] + gap:
            out.append((expected[i - 1], None)); i -= 1
        else:
            out.append((None, heard[j - 1])); j -= 1
    return out[::-1]


def context(p: Ph) -> str:
    """Ключ контекста ожидаемого звука: гласные делятся на ударные и безударные."""
    if p.sym in VOWELS:
        return f"{p.sym} ({'уд.' if p.stressed else 'безуд.'})"
    return p.sym


def substitutions(expected: list[Ph], heard: list[Ph]) -> list[tuple[str, str]]:
    """[(контекст ожидаемого, услышанный символ)] для всех выровненных пар, включая совпадения."""
    return [(context(e), h.sym) for e, h in align(expected, heard) if e is not None and h is not None]


CYR = {"a": "а", "o": "о", "e": "е", "ə": "ə", "i": "і", "ɪ": "и", "ɨ": "ы", "u": "у", "w": "ў", "v": "в", "f": "ф",
       "ɦ": "г", "ɡ": "ґ", "x": "х", "tʃ": "ч", "tʃʲ": "ч'", "ts": "ц", "tsʲ": "ць", "ʃ": "ш", "ʒ": "ж", "dʒ": "дж",
       "j": "й", "s": "с", "sʲ": "сь", "z": "з", "zʲ": "зь", "t": "т", "tʲ": "ть", "d": "д", "dʲ": "дь", "n": "н",
       "nʲ": "нь", "l": "л", "lʲ": "ль", "r": "р", "rʲ": "рь", "m": "м", "b": "б", "p": "п", "k": "к", "kʲ": "кь"}


def cyr(sym: str) -> str:
    return CYR.get(sym, sym)


def label_ru(ctx: str, heard: str) -> str:
    base, _, rest = ctx.partition(" ")
    return f"[{cyr(base)}] → [{cyr(heard)}]" + (f" {rest.strip('()')}" if rest else "")


_WORD = re.compile(r"[^\w'’-]")


def norm_word(w: str) -> str:
    return _WORD.sub("", w.lower()).replace("’", "'").strip("-'")
