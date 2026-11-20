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

🔊 **[Listen to 10 before/after clips →](samples/README.md)** (Sarvam's v4 Gujarati agent voice)

🤗 **[Try it in your browser](https://huggingface.co/spaces/sinhal/gujnorm)** ·
**[Dataset: Gujarati TTS number reading](https://huggingface.co/datasets/sinhal/gujarati-tts-number-reading)**
(177 sentences, all results, listening test) ·
**[Dataset: IndicTrans2 number fidelity](https://huggingface.co/datasets/sinhal/indictrans2-number-fidelity)**
(related: Indian amounts split by IndicTrans2's pre-processing, fix in
[VarunGumma/IndicTransToolkit#32](https://github.com/VarunGumma/IndicTransToolkit/pull/32))

## Results (Bulbul TTS → Saaras STT, 108 stress sentences that gujnorm changes)

| Voice | Sentences misread: before → after (of 108) |
|---|---|
| bulbul:v3 (default) | 59 → **0** |
| bulbul:v4-flash `pooja_gu_customer` | 55 → **2** |
| bulbul:v4-flash `bhavik_gu_conversation` | 56 → **1** |

Misread means an expected spoken word is missing, or a number or symbol is said in English ("rupees", "percent").
53 sentences fail on all three voices. Every ₹ (20/20), every clock time that isn't a whole hour (9/9) and every
x.5/x.25/x.75 (13/13) is misread on every voice. Counts: `stats.py` → `results/stats.json`.

- **Blind native-speaker A/B test** (36 pairs): where Sarvam misread the sentence, the listener judged Sarvam correct
  0/20 and gujnorm 19/20, and preferred gujnorm 18 to 1 (sign test p = 0.00008). Where both clips had the same words,
  there was no significant difference (p = 0.27).
- On Sarvam's `tts-robustness-benchmark` (gu): it rewrites 35/81 sentences (Numerics 21/23) and leaves no stray digits.
- 100 unit tests pass.
- The audio numbers above were measured with v0.1.0. v0.1.1 adds the native-speaker spelling fixes (પિસ્તાલીસ…) and joined
  postpositions (છવ્વીસમાં), and still needs an audio re-run.
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
Gujarati digits · Indian grouping (લાખ/કરોડ) · years (ઓગણીસો સુડતાલીસ) · dates (dd/mm/yyyy, ISO, "15 ઓગસ્ટ 1947") ·
clock times with સવા/સાડા/પોણા/દોઢ/અઢી, AM/PM → સવારે/બપોરે/સાંજે/રાત્રે, and વાગ્યે/વાગ્યાથી/વાગ્યા સુધી ·
₹ / Rs. / રૂ. / INR / /- / $ with paise · % → ટકા · ranges → થી · ordinals (પહેલો, બીજી, ચોથું, છઠ્ઠો, એકવીસમી) ·
phone / OTP / PIN / policy numbers read digit by digit · units · + = · abbreviations (તા., નં., કિ.મી., ડૉ., ઇ.સ., તા.ક.).
Alphanumeric IDs (GJ01AB1234, IFSC) are left untouched on purpose.

## Repo layout
- `gujnorm/`: the normalizer (`numbers.py` holds the word tables, `rules.py` the passes, `sarvam.py` the SDK helpers)
- `tests/`: unit tests (`pytest`)
- `testset.py`: 177 Gujarati stress sentences · `sweep.py` / `eval_fix.py`: TTS→STT harness and before/after evaluation
- `samples/`: before/after MP3s with a table of what was written, said and sent
- `FINDINGS.md`: the bugs found in Sarvam's stack · `DESIGN.md`: how the fix works
