GOOGLE_VOICE_BY_LANGUAGE = {
    "en": "en-IN-Wavenet-A",
    "hi": "hi-IN-Wavenet-A",
    "bn": "bn-IN-Wavenet-A",
    "te": "te-IN-Standard-A",
    "mr": "mr-IN-Wavenet-A",
    "ta": "ta-IN-Wavenet-A",
    "gu": "gu-IN-Wavenet-A",
    "kn": "kn-IN-Wavenet-A",
    "ml": "ml-IN-Wavenet-A",
    "pa": "pa-IN-Standard-A",
    "or": "hi-IN-Wavenet-A",
}


def voice_name_for_language(language_code: str, provider: str) -> str:
    if provider == "google":
        return GOOGLE_VOICE_BY_LANGUAGE.get(language_code, "en-IN-Wavenet-A")
    return f"{language_code}-default_female"
