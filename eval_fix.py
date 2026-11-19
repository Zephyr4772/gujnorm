# -*- coding: utf-8 -*-
"""Before/after: Bulbul(raw) vs Bulbul(gujnorm.normalize(raw)), judged by Saaras verbatim."""
import json, sys
from concurrent.futures import ThreadPoolExecutor
import sv
from sweep import CONFIGS, run_item, EN_LEAK
from testset import ITEMS
from gujnorm import normalize



import re
from sweep import norm

# Spelling variants that STT may produce for the same spoken word
VARIANTS = {"સુડતાળીસ": "સુડતાલીસ", "મિલીગ્રામ": "મિલિગ્રામ", "બેતાળીસ": "બેતાલીસ", "પિસ્તાળીસ": "પિસ્તાલીસ",
            "વાગે": "વાગ્યે", "પચ્ચીસ": "પચીસ"}


def canon(s):
    for a, b in VARIANTS.items():
        s = s.replace(a, b)
    return s


def judge(r, item):
    """Saaras 'verbatim' sometimes writes numbers back as digits. Spell those digits out the same way for
    raw AND fixed (so the number's value is checked), then look for the expected spoken words."""
    if r.get("error"):
        return {"pass": False, "en": False, "missing": ["<error>"]}
    heard = r.get("verbatim") or ""
    heard_w = " " + canon(norm(normalize(heard))) + " "
    missing = [g for g in item["expect"] if not any(canon(a) in heard_w for a in g.split("|"))]
    return {"pass": not missing, "en": len(r.get("en_leak", [])) > 0, "missing": missing,
            "stt_wrote_digits": bool(re.search(r"\d", heard))}



def main(CFG_NAMES):
    summary = {}
    rows = []
    for name in CFG_NAMES:
        cfg = CONFIGS[name]
        changed = [it for it in ITEMS if normalize(it["text"]) != it["text"]]

        def both(it):
            raw = run_item(it, cfg)
            fixed = run_item({**it, "text": normalize(it["text"])}, cfg)
            return it, raw, fixed
        with ThreadPoolExecutor(4) as ex:
            res = list(ex.map(both, changed))
        s = {"items_changed": len(changed), "raw_pass": 0, "fixed_pass": 0, "raw_en_leak": 0, "fixed_en_leak": 0,
             "fixed_regressions": []}
        by_cat = {}
        for it, raw, fixed in res:
            jr, jf = judge(raw, it), judge(fixed, it)
            fixed["missing"] = jf["missing"]
            s["raw_pass"] += jr["pass"]; s["fixed_pass"] += jf["pass"]
            s["raw_en_leak"] += jr["en"]; s["fixed_en_leak"] += jf["en"]
            c = by_cat.setdefault(it["cat"], [0, 0, 0])
            c[0] += 1; c[1] += jr["pass"]; c[2] += jf["pass"]
            if jr["pass"] and not jf["pass"]:
                s["fixed_regressions"].append(it["id"])
            rows.append({"cfg": name, "id": it["id"], "cat": it["cat"], "raw_text": it["text"],
                         "fixed_text": normalize(it["text"]), "raw_heard": raw.get("verbatim"),
                         "fixed_heard": fixed.get("verbatim"), "raw_pass": jr["pass"], "fixed_pass": jf["pass"],
                         "fixed_missing": fixed.get("missing"), "fixed_en": fixed.get("en_leak"),
                         "fixed_wav": fixed.get("wav"), "raw_wav": raw.get("wav")})
        s["by_category"] = {k: {"n": v[0], "raw_pass": v[1], "fixed_pass": v[2]} for k, v in sorted(by_cat.items())}
        summary[name] = s
        print(f"\n== {name}: {len(changed)} sentences changed by gujnorm")
        print(f"   expected spoken words present: raw {s['raw_pass']}/{len(changed)}  ->  fixed {s['fixed_pass']}/{len(changed)}")
        print(f"   English words in Gujarati speech: raw {s['raw_en_leak']}  ->  fixed {s['fixed_en_leak']}")
        print(f"   regressions: {s['fixed_regressions']}")
        for k, v in s["by_category"].items():
            print(f"     {k:8} {v['raw_pass']}/{v['n']} -> {v['fixed_pass']}/{v['n']}")

    json.dump(summary, open(sv.ROOT / "out" / "eval_summary.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    with open(sv.ROOT / "out" / "eval_rows.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main(sys.argv[1:] or ["v3", "v4_pooja_cust", "v4_bhavik"])
