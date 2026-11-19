# Gujarati numbers in Sarvam TTS: findings and a fix

*Independent evaluation by a native Gujarati speaker, November 2026. Code, test set and audio: [repo link].*

## The problem
Bulbul reads **written** Gujarati numbers incorrectly, and that is exactly what voice agents say most: EMI amounts,
due dates, branch hours, interest rates. It happens the same way in **bulbul:v3 and v4-flash, with `enable_preprocessing`
on or off**. The voices are fine: written out as words, the same sentences are spoken correctly. So the fault is in
the text cleanup step.

| Written | Bulbul says | Should be |
|---|---|---|
| સવારે 9:30 વાગ્યે | નવ વાગ્યે ત્રીસ મિનિટ વાગ્યે (ungrammatical) | સાડા નવ વાગ્યે |
| લોન ₹1.5 લાખની | એક દશાંશ પાંચ લાખ **રૂપીઝ**ની | દોઢ લાખ રૂપિયાની |
| ₹99.50 | નવ્વાણું દશાંશ પાંચ રૂપીસ (paise lost) | નવ્વાણું રૂપિયા પચાસ પૈસા |
| 10-15 દિવસ | **એક શૂન્ય એક પાંચ** દિવસ | દસથી પંદર દિવસ |
| 1લા નંબરે | **એકલા** ("alone") નંબરે | પહેલા નંબરે |

The **Transliterate `spoken_form`** API is worse for times. It returns **wrong times** in 7 of 10 Gujarati cases, the same
way on every run: 9:30 → સવા દસ (10:15), 1:30 → સવા એક (1:15), 6:45 → સાડા છ (6:30). The docs' own example
(`9:30am`) gives "સવારે સવા દસ વાગ્યે એ.એમ." in Gujarati. Hindi gets 8 of 10 right.

**Pipeline effect:** `sarvam-105b-conversations`, acting as a Gujarati bank agent, wrote `9:30`, `10.75%` and `₹` in most
replies. Through Bulbul v4, the branch hours came out as "નવ વાગ્યે ત્રીસ મિનિટ વાગ્યે".

## The fix: `gujnorm`
A deterministic text-to-text step before TTS (pure Python, ~0.13 ms per sentence, 100 unit tests). It handles times
(સવા/સાડા/પોણા/દોઢ/અઢી, AM/PM → સવારે/સાંજે), money with paise, લાખ/કરોડ/Cr, %, ranges, ordinals, dates in Indian and
English order, years, phone/OTP/account numbers digit by digit, SI units, and Gujarati abbreviations. Alphanumeric IDs and
chemical formulas are left untouched.

## Results
**Through Sarvam's own voices** (108 stress sentences, Bulbul → Saaras `verbatim`):

| Voice | Expected Gujarati spoken: before → after | English-word slips |
|---|---|---|
| bulbul:v3 | 68 → **108 / 108** | 15 → 2 |
| v4-flash `pooja_gu_customer` | 73 → **106 / 108** | 15 → 2 |
| v4-flash `bhavik_gu_conversation` | 71 → **107 / 108** | 11 → 1 |

**On Sarvam's `tts-robustness-benchmark` (gu, 81 sentences):** gujnorm rewrites 35 sentences (Numerics 21/23,
STEM 11/22, Code-mixed 3/7), leaves names, URLs and romanized text alone, and leaves no stray digits.
The audio CER before/after is pending: my free credits ran out.

**Blind native-speaker listening test** (36 random pairs across 3 voices, clip order hidden, key kept out of the page):

| Pairs | Judged correct: Sarvam → gujnorm | Preferred gujnorm / Sarvam / same | Sign test |
|---|---|---|---|
| Sarvam misread the sentence (20) | **0 → 19** | **18 / 1 / 1** | p = 0.00008 |
| Both clips have the same words (16) | 12 → 7 | 4 / 9 / 3 | p = 0.27 (no real difference) |
| All 36 | 12 → 26 | 22 / 10 / 4 | p = 0.05 |

The listener preferred the second clip more often, and gujnorm's clip was usually first, so position bias worked against it.
On the identical-word pairs, two of gujnorm's "wrong" marks traced back to spelling (પિસ્તાળીસ/બેતાળીસ). gujnorm now uses
the spoken લ forms (પિસ્તાલીસ…) and joins postpositions (છવ્વીસમાં). This is v0.1.1. Its audio needs re-measuring once credits are available.

## Also observed
- Saaras with `language_code=gu-IN` sometimes returned Marathi or Devanagari text, or Latin script for short words, for Gujarati audio.
- The 105B model invents Gujarati literary facts (works credited to Narsinh Mehta, the meaning of "ભૂવો") while its script stays clean Gujarati.
- Hindi has the same decimal, range and ordinal problems, so the approach carries over to other languages.

## What I'd like to do next
Run the benchmark CER, extend gujnorm to Hindi and Marathi, and help put these rules into Bulbul's own gu-IN cleanup step and `spoken_form`.
