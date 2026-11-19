# -*- coding: utf-8 -*-
"""gujnorm — Gujarati text normalizer for TTS (times, money, fractions, dates, ranges, ordinals, IDs)."""
from .rules import PASSES
from .numbers import num_words, year_words, time_words, fraction_words

__all__ = ["normalize", "num_words", "year_words", "time_words", "fraction_words"]
__version__ = "0.1.1"


def normalize(text: str) -> str:
    """Rewrite written Gujarati into fully spoken Gujarati words, ready for TTS."""
    for p in PASSES:
        text = p(text)
    return text
