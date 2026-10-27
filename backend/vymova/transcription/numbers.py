"""Numbers that Scribe writes as digits, rendered as words (0–999)."""
UNITS = ["нуль", "один", "два", "три", "чотири", "п'ять", "шість", "сім", "вісім", "дев'ять"]
TEENS = ["десять", "одинадцять", "дванадцять", "тринадцять", "чотирнадцять", "п'ятнадцять", "шістнадцять",
         "сімнадцять", "вісімнадцять", "дев'ятнадцять"]
TENS = ["", "", "двадцять", "тридцять", "сорок", "п'ятдесят", "шістдесят", "сімдесят", "вісімдесят", "дев'яносто"]
HUNDS = ["", "сто", "двісті", "триста", "чотириста", "п'ятсот", "шістсот", "сімсот", "вісімсот", "дев'ятсот"]


def words_of(n: int) -> list[str]:
    if not 0 <= n <= 999:
        return []
    if n < 10:
        return [UNITS[n]]
    out = []
    if n >= 100:
        out.append(HUNDS[n // 100])
        n %= 100
    if 10 <= n < 20:
        out.append(TEENS[n - 10])
    else:
        if n >= 20:
            out.append(TENS[n // 10])
        if n % 10:
            out.append(UNITS[n % 10])
    return out


def spoken(token: str) -> list[str]:
    """«21» → ["двадцять", "один"]; not a number → [token]."""
    t = token.strip()
    return words_of(int(t)) if t.isdigit() and len(t) <= 3 else [token]
