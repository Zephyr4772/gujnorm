# -*- coding: utf-8 -*-
"""Score the blind listening test: python score_abtest.py [out/abtest/answers.json]"""
import json, sys, pathlib
from math import comb

ROOT = pathlib.Path(__file__).parent
ans_path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "out" / "abtest" / "answers.json"
key = json.load(open(ROOT / "out" / "abtest" / "key.json", encoding="utf-8"))
answers = json.load(open(ans_path, encoding="utf-8"))["answers"]


def sign_test_p(wins, losses):
    """two-sided exact binomial sign test, ties excluded"""
    n = wins + losses
    if n == 0:
        return 1.0
    k = max(wins, losses)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k, n + 1)) / 2 ** n)


def summarize(ids):
    s = {"n": 0, "fixed_correct": 0, "raw_correct": 0, "prefer_fixed": 0, "prefer_raw": 0, "same": 0}
    for tid in ids:
        a, k = answers.get(tid), key[tid]
        if not a or a.get("pref") is None:
            continue
        f, r = k["fixed_is"], 3 - k["fixed_is"]
        s["n"] += 1
        s["fixed_correct"] += a[f"c{f}"] is True
        s["raw_correct"] += a[f"c{r}"] is True
        if a["pref"] == "same":
            s["same"] += 1
        elif int(a["pref"]) == f:
            s["prefer_fixed"] += 1
        else:
            s["prefer_raw"] += 1
    s["sign_test_p"] = round(sign_test_p(s["prefer_fixed"], s["prefer_raw"]), 6)
    return s


groups = {"ALL": list(key)}
for tid, k in key.items():
    groups.setdefault(k["voice"], []).append(tid)
result = {g: summarize(ids) for g, ids in groups.items()}
for g, s in result.items():
    n = s["n"] or 1
    print(f"{g:14} n={s['n']:2}  judged correct: raw {s['raw_correct']}/{s['n']} -> gujnorm {s['fixed_correct']}/{s['n']}   "
          f"prefer gujnorm {s['prefer_fixed']} / raw {s['prefer_raw']} / same {s['same']}   (sign test p={s['sign_test_p']})")
json.dump(result, open(ROOT / "out" / "abtest" / "score.json", "w", encoding="utf-8"), indent=1)
