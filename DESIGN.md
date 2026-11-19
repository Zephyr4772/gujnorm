# gujnorm: Gujarati text normalizer for TTS

## Problem (see FINDINGS.md)
Bulbul's text cleanup step (v3 and v4 Flash alike, whatever `enable_preprocessing` is set to) misreads Gujarati times, fractions,
money, ranges, ordinals, ₹ and abbreviations. When the same text is written out in words, it is spoken correctly.
So the fix is a text-to-text layer that runs **before** TTS. No model change is needed.

## Design
`gujnorm.normalize(text) -> str` turns written Gujarati into fully spoken Gujarati words. It is pure Python, deterministic,
has no dependencies, and runs in under 1 ms per sentence, so it is safe on the real-time voice-agent path.

It is built as ordered regex passes. Each pass outputs words only, with no digits, so later passes never re-match earlier output:

| # | Pass | Example |
|---|---|---|
| 1 | Gujarati digits → ASCII | ૯:૩૦ → 9:30 |
| 2 | Abbreviations | તા. → તારીખ, નં. → નંબર, કિ.મી. → કિલોમીટર, ઇ.સ. → ઈસવીસન |
| 3 | Dates | 05/12/2026 → પાંચ ડિસેમ્બર બે હજાર છવ્વીસ; 15 ઓગસ્ટ 1947 → … ઓગણીસો સુડતાળીસ |
| 4 | Times | 9:30 → સાડા નવ, 1:30 → દોઢ, 4:45 → પોણા પાંચ, 6 PM → સાંજે છ વાગ્યે; adds વાગ્યે / વાગ્યાથી / વાગ્યા સુધી |
| 5 | Phone / OTP / IDs | 9876543210 → નવ આઠ સાત … (digit by digit) |
| 6 | Money | ₹1.5 લાખની → દોઢ લાખ રૂપિયાની; ₹99.50 → નવ્વાણું રૂપિયા પચાસ પૈસા |
| 7 | Percent | 8.5% → સાડા આઠ ટકા |
| 8 | Ranges | 10-15 → દસથી પંદર |
| 9 | Ordinals | 1લા → પહેલા, 4થું → ચોથું, 21મી → એકવીસમી |
| 10 | Units | km/h, kg, mg, °C |
| 11 | Math | + → વત્તા, = → બરાબર |
| 12 | Decimals | 2.5 → અઢી, 1.25 → સવા, 0.75 → પોણો, 3.2 → ત્રણ દશાંશ બે |
| 13 | Integers | Indian grouping: લાખ / કરોડ; 1100–1999 read the year way (ઓગણીસો પંચ્યાસી) |

## Integration
- Call it on the text right before `client.text_to_speech.convert(...)`, or use `gujnorm.sarvam.speak()`.
- Voice agents: one line in the LiveKit/Pipecat TTS step (`text = normalize(text)`).
- Upstream: the same rules could live in Bulbul's own gu-IN cleanup step and in `spoken_form`.

## Evaluation
For each of the 177 stress sentences: TTS(raw) and TTS(normalize(raw)), then Saaras `verbatim`, then check for the expected spoken words and count English or Hindi words that slipped in.
Next: the Gujarati split of Sarvam's `tts-robustness-benchmark`.

## Known limits
- Alphanumeric IDs (PAN, vehicle numbers) are left alone. Bulbul reads them letter by letter in English, which is how people say them.
- `d/m/yyyy` is assumed to be the Indian day/month order.
- The number-word spellings need a native speaker's check (e.g. સુડતાળીસ vs સુડતાલીસ).
