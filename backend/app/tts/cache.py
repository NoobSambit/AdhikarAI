from hashlib import sha256


def tts_cache_key(text: str, language_code: str, voice_name: str, speaking_rate: float) -> str:
    digest = sha256(f"{language_code}\0{voice_name}\0{speaking_rate:.2f}\0{text}".encode("utf-8")).hexdigest()
    return f"tts:{digest}"
