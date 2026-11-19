"""Shared Sarvam client + helpers. Reads key from .env; never prints it."""
import base64, json, os, time, hashlib, pathlib
from dotenv import load_dotenv
from sarvamai import SarvamAI

ROOT = pathlib.Path(__file__).parent
load_dotenv(ROOT / ".env")
client = SarvamAI(api_subscription_key=os.environ["SARVAM_API_KEY"])
CACHE = ROOT / "out" / "cache"
CACHE.mkdir(parents=True, exist_ok=True)


def _key(*parts):
    return hashlib.sha1(json.dumps(parts, ensure_ascii=False).encode()).hexdigest()[:16]


def retry(fn, tries=4):
    for i in range(tries):
        try:
            return fn()
        except Exception as e:  # rate limits / transient
            code = getattr(e, "status_code", None)
            if i == tries - 1 or code in (400, 401, 403, 404, 422):
                raise
            time.sleep(3 * (i + 1))


def tts(text, model="bulbul:v3", speaker=None, preprocessing=True, rate=16000):
    """Returns path to wav (cached)."""
    k = _key("tts", text, model, speaker, preprocessing, rate)
    p = CACHE / f"tts_{k}.wav"
    if p.exists():
        return p
    kw = dict(text=text, language_code="gu-IN", model=model,
              enable_preprocessing=preprocessing, speech_sample_rate=rate,
              output_audio_codec="wav")
    if speaker:
        kw["speaker"] = speaker
    r = retry(lambda: client.text_to_speech.convert(**kw))
    audio = b"".join(base64.b64decode(a) for a in r.audios)
    p.write_bytes(audio)
    return p


def tts_lang(text, lang="gu-IN", model="bulbul:v3", speaker=None, preprocessing=True, rate=16000):
    k = _key("tts", text, lang, model, speaker, preprocessing, rate)
    p = CACHE / f"tts_{k}.wav"
    if p.exists():
        return p
    kw = dict(text=text, language_code=lang, model=model,
              enable_preprocessing=preprocessing, speech_sample_rate=rate, output_audio_codec="wav")
    if speaker:
        kw["speaker"] = speaker
    r = retry(lambda: client.text_to_speech.convert(**kw))
    p.write_bytes(b"".join(base64.b64decode(a) for a in r.audios))
    return p


def stt(path, model="saaras:v4", mode="transcribe", lang="gu-IN"):
    k = _key("stt", str(path), model, mode, lang)
    p = CACHE / f"stt_{k}.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    with open(path, "rb") as f:
        data = f.read()
    r = retry(lambda: client.speech_to_text.transcribe(
        file=("a.wav", data, "audio/wav"), model=model, mode=mode, language_code=lang))
    out = {"transcript": r.transcript, "language_code": getattr(r, "language_code", None)}
    p.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    return out


def spoken_form(text):
    k = _key("sf", text)
    p = CACHE / f"sf_{k}.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))["out"]
    r = retry(lambda: client.text.transliterate(
        input=text, source_language_code="gu-IN", target_language_code="gu-IN",
        spoken_form=True, spoken_form_numerals_language="native"))
    p.write_text(json.dumps({"out": r.transliterated_text}, ensure_ascii=False), encoding="utf-8")
    return r.transliterated_text


def chat(messages, model="sarvam-105b-conversations", **kw):
    k = _key("chat", messages, model, kw)
    p = CACHE / f"chat_{k}.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))["out"]
    r = retry(lambda: client.chat.completions(messages=messages, model=model, **kw))
    out = r.choices[0].message.content
    p.write_text(json.dumps({"out": out}, ensure_ascii=False), encoding="utf-8")
    return out
