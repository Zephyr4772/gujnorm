# -*- coding: utf-8 -*-
"""Gujarati number words (Indian numbering system)."""

# 0–99 are irregular in Gujarati and must be listed.
UNITS = (
    "શૂન્ય એક બે ત્રણ ચાર પાંચ છ સાત આઠ નવ "
    "દસ અગિયાર બાર તેર ચૌદ પંદર સોળ સત્તર અઢાર ઓગણીસ "
    "વીસ એકવીસ બાવીસ ત્રેવીસ ચોવીસ પચીસ છવ્વીસ સત્તાવીસ અઠ્ઠાવીસ ઓગણત્રીસ "
    "ત્રીસ એકત્રીસ બત્રીસ તેત્રીસ ચોત્રીસ પાંત્રીસ છત્રીસ સાડત્રીસ આડત્રીસ ઓગણચાલીસ "
    "ચાલીસ એકતાલીસ બેતાલીસ તેતાલીસ ચુંમાલીસ પિસ્તાલીસ છેતાલીસ સુડતાલીસ અડતાલીસ ઓગણપચાસ "
    "પચાસ એકાવન બાવન ત્રેપન ચોપન પંચાવન છપ્પન સત્તાવન અઠ્ઠાવન ઓગણસાઠ "
    "સાઠ એકસઠ બાસઠ ત્રેસઠ ચોસઠ પાંસઠ છાસઠ સડસઠ અડસઠ અગણોસિત્તેર "
    "સિત્તેર એકોતેર બોતેર તોતેર ચુંમોતેર પંચોતેર છોતેર સિત્યોતેર ઇઠ્યોતેર ઓગણએંસી "
    "એંસી એક્યાસી બ્યાસી ત્યાસી ચોર્યાસી પંચ્યાસી છ્યાસી સિત્યાસી ઈઠ્યાસી નેવ્યાસી "
    "નેવું એકાણું બાણું ત્રાણું ચોરાણું પંચાણું છન્નું સત્તાણું અઠ્ઠાણું નવ્વાણું"
).split()
assert len(UNITS) == 100, len(UNITS)

HUNDREDS = {1: "એકસો", 2: "બસો", 3: "ત્રણસો", 4: "ચારસો", 5: "પાંચસો",
            6: "છસો", 7: "સાતસો", 8: "આઠસો", 9: "નવસો"}

DIGITS = UNITS[:10]

MONTHS = ["જાન્યુઆરી", "ફેબ્રુઆરી", "માર્ચ", "એપ્રિલ", "મે", "જૂન",
          "જુલાઈ", "ઓગસ્ટ", "સપ્ટેમ્બર", "ઓક્ટોબર", "નવેમ્બર", "ડિસેમ્બર"]

# ordinal stems: 1 પહેલ-, 2 બીજ-, 3 ત્રીજ-, 4 ચોથ-, 6 છઠ્ઠ-, else <number>મ-
ORD_STEM = {1: "પહેલ", 2: "બીજ", 3: "ત્રીજ", 4: "ચોથ", 6: "છઠ્ઠ"}


def num_words(n: int) -> str:
    """Cardinal in Indian grouping: 1,25,000 -> એક લાખ પચીસ હજાર."""
    if n < 0:
        return "માઇનસ " + num_words(-n)
    if n < 100:
        return UNITS[n]
    parts = []
    crore, n = divmod(n, 10**7)
    if crore:
        parts.append(num_words(crore) + " કરોડ")
    lakh, n = divmod(n, 10**5)
    if lakh:
        parts.append(UNITS[lakh] + " લાખ")
    thousand, n = divmod(n, 1000)
    if thousand:
        parts.append(UNITS[thousand] + " હજાર")
    hundred, n = divmod(n, 100)
    if hundred:
        parts.append(HUNDREDS[hundred])
    if n:
        parts.append(UNITS[n])
    return " ".join(parts)


def year_words(y: int) -> str:
    """1947 -> ઓગણીસો સુડતાલીસ, 1857 -> અઢારસો સત્તાવન, 2026 -> બે હજાર છવ્વીસ."""
    if 1100 <= y <= 1999:
        hi, lo = divmod(y, 100)
        head = "ઓગણીસો" if hi == 19 else UNITS[hi] + "સો"
        return head if lo == 0 else f"{head} {UNITS[lo]}"
    return num_words(y)


def digit_words(s: str) -> str:
    """'0045' -> શૂન્ય શૂન્ય ચાર પાંચ (ignores spaces/dashes)."""
    return " ".join(DIGITS[int(c)] for c in s if c.isdigit())


def fraction_words(i: int, frac: str) -> str:
    """Gujarati fraction words for x.5 / x.25 / x.75; otherwise '<n> દશાંશ <digits>'."""
    f = frac.rstrip("0")
    if i <= 99:
        if f == "5":
            return {0: "અડધો", 1: "દોઢ", 2: "અઢી"}.get(i, "સાડા " + UNITS[i])
        if f == "25":
            return {0: "પા", 1: "સવા"}.get(i, "સવા " + UNITS[i])
        if f == "75":
            return "પોણો" if i == 0 else "પોણા " + num_words(i + 1)
    if f == "":
        return num_words(i)
    return f"{num_words(i)} દશાંશ {digit_words(frac)}"


def ordinal_words(n: int, ending: str) -> str:
    """n + inflection vowel (ો ા ી ું ે) -> પહેલો / બીજી / ચોથું / એકવીસમી."""
    stem = ORD_STEM.get(n, num_words(n) + "મ")
    return stem + ending


def time_words(h: int, m: int) -> str:
    """Clock time the way Gujarati speakers say it (12-hour)."""
    h12 = h % 12 or 12
    nxt = h12 % 12 + 1
    if m == 0:
        return UNITS[h12]
    if m == 15:
        return "સવા " + UNITS[h12]
    if m == 30:
        return {1: "દોઢ", 2: "અઢી"}.get(h12, "સાડા " + UNITS[h12])
    if m == 45:
        return "પોણા " + UNITS[nxt]
    return f"{UNITS[h12]} ને {UNITS[m]}"


def day_period(h: int) -> str:
    """24h hour -> સવારે / બપોરે / સાંજે / રાત્રે."""
    if 4 <= h < 12:
        return "સવારે"
    if 12 <= h < 16:
        return "બપોરે"
    if 16 <= h < 20:
        return "સાંજે"
    return "રાત્રે"
