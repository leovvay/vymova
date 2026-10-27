"""Systematic student deviations beyond what the model "normally" distorts in native speakers."""
import collections
import math

from .align import Ph, label_ru, substitutions

MIN_N, EXCESS, NATIVE_BLIND, P_MAX = 5, 0.25, 0.4, 0.01


def p_value(k: int, n: int, p0: float) -> float:
    """One-sided binomial test: probability of seeing ≥k distortions out of n if the student speaks like a native."""
    p0 = min(max(p0, 1e-3), 1 - 1e-3)
    lp, lq = math.log(p0), math.log(1 - p0)
    logs = [math.lgamma(n + 1) - math.lgamma(i + 1) - math.lgamma(n - i + 1) + i * lp + (n - i) * lq
            for i in range(k, n + 1)]
    top = max(logs)
    return min(1.0, math.exp(top) * sum(math.exp(x - top) for x in logs))


def count(pairs: list[tuple[dict, list[Ph], list[Ph]]]):
    """pairs: [(example {clip, word}, expected, heard)] → (totals, subs, examples)."""
    totals, subs = collections.Counter(), collections.Counter()
    examples: dict[tuple[str, str], list[dict]] = collections.defaultdict(list)
    for ex, exp, heard in pairs:
        for ctx, h in substitutions(exp, heard):
            totals[ctx] += 1
            if h != ctx.split(" ")[0]:
                subs[(ctx, h)] += 1
                if len(examples[(ctx, h)]) < 5:
                    examples[(ctx, h)].append({**ex, "heard": "".join(p.sym for p in heard),
                                               "expected": "".join(p.sym for p in exp)})
    return totals, subs, examples


def verdicts(per_model: dict[str, tuple], calibration: dict) -> list[dict]:
    flagged: dict[str, dict] = {}
    for model_id, (totals, subs, examples) in per_model.items():
        cal = (calibration.get("models") or {}).get(model_id, {})
        for (ctx, h), k in subs.items():
            n = totals[ctx]
            rate = k / n
            if n < MIN_N or rate < EXCESS:
                continue
            key = f"{ctx}→{h}"
            native = cal.get("rates", {}).get(key, 0.0) if ctx in cal.get("totals", {}) else None
            f = flagged.setdefault(key, {"pattern_key": key, "label_ru": label_ru(ctx, h), "models": {},
                                         "examples": []})
            f["examples"] += [{**ex, "model": model_id.split("/")[1]} for ex in examples[(ctx, h)][:4]]
            f["models"][model_id] = {"k": k, "n": n, "rate": round(rate, 2),
                                     "native_rate": None if native is None else round(native, 4),
                                     "p": None if native is None else round(p_value(k, n, native), 6)}
    out = []
    for f in flagged.values():
        ms = f["models"].values()
        # model has no calibration for this sound or distorts it heavily in natives — abstain
        blind = [m for m in ms if m["native_rate"] is None or m["native_rate"] >= NATIVE_BLIND]
        hits = sum(1 for m in ms if m not in blind and m["rate"] - m["native_rate"] >= EXCESS and m["p"] < P_MAX)
        f["verdict"] = "confirmed" if hits >= 2 else "likely" if hits == 1 else "unresolved" if blind else None
        if f["verdict"]:
            out.append(f)
    order = {"confirmed": 0, "likely": 1, "unresolved": 2}
    return sorted(out, key=lambda f: (order[f["verdict"]], -max(m["rate"] for m in f["models"].values())))
