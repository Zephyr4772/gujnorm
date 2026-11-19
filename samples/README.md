# Listen: Sarvam Bulbul before and after gujnorm

Voice: **bulbul:v4-flash · `pooja_gu_customer`**, the Gujarati voice Sarvam's voice agents now run on (Bulbul v3 was retired on Voice Agents on 10 Nov 2026).
**before** = Sarvam's TTS given the written text. **after** = the same voice given `gujnorm.normalize(text)`.
"Sarvam says" is Saaras v4's `verbatim` transcript of the before clip. A native Gujarati speaker checked these by ear.
Click a file, then **View raw**, to play it in the browser.

| # | Written text | Sarvam says (before) | gujnorm sends (after) | Listen |
|---|---|---|---|---|
| 1 | સવારે 9:30 વાગ્યે આવજો. | સવારે નવ વાગ્યે ત્રીસ મિનિટ વાગ્યે આવજો *(ungrammatical)* | સવારે સાડા નવ વાગ્યે આવજો. | [before](01_time_9-30_before.mp3) · [after](01_time_9-30_after.mp3) |
| 2 | લોન ₹1.5 લાખની છે. | લોન એક દશાંશ પાંચ લાખ **રૂપીઝ**ની છે | લોન દોઢ લાખ રૂપિયાની છે. | [before](02_loan_1.5_lakh_before.mp3) · [after](02_loan_1.5_lakh_after.mp3) |
| 3 | તમારું બેલેન્સ ₹99.50 છે. | નવ્વાણું દશાંશ પાંચ રૂપીસ *(paise lost)* | નવ્વાણું રૂપિયા પચાસ પૈસા | [before](03_balance_99.50_before.mp3) · [after](03_balance_99.50_after.mp3) |
| 4 | 10-15 દિવસ લાગશે. | **એક શૂન્ય એક પાંચ** દિવસ લાગશે | દસથી પંદર દિવસ લાગશે. | [before](04_range_10-15_days_before.mp3) · [after](04_range_10-15_days_after.mp3) |
| 5 | તે 1લા નંબરે આવ્યો. | તે **એકલા** ("alone") નંબરે આવ્યો | તે પહેલા નંબરે આવ્યો. | [before](05_ordinal_1la_before.mp3) · [after](05_ordinal_1la_after.mp3) |
| 6 | વ્યાજ દર 8.5% છે. | આઠ દશાંશ પાંચ **પર્સેન્ટ** | સાડા આઠ ટકા | [before](06_interest_8.5pct_before.mp3) · [after](06_interest_8.5pct_after.mp3) |
| 7 | તમારો આગલો હપ્તો ₹4,350 તા. 05/12/2026 ના રોજ ભરવાનો છે. | … ચાર હજાર ત્રણસો પચાસ **રૂપીસ તા** પાંચ ડિસેમ્બર … | … રૂપિયા **તારીખ** પાંચ ડિસેમ્બર … | [before](07_agent_emi_due_date_before.mp3) · [after](07_agent_emi_due_date_after.mp3) |
| 8 | બાકી રકમ ₹2,37,450 છે અને વ્યાજ દર 10.75% છે. | … રૂપીસ … દસ દશાંશ સાત પાંચ પર્સેન્ટ | … રૂપિયા … પોણા અગિયાર ટકા | [before](08_agent_loan_and_rate_before.mp3) · [after](08_agent_loan_and_rate_after.mp3) |
| 9 | પાર્સલ … આજે સાંજે 6:30 સુધી પહોંચશે. | … છ વાગ્યે ત્રીસ મિનિટ સુધી | … સાડા છ વાગ્યા સુધી | [before](09_agent_parcel_6-30_before.mp3) · [after](09_agent_parcel_6-30_after.mp3) |
| 10 | *A real `sarvam-105b-conversations` reply as a Gujarati bank agent:* "અમારી શાખા સવારે 9:30 વાગ્યે ખુલે છે. તે સાંજે 4:30 વાગ્યે બંધ થાય છે." | … સવારે નવ વાગ્યે ત્રીસ મિનિટ વાગ્યે ખુલે છે … ચાર વાગ્યે ત્રીસ મિનિટ વાગ્યે બંધ થાય છે | *(after clip not recorded: API credits ran out)* | [before](10_llm_agent_branch_hours_before.mp3) |

The after clips were generated with gujnorm v0.1.0. The text sent for clip 7 had "છવ્વીસ ના રોજ"; v0.1.1 joins it to "છવ્વીસના રોજ".
