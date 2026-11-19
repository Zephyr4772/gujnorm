# gujnorm: making Sarvam's Gujarati voices read numbers correctly

Sarvam's Bulbul voices read **written** Gujarati numbers wrong: times, fractions, money, ranges, ordinals, ₹ and abbreviations.
The voices pronounce Gujarati **words** perfectly. `gujnorm` turns the written forms into Gujarati words before TTS.

| Written | Bulbul today | With gujnorm |
|---|---|---|
| સવારે 9:30 વાગ્યે | નવ વાગ્યે ત્રીસ મિનિટ વાગ્યે | સાડા નવ વાગ્યે |
| લોન ₹1.5 લાખની | એક દશાંશ પાંચ લાખ રૂપીઝની | દોઢ લાખ રૂપિયાની |
| ₹99.50 | નવ્વાણું દશાંશ પાંચ રૂપીસ | નવ્વાણું રૂપિયા પચાસ પૈસા |
| 10-15 દિવસ | એક શૂન્ય એક પાંચ દિવસ | દસથી પંદર દિવસ |
| 1લા નંબરે | એકલા ("alone") નંબરે | પહેલા નંબરે |
| 8.5% | આઠ દશાંશ પાંચ પર્સેન્ટ | સાડા આઠ ટકા |
| તા. 05/12/2026 | તા પાંચ ડિસેમ્બર… | તારીખ પાંચ ડિસેમ્બર બે હજાર છવ્વીસ |

## Results (Bulbul TTS → Saaras STT, 108 stress sentences that gujnorm changes)

| Voice | Expected Gujarati spoken: before → after | English words in the speech: before → after |
|---|---|---|
| bulbul:v3 (default) | 68 → **108 / 108** | 15 → 2 |
| bulbul:v4-flash `pooja_gu_customer` | 73 → **106 / 108** | 15 → 2 |
| bulbul:v4-flash `bhavik_gu_conversation` | 71 → **107 / 108** | 11 → 1 |

- Native-speaker check: before/after clips confirmed by ear (`out/listen/`).
- 80 unit tests pass.
- About 0.13 ms per sentence, no dependencies, thread-safe, and it doesn't change already-normalized text.
- The few remaining misses are on the voice side ("પોણો" heard as "પૂર્ણો"/"કોણ" on v4), not in the text cleanup.

## Use

```python
from gujnorm import normalize
normalize("તમારો હપ્તો ₹4,350 તા. 05/12/2026 ના રોજ, શાખા 9:30 થી 4:30")
# 'તમારો હપ્તો ચાર હજાર ત્રણસો પચાસ રૂપિયા તારીખ પાંચ ડિસેમ્બર બે હજાર છવ્વીસ ના રોજ, શાખા સાડા નવ વાગ્યાથી સાડા ચાર વાગ્યે'
```

With the Sarvam SDK, or inside a voice agent:

```python
from gujnorm.sarvam import speak, wrap_tts_text
audios = speak(client, llm_reply, model="bulbul:v4-flash", speaker="pooja_gu_customer")
```

## What it covers
Gujarati digits · Indian grouping (લાખ/કરોડ) · years (ઓગણીસો સુડતાળીસ) · dates (dd/mm/yyyy, ISO, "15 ઓગસ્ટ 1947") ·
clock times with સવા/સાડા/પોણા/દોઢ/અઢી, AM/PM → સવારે/બપોરે/સાંજે/રાત્રે, and વાગ્યે/વાગ્યાથી/વાગ્યા સુધી ·
₹ / Rs. / રૂ. / INR / /- / $ with paise · % → ટકા · ranges → થી · ordinals (પહેલો, બીજી, ચોથું, છઠ્ઠો, એકવીસમી) ·
phone / OTP / PIN / policy numbers read digit by digit · units · + = · abbreviations (તા., નં., કિ.મી., ડૉ., ઇ.સ., તા.ક.).
Alphanumeric IDs (GJ01AB1234, IFSC) are left untouched on purpose.

## Repo layout
- `gujnorm/`: the normalizer (`numbers.py` holds the word tables, `rules.py` the passes, `sarvam.py` the SDK helpers)
- `tests/`: unit tests (`pytest`)
- `testset.py`: 177 Gujarati stress sentences · `sweep.py` / `eval_fix.py`: TTS→STT harness and before/after evaluation
- `FINDINGS.md`: the bugs found in Sarvam's stack · `DESIGN.md`: how the fix works
