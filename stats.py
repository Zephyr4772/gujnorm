# -*- coding: utf-8 -*-
"""Count every finding from data already collected (no API calls). Writes out/stats.json."""
import json, re, collections, pathlib
from gujnorm import normalize
from sweep import norm

ROOT = pathlib.Path(__file__).parent
O = ROOT / "out"
VAR = {"સુડતાળીસ": "સુડતાલીસ", "મિલીગ્રામ": "મિલિગ્રામ", "બેતાળીસ": "બેતાલીસ", "પિસ્તાળીસ": "પિસ્તાલીસ",
       "વાગે": "વાગ્યે", "પચ્ચીસ": "પચીસ"}


def canon(s):
    s = " " + norm(normalize(s or "")) + " "
    for a, b in VAR.items():
        s = s.replace(a, b)
    return s


def missing(item_expect, heard):
    h = canon(heard)
    return [g for g in item_expect if not any(canon(a).strip() in h for a in g.split("|"))]


from testset import ITEMS
EXP = {it["id"]: it["expect"] for it in ITEMS}
rows = [json.loads(l) for l in open(O / "eval_rows.jsonl", encoding="utf-8")]

# ---------- defect classes, detected in what the voice actually said ----------
CLASSES = {
    "time: 'X વાગ્યે Y મિનિટ' instead of સવા/સાડા/પોણા/દોઢ/અઢી":
        lambda t, h: bool(re.search(r"\d:\d\d", t)) and "મિનિટ" in h and not re.search(r"\d:00", t),
    "decimal read as 'દશાંશ/પોઇન્ટ' instead of a fraction word":
        lambda t, h: bool(re.search(r"\d\.(5|25|75)(?!\d)", t)) and re.search(r"દશાંશ|પોઇન્ટ|પોઈન્ટ", h),
    "paise dropped (₹99.50 -> 99.5 rupees)":
        lambda t, h: bool(re.search(r"₹\s?\d+\.\d\d", t)) and "પૈસા" not in h,
    "₹ / Rs read as English 'rupees'":
        lambda t, h: bool(re.search(r"રૂપીસ|રૂપીઝ|રુપીસ|રુપીઝ", h)),
    "% read as English 'percent'":
        lambda t, h: "%" in t and bool(re.search(r"પર્સેન્ટ|પરસેન્ટ|પર્સન્ટ", h)),
    "range 10-15 read as digits / without 'થી'":
        lambda t, h: bool(re.search(r"(?<![A-Za-z\-\d])\d+\s?-\s?\d+(?![\d\-/])", t)) and "થી" not in h,
    "ordinal mangled (1લા->એકલા, 4થું->ચારથું, 3જી->ત્રણ જી)":
        lambda t, h: bool(re.search(r"\d(લ|જ|થ|મ)", t)) and re.search(r"એકલા|ચારથું|ત્રણ જી|ત્રણ જે|બેજા", h),
    "abbreviation not expanded (તા. નં. કિ.મી. ઇ.સ. રૂ.)":
        lambda t, h: (("તા." in t and "તારીખ" not in h) or ("કિ.મી." in t and "કિલોમીટર" not in h)
                      or ("ઇ.સ." in t and "ઈસવીસન" not in h) or ("રૂ." in t and "રૂપિયા" not in h)
                      or ("નં." in t and "નંબર" not in h)),
    "math/symbol read in English (plus, equals, slash)":
        lambda t, h: bool(re.search(r"\d\s*[+=/]\s*\d", t)) and re.search(r"પ્લસ|ઇક્વલ|બાય|સ્લેશ", h)
                     and not re.search(r"\+91", t),
    "year read digit by digit":
        lambda t, h: bool(re.search(r"\b1[1-9]\d\d\b", t)) and re.search(r"એક નવ ચાર સાત", h),
}

out = {"tts": {}, "classes": {}}
voices = ["v3", "v4_pooja_cust", "v4_bhavik"]
for v in voices:
    R = [r for r in rows if r["cfg"] == v]
    bad = []
    cats = collections.defaultdict(lambda: [0, 0])
    for r in R:
        m = missing(EXP[r["id"]], r["raw_heard"])
        cls = [c for c, f in CLASSES.items() if f(r["raw_text"], r["raw_heard"] or "")]
        defect = bool(m) or bool(cls)
        cats[r["cat"]][0] += 1
        cats[r["cat"]][1] += defect
        if defect:
            bad.append(r["id"])
        for c in cls:
            out["classes"].setdefault(c, {}).setdefault(v, []).append(r["id"])
    fixed_bad = [r["id"] for r in R if missing(EXP[r["id"]], r["fixed_heard"])
                 or any(f(r["raw_text"], r["fixed_heard"] or "") for c, f in CLASSES.items()
                        if not c.startswith("year"))]
    out["tts"][v] = {"n": len(R), "raw_defective": len(bad), "fixed_defective": len(fixed_bad),
                     "by_category": {k: {"n": a, "raw_defective": b} for k, (a, b) in sorted(cats.items())},
                     "raw_defective_ids": bad, "fixed_defective_ids": fixed_bad}

# sentences broken on ALL three voices (systematic, not voice noise)
sets = [set(out["tts"][v]["raw_defective_ids"]) for v in voices]
out["broken_on_all_3_voices"] = sorted(set.intersection(*sets))
out["broken_on_any_voice"] = sorted(set.union(*sets))

# ---------- enable_preprocessing ----------
p2 = json.load(open(O / "probe2.json", encoding="utf-8"))
same = {m: sum(norm(r[f"{m}_prep"]) == norm(r[f"{m}_noprep"]) for r in p2) for m in ("v3", "v4")}
# compare only the number words: strip known transcript-spelling noise and abbreviation tokens
_noise = lambda s: canon(s).replace("પરસેન્ટ", "પર્સેન્ટ").replace("પર્સન્ટ", "પર્સેન્ટ").replace("તમારો", "તમારું") \
    .replace("આવ્યા", "આવ્યો").replace(" વ્યાજ દર ", " વ્યાજદર ").replace(" તા ", " ").replace(" કી ", " ") \
    .replace(" નમ ", " ના ")
same_numbers = {m: sum(_noise(r[f"{m}_prep"]) == _noise(r[f"{m}_noprep"]) for r in p2) for m in ("v3", "v4")}
handnorm_ok = {m: sum(1 for r in p2 if norm(r[f"{m}_handnorm"]) != norm(r[f"{m}_prep"])) for m in ("v3", "v4")}
out["preprocessing"] = {"sentences": len(p2), "identical_transcript_on_vs_off": same,
                        "identical_number_reading_on_vs_off": same_numbers}

# ---------- spoken_form ----------
sf = json.load(open(O / "spoken_form_times.json", encoding="utf-8"))
RIGHT_GU = {"9:30": "સાડા નવ", "1:30": "દોઢ", "2:30": "અઢી", "4:45": "પોણા પાંચ", "3:15": "સવા ત્રણ",
            "10:00": "દસ", "6:45": "પોણા સાત", "11:30": "સાડા અગિયાર", "12:15": "સવા બાર|બાર ને પંદર",
            "7:05": "સાત ને પાંચ|સાત વાગીને પાંચ"}
RIGHT_HI = {"9:30": "साढ़े नौ", "1:30": "डेढ़|एक बजकर तीस|एक बजे तीस", "2:30": "ढाई|दो बजकर तीस", "4:45": "पौने पांच|पौने पाँच|चार बजकर पैंतालीस",
            "3:15": "सवा तीन|तीन बजकर पंद्रह", "10:00": "दस", "6:45": "पौने सात|छह बजकर पैंतालीस", "11:30": "साढ़े ग्यारह",
            "12:15": "सवा बारह|बारह बजकर पंद्रह", "7:05": "सात बजकर पाँच|सात बजकर पांच"}
import unicodedata
nfd = lambda s: unicodedata.normalize("NFD", s)   # Hindi ढ़ can be precomposed or ढ + nukta
gu_wrong = [t for t, v in sf.items() if not any(nfd(a) in nfd(v["gu"][0]) for a in RIGHT_GU[t].split("|"))]
hi_wrong = [t for t, v in sf.items() if not any(nfd(a) in nfd(v["hi"]) for a in RIGHT_HI[t].split("|"))]
gu_stable = sum(len(set(v["gu"])) == 1 for v in sf.values())
added_period = [t for t, v in sf.items() if re.search(r"સવારે|સાંજે|બપોરે|રાત્રે", v["gu"][0])]
out["spoken_form"] = {"times_tested": len(sf), "gu_wrong": gu_wrong, "hi_wrong": hi_wrong,
                      "gu_identical_across_3_runs": gu_stable, "gu_invented_time_of_day": added_period}

# ---------- STT: wrong script / language for Gujarati audio ----------
seen, stt = set(), collections.Counter()
examples = []
for name in ["results_v3.jsonl", "results_v4_pooja_cust.jsonl"]:
    for l in open(O / name, encoding="utf-8"):
        r = json.loads(l)
        if r.get("error") or not re.search(r"[\u0A80-\u0AFF]", r["text"]):
            continue
        for mode in ("verbatim", "transcribe"):
            h = r.get(mode) or ""
            key = (r["wav"], mode)
            if key in seen:
                continue
            seen.add(key)
            stt["total"] += 1
            if re.search(r"[\u0900-\u097F]", h):
                stt["devanagari"] += 1; examples.append((r["id"], mode, h[:60]))
            elif not re.search(r"[\u0A80-\u0AFF]", h) and re.search(r"[A-Za-z]{2}", h):
                stt["latin_only"] += 1; examples.append((r["id"], mode, h[:60]))
for r in rows:
    for side in ("raw", "fixed"):
        h, w = r[f"{side}_heard"] or "", r[f"{side}_wav"]
        if (w, "verbatim") in seen:
            continue
        seen.add((w, "verbatim"))
        stt["total"] += 1
        if re.search(r"[\u0900-\u097F]", h):
            stt["devanagari"] += 1; examples.append((r["id"], r["cfg"] + "/" + side, h[:60]))
        elif not re.search(r"[\u0A80-\u0AFF]", h) and re.search(r"[A-Za-z]{2}", h):
            stt["latin_only"] += 1; examples.append((r["id"], r["cfg"] + "/" + side, h[:60]))
out["stt_wrong_script"] = {**stt, "examples": examples}

# ---------- LLM ----------
L = json.load(open(O / "llm_probe.json", encoding="utf-8"))
ag = [r for r in L if r["kind"] == "agent" and "out" in r]
out["llm_agent"] = {"replies": len(ag),
                    "with_clock_time_digits": sum(bool(r["times"]) for r in ag),
                    "with_decimals": sum(bool(r["decimals"]) for r in ag),
                    "with_rupee_symbol": sum(r["rupee_sym"] > 0 for r in ag),
                    "with_any_tts_breaking_format": sum(bool(r["times"] or r["decimals"] or r["rupee_sym"] or r["ranges"]) for r in ag),
                    "devanagari_or_hindi_words": sum(bool(r["deva_chars"] or r["hindi_tells"]) for r in ag)}
gen = [r for r in L if r["kind"] == "general"]
out["llm_general"] = {"asked": len(gen), "answered": sum("out" in r for r in gen),
                      "errors_400": sum("error" in r for r in gen)}

json.dump(out, open(O / "stats.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ---------- print ----------
print("== TTS: number/symbol sentences Sarvam reads wrong (raw) -> with gujnorm")
for v in voices:
    t = out["tts"][v]
    print(f"  {v:14} {t['raw_defective']:3}/{t['n']} ({100*t['raw_defective']/t['n']:.0f}%)  ->  {t['fixed_defective']}/{t['n']}")
print(f"  broken on all 3 voices: {len(out['broken_on_all_3_voices'])}   on at least one: {len(out['broken_on_any_voice'])}")
print("  by category (v3 / v4_pooja / v4_bhavik):")
for c in out["tts"]["v3"]["by_category"]:
    cells = [f"{out['tts'][v]['by_category'][c]['raw_defective']}/{out['tts'][v]['by_category'][c]['n']}" for v in voices]
    print(f"    {c:8} " + "  ".join(cells))
print("\n== distinct defect classes (sentences hit: v3 / v4_pooja / v4_bhavik)")
for c, d in out["classes"].items():
    print(f"  {len(d.get('v3', [])):2} / {len(d.get('v4_pooja_cust', [])):2} / {len(d.get('v4_bhavik', [])):2}   {c}")
print(f"\n== enable_preprocessing on vs off ({len(p2)} sentences per model): identical transcript {same}, "
      f"identical number reading {same_numbers}")
s = out["spoken_form"]
print(f"== spoken_form times: Gujarati wrong {len(s['gu_wrong'])}/{s['times_tested']} {s['gu_wrong']} | Hindi wrong {len(s['hi_wrong'])}/{s['times_tested']} {s['hi_wrong']}")
print(f"   identical on 3 runs: {s['gu_identical_across_3_runs']}/{s['times_tested']}   invented સવારે/સાંજે: {s['gu_invented_time_of_day']}")
st = out["stt_wrong_script"]
print(f"== STT (gu-IN set) returned wrong script: Devanagari {st['devanagari']}, Latin-only {st['latin_only']} of {st['total']} transcripts")
for e in st["examples"][:12]:
    print("     ", e)
print(f"== LLM agent replies: {out['llm_agent']}")
print(f"== LLM general: {out['llm_general']}")
