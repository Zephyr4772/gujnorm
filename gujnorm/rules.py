# -*- coding: utf-8 -*-
"""Ordered normalization passes. Every pass emits words (no digits), so later passes never re-match."""
import re
import threading
from .numbers import (num_words, year_words, digit_words, fraction_words, ordinal_words,
                      time_words, day_period, MONTHS)

GU = "઀-૿"
NS = r"(?<![\d.,/:])"          # number start
NE = r"(?![\d])"                # number end
END = r"(?=[\s.,!?;:)\]\"'”’…]|$)"   # word end


# ---------------- 1. digits ----------------
_GU_DIGITS = str.maketrans("૦૧૨૩૪૫૬૭૮૯", "0123456789")


def gujarati_digits(t):
    return t.translate(_GU_DIGITS)


# ---------------- 2. abbreviations ----------------
_ABBR = [
    (r"તા\.\s?ક\.", "તાજા કલમ"),
    (r"[ઇઈ]\.\s?સ\.\s?પૂ\.", "ઈસવીસન પૂર્વે"),
    (r"[ઇઈ]\.\s?સ\.", "ઈસવીસન"),
    (r"કિ\.\s?મી\.", "કિલોમીટર"),
    (r"કિ\.\s?ગ્રા\.", "કિલોગ્રામ"),
    (r"સૌ\.\s?યુ\.", "સૌરાષ્ટ્ર યુનિવર્સિટી"),
    (r"ગુ\.\s?યુ\.", "ગુજરાત યુનિવર્સિટી"),
    (rf"(?<![{GU}])તા\.", "તારીખ"),
    (rf"(?<![{GU}])નં\.", "નંબર"),
    (rf"(?<![{GU}])ડૉ\.", "ડૉક્ટર"),
    (rf"(?<![{GU}])ડો\.", "ડૉક્ટર"),
    (rf"(?<![{GU}])રૂ\.(?=\s*\d)", "₹"),
    (rf"(?<![{GU}])રૂ\.", "રૂપિયા"),
]


def abbreviations(t):
    for pat, rep in _ABBR:
        t = re.sub(pat, rep, t)
    return t


# ---------------- 3. dates ----------------
_MONTH_ALT = "|".join(MONTHS + ["ઑગસ્ટ", "ઓગષ્ટ", "જુન", "જુલાઇ", "ઑક્ટોબર", "સપ્ટેંબર", "નવેંબર", "ડિસેંબર"])


def _date(d, m, y):
    d, m, y = int(d), int(m), int(y)
    if not (1 <= d <= 31 and 1 <= m <= 12):
        return None
    return f"{num_words(d)} {MONTHS[m - 1]} {year_words(y)}"


def dates(t):
    t = re.sub(rf"{NS}(\d{{4}})-(\d{{1,2}})-(\d{{1,2}}){NE}",
               lambda m: _date(m[3], m[2], m[1]) or m[0], t)
    t = re.sub(rf"{NS}(\d{{1,2}})[/.\-](\d{{1,2}})[/.\-](\d{{4}}){NE}",
               lambda m: _date(m[1], m[2], m[3]) or m[0], t)
    t = re.sub(rf"{NS}(\d{{1,2}})\s+({_MONTH_ALT})\s+(\d{{4}}){NE}",
               lambda m: f"{num_words(int(m[1]))} {m[2]} {year_words(int(m[3]))}", t)
    # English month names, either order: "March 12, 1930" / "12 March 1930" / "April 21"
    t = re.sub(rf"\b({_EN_MONTH_ALT})\.?\s+(\d{{1,2}})(?:st|nd|rd|th)?(?:,?\s+(\d{{4}}))?{NE}",
               lambda m: _en_date(m[2], m[1], m[3]), t)
    t = re.sub(rf"{NS}(\d{{1,2}})(?:st|nd|rd|th)?\s+({_EN_MONTH_ALT})\.?(?:,?\s+(\d{{4}}))?{NE}",
               lambda m: _en_date(m[1], m[2], m[3]), t)
    return t


_EN_MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august",
              "september", "october", "november", "december"]
_EN_MONTH_ALT = "|".join([m.capitalize() for m in _EN_MONTHS] + [m[:3].capitalize() for m in _EN_MONTHS if m != "may"])


def _en_date(d, mon, y):
    d = int(d)
    key = mon.lower()[:3]
    idx = [m[:3] for m in _EN_MONTHS].index(key)
    if not 1 <= d <= 31:
        return f"{mon} {d}"
    s = f"{num_words(d)} {MONTHS[idx]}"
    return s + (f" {year_words(int(y))}" if y else "")


def simple_fractions(t):
    fr = {"1/2": "અડધો", "1/4": "પા", "3/4": "પોણો"}
    return re.sub(r"(?<![\d/])([13])/([24])(?![\d/])", lambda m: fr.get(m[0], m[0]), t)


# ---------------- 4. times ----------------
_AMPM = r"(?:[AaPp]\.?\s?[Mm]\.?)(?![A-Za-z])"
_HAS_PERIOD = re.compile(r"(સવારે|બપોરે|સાંજે|રાત્રે|સવારના|બપોરના|સાંજના|રાતના|રાત્રિના)\s*$")
_VAGYE = re.compile(r"\s*(વાગ્યે|વાગે|વાગ્યા|વાગ્યાથી|વાગ્યાનો|વાગ્યાની|વાગ્યાના)")
_GLUE_POST = re.compile(r"(થી|નો|ની|નું|ના)" + END)
_SPACE_POST = re.compile(r"\s+(થી|સુધીમાં|સુધી|વચ્ચે|પહેલાં|પહેલા|પછી|બાદ|આસપાસ|નો|ની|નું|ના)" + END)
_AT = re.compile(r"\s+(એ|પર|પરે)" + END)
_TIME = re.compile(rf"{NS}(\d{{1,2}})(?::(\d{{2}})(?:\s*({_AMPM}))?|\s*({_AMPM})){NE}")


def times(t):
    out, pos = [], 0
    for m in _TIME.finditer(t):
        h = int(m[1])
        mins = int(m[2]) if m[2] else 0
        ampm = (m[3] or m[4] or "").lower().replace(".", "").replace(" ", "")
        if h > 23 or mins > 59 or (ampm and not 1 <= h <= 12):
            continue
        if m.start() < pos:
            continue
        # 24h hour for the period word
        if ampm == "pm":
            h24 = h % 12 + 12
        elif ampm == "am":
            h24 = h % 12
        else:
            h24 = h
        before = t[pos:m.start()]
        period = ""
        if (ampm or h >= 13 or h == 0) and not _HAS_PERIOD.search(t[:m.start()]):
            period = day_period(h24) + " "
        words = period + time_words(h24, mins)
        rest_start = m.end()
        rest = t[rest_start:]
        if (v := _VAGYE.match(rest)):
            words += " " + v[1]
            rest_start += v.end()
        elif (g := _GLUE_POST.match(rest)):
            words += " વાગ્યા" + g[1]
            rest_start += g.end()
        elif (s := _SPACE_POST.match(rest)):
            glue = s[1] in ("થી", "નો", "ની", "નું", "ના")
            words += " વાગ્યા" + ("" if glue else " ") + s[1]
            rest_start += s.end()
        elif (a := _AT.match(rest)):
            words += " વાગ્યે"
            rest_start += a.end()
        else:
            words += " વાગ્યે"
        out.append(before + words)
        pos = rest_start
    out.append(t[pos:])
    return "".join(out)


# ---------------- 5. phone / OTP / IDs ----------------
_PHONE = re.compile(r"(\+\s?91[\s\-]?)?(?<!\d)([6-9]\d{4})[\s\-]?(\d{5})(?!\d)")
_KEYWORD_ID = re.compile(
    r"(OTP|ઓટીપી|PIN|પિન(?:\s*કોડ)?|પીન(?:\s*કોડ)?|કોડ|AWB|આઈડી|આઇડી|ID|અંક|એકાઉન્ટ\s*નંબર|ખાતા\s*નંબર)"
    r"([^\d\n]{0,12}?)(\d[\d \-]{2,}\d)(?!\d)")
_LONG_NUMBER_AFTER_NO = re.compile(r"(નંબર|નં)(\s*)(\d{5,})(?!\d)")
_SPACED_GROUPS = re.compile(r"(?<![\d,.])\d{3,5}(?:[ \-]\d{3,5})+(?![\d,.])")


def ids(t):
    t = _PHONE.sub(lambda m: ("પ્લસ નવ એક " if m[1] else "") + digit_words(m[2]) + ", " + digit_words(m[3]), t)
    t = _KEYWORD_ID.sub(lambda m: m[1] + m[2] + digit_words(m[3]), t)
    t = _LONG_NUMBER_AFTER_NO.sub(lambda m: m[1] + m[2] + digit_words(m[3]), t)
    t = _SPACED_GROUPS.sub(lambda m: ", ".join(digit_words(g) for g in re.split(r"[ \-]", m[0])), t)
    return t


# ---------------- 6. math ----------------
def math_symbols(t):
    t = re.sub(r"(?<=\d)\s*\+\s*(?=\d)", " વત્તા ", t)
    t = re.sub(rf"(?<=[\d{GU}])\s*=\s*(?=[\d₹$])", " બરાબર ", t)
    return t


# ---------------- 7. money ----------------
_POST_GLUE = r"(ની|નું|નો|ના|નાં|માં|થી|નુ)"
_SCALE = r"લાખ|કરોડ|હજાર|Crore|crore|Cr\.?|cr\.?|Lakh|lakh|Lac|lac|L(?![A-Za-z])"
_SCALE_MAP = {"cr": "કરોડ", "crore": "કરોડ", "lakh": "લાખ", "lac": "લાખ", "l": "લાખ"}
_MONEY = re.compile(
    rf"(?:₹|Rs\.?|INR|Rs)\s*(\d[\d,]*)(?:\.(\d+))?(?:\s*({_SCALE}))?"
    rf"(?:{_POST_GLUE}{END}|\s+(ની|નું|નો|ના|નાં){END})?")


def _amount(intpart, frac, scale):
    n = int(intpart.replace(",", ""))
    if scale:
        scale = _SCALE_MAP.get(scale.lower().rstrip("."), scale)
        w = fraction_words(n, frac) if frac else num_words(n)
        return f"{w} {scale} રૂપિયા"
    s = f"{num_words(n)} રૂપિયા"
    if frac:
        paise = int((frac + "0")[:2])
        if paise:
            s += f" {num_words(paise)} પૈસા"
    return s


def money(t):
    t = _MONEY.sub(lambda m: _amount(m[1], m[2], m[3]) + (m[4] or m[5] or ""), t)
    t = re.sub(rf"{NS}(\d[\d,]*)\s*/-", lambda m: num_words(int(m[1].replace(",", ""))) + " રૂપિયા", t)
    def dollars(m):
        d = int(m[1].replace(",", ""))
        s = f"{num_words(d)} ડોલર"
        if m[2]:
            cents = int((m[2] + "0")[:2])
            if cents:
                s += f" {num_words(cents)} સેન્ટ"
        return s
    t = re.sub(r"\$\s*(\d[\d,]*)(?:\.(\d+))?", dollars, t)
    return t


# ---------------- 8. percent ----------------
def percent(t):
    return re.sub(rf"{NS}(\d+)(?:\.(\d+))?\s*%",
                  lambda m: (fraction_words(int(m[1]), m[2]) if m[2] else num_words(int(m[1]))) + " ટકા", t)


# ---------------- 9. units ----------------
_UNITS = [
    ("km/h", "કિલોમીટર પ્રતિ કલાક"), ("kmph", "કિલોમીટર પ્રતિ કલાક"), ("km/l", "કિલોમીટર પ્રતિ લીટર"),
    ("m/s", "મીટર પ્રતિ સેકન્ડ"), ("km", "કિલોમીટર"), ("kWh", "કિલોવોટ કલાક"), ("kW", "કિલોવોટ"),
    ("kg", "કિલો"), ("mg", "મિલિગ્રામ"), ("ml", "મિલીલીટર"), ("cm", "સેન્ટિમીટર"),
    ("mm", "મિલીમીટર"), ("g", "ગ્રામ"), ("°C", "ડિગ્રી સેલ્સિયસ"), ("°F", "ડિગ્રી ફેરનહીટ"), ("°", "ડિગ્રી"),
]
# single-letter / SI units: only after "<number><space>" and before a word end, to avoid eating ordinary letters
_SI_UNITS = [("Pa", "પાસ્કલ"), ("Hz", "હર્ટ્ઝ"), ("A", "એમ્પિયર"), ("W", "વોટ"), ("V", "વોલ્ટ"),
             ("N", "ન્યૂટન"), ("s", "સેકન્ડ"), ("m", "મીટર")]


def units(t):
    for u, w in _UNITS:
        t = re.sub(rf"(?<=\d)\s*{re.escape(u)}(?![A-Za-z])", " " + w, t)
    for u, w in _SI_UNITS:
        t = re.sub(rf"(?<=\d) ?{u}(?=[\s.,;:!?)]|$)", " " + w, t)
    return t


def sci_notation(t):
    """3 x 10^8 -> ત્રણ ગુણ્યા દસની ઘાત આઠ"""
    return re.sub(r"(?<![\d.])(\d+(?:\.\d+)?)\s*[x×]\s*10\^(-?\d+)",
                  lambda m: f"{m[1]} ગુણ્યા દસની ઘાત {'માઇનસ ' if m[2].startswith('-') else ''}{m[2].lstrip('-')}", t)


def slashes(t):
    """7/12 (Gujarat land record) -> સાત બાર; other N/M that is not a date -> N બટા M"""
    t = re.sub(r"(?<![\d/])7/12(?![\d/])", "સાત બાર", t)
    return re.sub(r"(?<![\d/])(\d+)/(\d+)(?![\d/])", lambda m: f"{m[1]} બટા {m[2]}", t)


# ---------------- 10. ranges ----------------
_DAYS = "સોમ|મંગળ|બુધ|ગુરુ|શુક્ર|શનિ|રવિ"


def ranges(t):
    def rng(m):
        a, b = int(m[1]), int(m[2])
        if a >= b:
            return m[0]
        return f"{num_words(a)}થી {num_words(b)}"
    t = re.sub(rf"(?<![A-Za-z\-\d.,/:])(\d+)\s*[-–]\s*(\d+)(?![\d.,]|\s*[-–/]\s*\d)", rng, t)
    t = re.sub(rf"({_DAYS})(વાર)?\s*[-–]\s*({_DAYS})(વાર)?", lambda m: f"{m[1]}{m[2] or ''}થી {m[3]}{m[4] or ''}", t)
    t = re.sub(r"(?<![\w\d])-(?=\d)", "માઇનસ ", t)
    return t


# ---------------- 11. ordinals ----------------
_ORD = re.compile(rf"{NS}(\d+)(લ|જ|થ|ઠ્ઠ|મ)(ું|ો|ા|ી|ે|ુ)(?!ં)")


def ordinals(t):
    def ordf(m):
        n, ending = int(m[1]), m[3]
        if m[2] == "થ" and ending == "ી" and re.match(r"\s*\d", t[m.end():]):
            return f"{num_words(n)}થી"           # ablative "from n" (e.g. 10થી 15)
        if m[2] == "મ" and n in (1, 2, 3, 4, 6):  # "1મી" style is unusual; still say ordinal
            pass
        return ordinal_words(n, ending)
    return _ORD.sub(ordf, t)


# ---------------- 12. decimals ----------------
def decimals(t):
    return re.sub(rf"{NS}(\d+)\.(\d+){NE}", lambda m: fraction_words(int(m[1]), m[2]), t)


# ---------------- 13. integers ----------------
def integers(t):
    def intf(m):
        s = m[0]
        if "," in s:
            return num_words(int(s.replace(",", "")))
        after = t[m.end():m.end() + 12]
        if len(s) > 1 and s[0] == "0":
            return digit_words(s)
        if len(s) >= 8 and not re.match(r"\s*(રૂપિયા|ડોલર|લોકો)", after):
            return digit_words(s)        # long bare numbers are IDs; 6–7 digits stay cardinal (101325 Pa)
        n = int(s)
        if 1100 <= n <= 1999:
            return year_words(n)
        return num_words(n)
    return re.sub(rf"{NS}(\d{{1,3}}(?:,\d{{2,3}})+|\d+){NE}", intf, t)


# ---------------- protect alphanumeric IDs (GJ01AB1234, SBIN0001234, SR-2026-00451, #A7B9) ----------------
# Bulbul already reads these letter-by-letter; we only make sure no number pass touches them.
# also chemistry names / formulas: 1,3-butadiene, Si(CH3)4, C6H12O6, B12
_ALNUM = re.compile(r"(?<![A-Za-z0-9])#?(?=[A-Za-z0-9\-,()]*[A-Za-z])(?=[A-Za-z0-9\-,()]*\d)"
                    r"[A-Za-z0-9()]+(?:[\-,/][A-Za-z0-9()]+)*")
_PH_BASE = 0xE100
_local = threading.local()   # voice agents call this from many threads


def glue_ampm(t):
    return re.sub(r"(?<=\d)(?=(?:AM|PM|am|pm)(?![A-Za-z]))", " ", t)


def protect(t):
    _local.store = store = []

    def keep(m):
        store.append(m[0])
        return chr(_PH_BASE + len(store) - 1)
    return _ALNUM.sub(keep, t)


def restore(t):
    for i, s in enumerate(getattr(_local, "store", [])):
        t = t.replace(chr(_PH_BASE + i), s)
    return t


def cleanup(t):
    t = re.sub(r"[ \t]{2,}", " ", t)
    t = re.sub(r"\s+([.,!?])", r"\1", t)
    return t.strip()


PASSES = [gujarati_digits, units, glue_ampm, protect, abbreviations, dates, simple_fractions, times, ids,
          sci_notation, math_symbols, money, percent, slashes, ranges, ordinals, decimals, integers,
          restore, cleanup]
