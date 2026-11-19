# -*- coding: utf-8 -*-
"""Build a blind A/B listening test from cached audio (no API calls).
Writes out/abtest/index.html + audio/ + key.json (the key is NOT in the page)."""
import json, random, shutil, pathlib, html

ROOT = pathlib.Path(__file__).parent
OUT = ROOT / "out" / "abtest"
N_PER_VOICE = 12
VOICES = ["v3", "v4_pooja_cust", "v4_bhavik"]

rows = [json.loads(l) for l in open(ROOT / "out" / "eval_rows.jsonl", encoding="utf-8")]
rows = [r for r in rows if r["cfg"] in VOICES and r.get("raw_wav") and r.get("fixed_wav")
        and pathlib.Path(r["raw_wav"]).exists() and pathlib.Path(r["fixed_wav"]).exists()]

rng = random.Random(20261119)
trials = []
for v in VOICES:
    pool = [r for r in rows if r["cfg"] == v]
    rng.shuffle(pool)
    seen_ids, pick = set(), []
    for r in pool:                       # avoid repeating a sentence within a voice
        if r["id"] not in seen_ids:
            pick.append(r); seen_ids.add(r["id"])
        if len(pick) == N_PER_VOICE:
            break
    trials += pick
rng.shuffle(trials)

if OUT.exists():
    shutil.rmtree(OUT)
(OUT / "audio").mkdir(parents=True)
key, page_trials = {}, []
for i, r in enumerate(trials, 1):
    tid = f"t{i:02d}"
    fixed_first = rng.random() < 0.5
    a, b = (r["fixed_wav"], r["raw_wav"]) if fixed_first else (r["raw_wav"], r["fixed_wav"])
    shutil.copy(a, OUT / "audio" / f"{tid}_1.wav")
    shutil.copy(b, OUT / "audio" / f"{tid}_2.wav")
    key[tid] = {"fixed_is": 1 if fixed_first else 2, "voice": r["cfg"], "item": r["id"], "cat": r["cat"]}
    page_trials.append({"id": tid, "text": r["raw_text"]})
json.dump(key, open(OUT / "key.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

TEMPLATE = (ROOT / "abtest_template.html").read_text(encoding="utf-8")
(OUT / "index.html").write_text(TEMPLATE.replace("__TRIALS__", json.dumps(page_trials, ensure_ascii=False)),
                                encoding="utf-8")
print(f"{len(trials)} trials -> {OUT / 'index.html'}")
