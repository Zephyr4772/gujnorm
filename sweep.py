# -*- coding: utf-8 -*-
"""TTS -> STT round-trip sweep over the Gujarati test set.
Usage: python sweep.py <config-name> [<config-name> ...]
Writes out/results_<config>.jsonl
"""
import json, sys, wave, re, traceback
from concurrent.futures import ThreadPoolExecutor
import sv
from testset import ITEMS

CONFIGS = {
    "v3":        dict(model="bulbul:v3", speaker=None, preprocessing=True),
    "v3_noprep": dict(model="bulbul:v3", speaker=None, preprocessing=False),
    "v3_ishita": dict(model="bulbul:v3", speaker="ishita", preprocessing=True),
    "v4_pooja_cust": dict(model="bulbul:v4-flash", speaker="pooja_gu_customer", preprocessing=True),
    "v4_pooja_conv": dict(model="bulbul:v4-flash", speaker="pooja_gu_conversational", preprocessing=True),
    "v4_bhavik": dict(model="bulbul:v4-flash", speaker="bhavik_gu_conversation", preprocessing=True),
    "v4_pooja_cust_noprep": dict(model="bulbul:v4-flash", speaker="pooja_gu_customer", preprocessing=False),
}

# English words rendered in Gujarati script — sign a number/symbol was read in English
EN_LEAK = ["ઝીરો", "વન ", "ટુ ", "થ્રી", "ફોર ", "ફાઇવ", "ફાઈવ", "સિક્સ", "સેવન", "એઇટ", "એઈટ", "નાઇન", "નાઈન",
           "હન્ડ્રેડ", "થાઉઝન્ડ", "સ્લેશ", "ડેશ", "હાઇફન", "માઇનસ", "પોઇન્ટ", "પોઈન્ટ", "કોલોન", "પર્સન્ટ",
           "રૂપીઝ", "રુપીઝ", "ઇક્વલ", "પ્લસ", "હેશ", "એમ્પરસેન્ડ"]
# Hindi words in Gujarati script — sign of Hindi leakage
HI_LEAK = ["સાઢે", "ઢાઈ", "ડેઢ", "પૌને", "બજે", "તીસ ", "સૌ ", "હૈ", "નહીં હૈ", "કરના", "ઔર ", "પચ્ચીસ",
           "ઇક્કીસ", "છબ્બીસ", "સત્તાઈસ", "અઠ્ઠાઈસ", "ઉન્નીસ", "તારીખ કો"]


def dur(path):
    with wave.open(str(path)) as w:
        return w.getnframes() / w.getframerate()


def norm(s):
    return re.sub(r"[\s\.,!?।\-–—:;\"'“”‘’…]+", " ", s or "").strip()


def run_item(item, cfg):
    r = {"id": item["id"], "cat": item["cat"], "text": item["text"], "expect": item["expect"]}
    try:
        p = sv.tts(item["text"], rate=16000, **cfg)
        r["wav"] = str(p)
        r["dur"] = round(dur(p), 2)
        r["verbatim"] = sv.stt(p, mode="verbatim")["transcript"]
        r["transcribe"] = sv.stt(p, mode="transcribe")["transcript"]
    except Exception as e:
        r["error"] = f"{type(e).__name__}: {str(e)[:300]}"
        return r
    v = " " + norm(r["verbatim"]) + " "
    r["missing"] = [g for g in item["expect"] if not any(a in v for a in g.split("|"))]
    r["en_leak"] = [w.strip() for w in EN_LEAK if w in v]
    r["hi_leak"] = [w.strip() for w in HI_LEAK if w in v]
    r["latin"] = bool(re.search(r"[A-Za-z]{2,}", r["verbatim"] or ""))
    nchar = max(len(norm(item["text"])), 1)
    r["sec_per_char"] = round(r["dur"] / nchar, 3)
    return r


def main(names):
    for name in names:
        cfg = CONFIGS[name]
        with ThreadPoolExecutor(max_workers=4) as ex:
            res = list(ex.map(lambda it: run_item(it, cfg), ITEMS))
        out = sv.ROOT / "out" / f"results_{name}.jsonl"
        with open(out, "w", encoding="utf-8") as f:
            for r in res:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        errs = sum("error" in r for r in res)
        flagged = sum(bool(r.get("missing") or r.get("en_leak") or r.get("hi_leak")) for r in res)
        print(f"{name}: {len(res)} items, {errs} errors, {flagged} flagged -> {out.name}")


if __name__ == "__main__":
    main(sys.argv[1:] or ["v3", "v4_pooja_cust"])
