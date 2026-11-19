# -*- coding: utf-8 -*-
"""Drop-in helper: normalize Gujarati text, then call Sarvam Bulbul.

    from sarvamai import SarvamAI
    from gujnorm.sarvam import speak
    audio_b64_chunks = speak(SarvamAI(api_subscription_key=...), "તમારો હપ્તો ₹4,350 તા. 05/12/2026 ના રોજ છે.")
"""
from . import normalize


def speak(client, text, language_code="gu-IN", **tts_kwargs):
    """Like client.text_to_speech.convert, but runs gujnorm first for gu-IN text."""
    if language_code == "gu-IN":
        text = normalize(text)
    tts_kwargs.setdefault("model", "bulbul:v3")
    return client.text_to_speech.convert(text=text, language_code=language_code, **tts_kwargs).audios


def wrap_tts_text(fn):
    """Decorator for voice-agent pipelines (LiveKit / Pipecat): normalize the text an LLM emits before TTS.

        @wrap_tts_text
        async def tts_node(text): ...
    """
    import functools, inspect

    if inspect.iscoroutinefunction(fn):
        @functools.wraps(fn)
        async def aw(text, *a, **k):
            return await fn(normalize(text), *a, **k)
        return aw

    @functools.wraps(fn)
    def w(text, *a, **k):
        return fn(normalize(text), *a, **k)
    return w
