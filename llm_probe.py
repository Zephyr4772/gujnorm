# -*- coding: utf-8 -*-
"""LLM side probe: Gujarati purity + how the agent model writes numbers (which TTS then reads)."""
import json, re
from concurrent.futures import ThreadPoolExecutor
import sv

SYS_AGENT = ("તમે HDFC બૅંકના ગુજરાતી ગ્રાહક સેવા વોઇસ એજન્ટ છો. ફક્ત ગુજરાતીમાં, ટૂંકા વાક્યોમાં જવાબ આપો. "
             "ગ્રાહકનો આગલો EMI ₹4,350 છે, ડ્યૂ તારીખ 05/12/2026, બાકી લોન ₹2,37,450, વ્યાજ દર 10.75%, "
             "શાખા સમય સવારે 9:30 થી સાંજે 4:30.")
PROMPTS = [
 "મારો આગલો હપ્તો કેટલો છે અને ક્યારે ભરવાનો છે?",
 "મારી બાકી લોન કેટલી છે?",
 "વ્યાજ દર કેટલો છે?",
 "બૅંક કેટલા વાગ્યે ખુલે છે અને બંધ થાય છે?",
 "જો હું હપ્તો 10 દિવસ મોડો ભરું તો શું થશે?",
 "મારે દોઢ લાખનું ટોપ-અપ જોઈએ છે, શક્ય છે?",
 "મને મારા EMI ની વિગતો સમજાવો.",
 "હું હપ્તો UPI થી ભરી શકું?",
 "તમે મને હિન્દીમાં નહીં, ગુજરાતીમાં જ જવાબ આપજો. મારું બેલેન્સ કેટલું છે?",
 "kem cho, maro hapto ketlo che?",
 "Mera EMI kitna hai? ગુજરાતીમાં કહો.",
 "મારે લોન વહેલી પૂરી કરવી છે, શું કરવું?",
]
GENERAL = [
 "ગુજરાતી સાહિત્યના ત્રણ મોટા લેખકો વિશે ટૂંકમાં લખો.",
 "ઉત્તરાયણનો તહેવાર કેવી રીતે ઉજવાય છે? 4 વાક્યમાં કહો.",
 "ઢોકળા બનાવવાની રીત 5 પગલામાં લખો.",
 "‘ઘરનો ભૂવો ને ઘરનો જાગરિયો’ કહેવતનો અર્થ શું છે?",
 "ગુજરાતી વ્યાકરણમાં ‘ળ’ અને ‘લ’ નો તફાવત ઉદાહરણ સાથે સમજાવો.",
 "એક સાદો ઇમેઇલ ગુજરાતીમાં લખો: રજા માટે અરજી.",
 "નીચેનું વાક્ય સુધારો: 'મેં કાલે બજાર ગયો હતો.'",
 "‘હું જમી ને આવું છું’ અને ‘હું જમીને આવું છું’ માં શું ફરક છે?",
]
# Hindi-only words/forms in Gujarati script (not normal Gujarati)
HINDI_TELLS = ["હૈ", "હૈં", "આપકા", "આપકી", "આપકો", "કીજિયે", "કીજિએ", "કરેં", "કૃપયા", "મેરા", "મેરી", "તુમ્હારા",
               "ક્યા ", "નહીં હૈ", "લેકિન", "ઔર ", "જાયેગા", "જાએગા", "હોગા", "કિયા", "દીજિયે", "બતાઇએ", "સકતે"]


def analyze(txt):
    deva = len(re.findall(r"[ऀ-ॿ]", txt))
    guj = len(re.findall(r"[઀-૿]", txt))
    latin = len(re.findall(r"[A-Za-z]", txt))
    return {"deva_chars": deva, "guj_chars": guj, "latin_chars": latin,
            "hindi_tells": [w.strip() for w in HINDI_TELLS if w in txt],
            "times": re.findall(r"\d{1,2}:\d{2}", txt),
            "decimals": re.findall(r"\d+\.\d+", txt),
            "rupee_sym": txt.count("₹"),
            "ranges": re.findall(r"\d+\s*-\s*\d+", txt)}


def one(job):
    kind, sysmsg, q, model = job
    msgs = ([{"role": "system", "content": sysmsg}] if sysmsg else []) + [{"role": "user", "content": q}]
    kw = {"temperature": 0.6, "max_tokens": 1500}
    if model == "sarvam-105b":
        kw["reasoning_effort"] = "none"
    try:
        out = sv.chat(msgs, model=model, **kw)
    except Exception as e:
        return {"kind": kind, "model": model, "q": q, "error": str(e)[:200]}
    return {"kind": kind, "model": model, "q": q, "out": out, **analyze(out or "")}


jobs = [("agent", SYS_AGENT, q, "sarvam-105b-conversations") for q in PROMPTS]
jobs += [("general", None, q, m) for q in GENERAL for m in ("sarvam-105b-conversations", "sarvam-105b")]
with ThreadPoolExecutor(4) as ex:
    res = list(ex.map(one, jobs))
json.dump(res, open(sv.ROOT / "out" / "llm_probe.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for r in res:
    if "error" in r:
        print("ERR", r["q"], r["error"]); continue
    flag = r["deva_chars"] or r["hindi_tells"] or r["times"] or r["decimals"] or r["ranges"] or r["rupee_sym"]
    print(f"\n[{r['kind']}/{r['model']}] Q: {r['q']}\nA: {r['out']}\n  deva={r['deva_chars']} latin={r['latin_chars']} hi={r['hindi_tells']} "
          f"times={r['times']} dec={r['decimals']} ranges={r['ranges']} ₹={r['rupee_sym']}{'  <-- FLAG' if flag else ''}")
