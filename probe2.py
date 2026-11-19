# -*- coding: utf-8 -*-
"""Phase 3 probes: (a) preprocessing off, (b) Hindi parallel, (c) spoken_form API, (d) hand-normalized text."""
import json, sys
import sv

FAIL = [  # (id, gujarati raw, hand-normalized gujarati, hindi parallel)
 ("time930", "સવારે 9:30 વાગ્યે આવજો.", "સવારે સાડા નવ વાગ્યે આવજો.", "सुबह 9:30 बजे आना."),
 ("time130", "બપોરે 1:30 વાગ્યે જમવાનું છે.", "બપોરે દોઢ વાગ્યે જમવાનું છે.", "दोपहर 1:30 बजे खाना है."),
 ("time245", "4:45 વાગ્યે બસ આવશે.", "પોણા પાંચ વાગ્યે બસ આવશે.", "4:45 बजे बस आएगी."),
 ("lakh15", "લોન ₹1.5 લાખની છે.", "લોન દોઢ લાખ રૂપિયાની છે.", "लोन ₹1.5 लाख का है."),
 ("kg25", "મને 2.5 કિલો ચોખા આપો.", "મને અઢી કિલો ચોખા આપો.", "मुझे 2.5 किलो चावल दो."),
 ("paise", "તમારું બેલેન્સ ₹99.50 છે.", "તમારું બેલેન્સ નવ્વાણું રૂપિયા પચાસ પૈસા છે.", "आपका बैलेंस ₹99.50 है."),
 ("range", "10-15 દિવસ લાગશે.", "દસથી પંદર દિવસ લાગશે.", "10-15 दिन लगेंगे."),
 ("year", "આઝાદી 15 ઓગસ્ટ 1947 એ મળી.", "આઝાદી પંદર ઓગસ્ટ ઓગણીસો સુડતાલીસે મળી.", "आज़ादी 15 अगस्त 1947 को मिली."),
 ("ord1", "તે 1લા નંબરે આવ્યો.", "તે પહેલા નંબરે આવ્યો.", "वह 1ले नंबर पर आया."),
 ("ord4", "4થું ધોરણ પાસ કર્યું.", "ચોથું ધોરણ પાસ કર્યું.", "4थी कक्षा पास की."),
 ("pct", "વ્યાજ દર 8.5% છે.", "વ્યાજ દર સાડા આઠ ટકા છે.", "ब्याज दर 8.5% है."),
 ("tarikh", "તા. 12/05/2026 ના રોજ મળીશું.", "તારીખ બાર મે બે હજાર છવ્વીસના રોજ મળીશું.", "दि. 12/05/2026 को मिलेंगे."),
 ("km", "અમદાવાદથી વડોદરા 110 કિ.મી. છે.", "અમદાવાદથી વડોદરા એકસો દસ કિલોમીટર છે.", "अहमदाबाद से वडोदरा 110 कि.मी. है."),
 ("no", "ફોર્મ નં. 16 ભરો.", "ફોર્મ નંબર સોળ ભરો.", "फॉर्म नं. 16 भरें."),
 ("emi", "તમારો આગલો હપ્તો ₹4,350 તા. 05/12/2026 ના રોજ ભરવાનો છે.",
         "તમારો આગલો હપ્તો ચાર હજાર ત્રણસો પચાસ રૂપિયા તારીખ પાંચ ડિસેમ્બર બે હજાર છવ્વીસના રોજ ભરવાનો છે.",
         "आपकी अगली किश्त ₹4,350 दि. 05/12/2026 को भरनी है."),
]

def run(text, lang="gu-IN", **cfg):
    p = sv.tts_lang(text, lang=lang, **cfg)
    return sv.stt(p, mode="verbatim", lang=lang)["transcript"]

rows = []
for fid, gu, gu_norm, hi in FAIL:
    r = {"id": fid, "gu": gu}
    for name, cfg in [("v3", dict(model="bulbul:v3")), ("v4", dict(model="bulbul:v4-flash", speaker="pooja_gu_customer"))]:
        r[f"{name}_prep"] = run(gu, preprocessing=True, **cfg)
        r[f"{name}_noprep"] = run(gu, preprocessing=False, **cfg)
        r[f"{name}_handnorm"] = run(gu_norm, preprocessing=True, **cfg)
    r["hi_v3"] = run(hi, lang="hi-IN", model="bulbul:v3", preprocessing=True)
    r["spoken_form_api"] = sv.spoken_form(gu)
    rows.append(r)
    print(json.dumps(r, ensure_ascii=False, indent=1))
json.dump(rows, open(sv.ROOT / "out" / "probe2.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
