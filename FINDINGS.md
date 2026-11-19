# Gujarati in Sarvam's stack: findings (19 Nov 2026)

Tested: Bulbul v3 and v4 Flash (TTS), Saaras v4 (STT), Transliterate `spoken_form`, sarvam-105b-conversations.
Method: 177 Gujarati stress sentences → TTS → Saaras `verbatim` (shows what was actually spoken), plus Hindi parallels,
`enable_preprocessing` on/off, and hand-normalized controls. All raw results are in `out/`; audio to check by ear is in `out/listen/`.

## Headline

**Gujarati text normalization is broken in two separate Sarvam components, and their own voice-agent LLM writes exactly the formats that trigger it.**
The voice itself is fine: when the same sentence is written out in words by hand, both Bulbul v3 and v4 speak it correctly.
So the bug sits in the text cleanup step, which can be fixed without touching the model.

## Finding 1: Bulbul reads Gujarati numbers wrong (v3 and v4 alike, with `enable_preprocessing` on or off)

| Input | What Bulbul says | Correct Gujarati |
|---|---|---|
| `9:30 વાગ્યે` | નવ વાગ્યે ત્રીસ મિનિટ વાગ્યે (ungrammatical, "o'clock" said twice) | સાડા નવ વાગ્યે |
| `1:30`, `2:30`, `3:15`, `4:45` | એક/બે/ત્રણ/ચાર વાગ્યે … મિનિટ વાગ્યે | દોઢ / અઢી / સવા ત્રણ / પોણા પાંચ |
| `₹1.5 લાખ` | એક દશાંશ પાંચ લાખ રૂપીઝ | દોઢ લાખ રૂપિયા |
| `2.5 કિલો` | બે **પોઇન્ટ** પાંચ કિલો | અઢી કિલો |
| `₹99.50` | નવ્વાણું દશાંશ પાંચ રૂપીસ (paise lost) | નવ્વાણું રૂપિયા પચાસ પૈસા |
| `10-15 દિવસ` | **એક શૂન્ય એક પાંચ** દિવસ ("one zero one five") | દસથી પંદર દિવસ |
| `1લા નંબરે` | **એકલા** નંબરે ("alone") | પહેલા નંબરે |
| `4થું`, `3જી` | ચારથું, ત્રણ જી | ચોથું, ત્રીજી |
| `₹500` | પાંચસો **રૂપીસ** (English "rupees"; Hindi correctly says रुपये) | પાંચસો રૂપિયા |
| `8.5%` | આઠ દશાંશ પાંચ **પર્સેન્ટ** | સાડા આઠ ટકા |
| `તા.`, `કિ.મી.`, `તા.ક.`, `ઇ.સ.` | not expanded (spoken as "તા", "કિમી"…) | તારીખ, કિલોમીટર, તાજા કલમ, ઈસવીસન |
| `15 ઓગસ્ટ 1947 એ` | એક નવ ચાર સાત (digit by digit; other years are fine) | ઓગણીસો સુડતાલીસ |

- Identical in v3 and v4 Flash, so it isn't the voice.
- `enable_preprocessing=false` gives **the same output**, so the documented flag has no visible effect for gu-IN.
- Hindi gets ₹, years and time grammar right ("नौ बजकर तीस मिनट"). Gujarati fails on all three.
- Ranges, decimals and ordinals also fail in Hindi, so those are cross-language bugs.

## Finding 2: The Transliterate `spoken_form` API gives wrong times in Gujarati (every run)

| Input (gu-IN) | spoken_form output | Means | Hindi output |
|---|---|---|---|
| 9:30 | સવા દસ | **10:15** | साढ़े नौ ✓ |
| 1:30 | સવા એક | **1:15** | ✓ |
| 2:30 | બસ્ઠી | not a real word | ✓ |
| 4:45 | સાડા ચાર | **4:30** | साढ़े चार ✗ |
| 6:45 | સાડા છ | **6:30** | साढ़े छह ✗ |
| 11:30 | સવા અગિયાર | **11:15** | ✓ |
| 7:05 | સાંજે સાત | minutes dropped, "evening" added | ✓ |
| `9:30am` (the docs' own example) | સવારે સવા દસ વાગ્યે એ.એમ. | **10:15**, "AM" said twice | साढे नौ बजे ✓ |

- **7 of 10 Gujarati times are wrong**, against 2 of 10 in Hindi. The output was the same in all 3 runs, so it isn't random sampling.
- It also adds morning/evening words that weren't in the input, and reads dates as "ફોરવર્ડ સ્લેશ".

## Finding 3: The voice-agent pipeline multiplies the problem

`sarvam-105b-conversations` (the LLM behind Samvaad) writes Gujarati replies with `9:30`, `10.75%` and `₹` in 8–11 of 12 banking-agent turns.
Through Bulbul v4 (`pooja_gu_customer`), "branch opens at 9:30" becomes
*"સવારે નવ વાગ્યે ત્રીસ મિનિટ વાગ્યે ખુલે છે"* and "10.75%" becomes *"દસ દશાંશ સાત પાંચ પર્સેન્ટ"*.
Bulbul v3 was retired on Voice Agents on 10 Nov 2026, so every Gujarati agent now runs on v4 Flash, which has 3 Gujarati voices.

## Smaller findings (secondary)
- **STT language slips** (need a listen to tell whether TTS or STT is at fault): Saaras with `language_code=gu-IN` returned Marathi (`मोटेरामध्ये आहे`), Devanagari (`पहलू काम पता हो`), or Latin script (`Na na na`, `Ha.`) for Gujarati audio.
- **The LLM makes up Gujarati cultural facts**: it credits Narsinh Mehta with works he didn't write, gives K. M. Munshi wrong works and a wrong name, and explains ભૂવો in a proverb as "a mud fort" (it means a folk exorcist). The Gujarati script itself is clean, with no Hindi leaking in.
- `sarvam-105b` with `reasoning_effort="none"` returns 400 through the SDK, although the SDK type allows `"none"`.
- Docs: the HF card says 105B covers 22 languages, the API docs say 11. Samvaad lists Assamese, but no Bulbul model supports it. Malayalam and Odia agents have no v4 voices after v3 was retired.

## Fix built: `gujnorm` (see README.md, DESIGN.md)
Native-speaker check: the hand-fixed clips sound correct and the raw ones sound wrong (confirmed by ear).

| Voice | Expected Gujarati spoken: before → after (108 sentences) | English-word slips |
|---|---|---|
| bulbul:v3 | 68 → **108** | 15 → 2 |
| v4-flash pooja_gu_customer | 73 → **106** | 15 → 2 |
| v4-flash bhavik_gu_conversation | 71 → **107** | 11 → 1 |

Scoring note: Saaras `verbatim` sometimes writes numbers back as digits. The digits in the transcript are spelled out
the same way for both raw and fixed audio before checking, so the score checks the number's value either way.
`pooja_gu_conversational` couldn't be scored because the account ran out of credits (HTTP 402).

### Blind native-speaker listening test (19 Nov 2026)
36 random before/after pairs (12 per voice), with clip order hidden. Sarvam misread 20 of the pairs: Sarvam was judged correct 0/20,
gujnorm 19/20, and gujnorm was preferred 18 to 1 (p = 0.00008). The 16 pairs with identical words showed no significant difference (p = 0.27).
Listener feedback that went back into gujnorm v0.1.1: use the spoken લ forms for 41–48 (પિસ્તાલીસ, not પિસ્તાળીસ), and join
postpositions to the number word (છવ્વીસમાં). The test sentence "5મો દિવસ રજા છે" was unnatural and is now "5મા દિવસે રજા છે".
The listener didn't recognise "તા.ક. → તાજા કલમ" (an old letter-writing "P.S."), so it is not counted as a finding.

## Original fix plan
An open-source **Gujarati text normalizer** to run before TTS:
- times using સવા / સાડા / પોણા / દોઢ / અઢી
- decimals and money with paise
- ranges ("થી")
- ordinals
- ₹ → રૂપિયા, % → ટકા
- Gujarati abbreviations
- IDs read digit by digit

Measured before and after on this test set **and on Sarvam's own `tts-robustness-benchmark` (81 Gujarati samples)**, with a LiveKit/Pipecat add-on so it fits their reference agent.

## Needs a native-speaker check (`out/listen/`)
For each pair, `A_raw` is what Sarvam produces and `B_handfixed` is the same sentence written out in words. Confirm that A sounds wrong and B sounds right, and note anything that sounds Hindi-accented.
Clips 12 and 13: decide whether the TTS audio sounds Gujarati (if so, it's an STT bug) or not (a TTS bug).
