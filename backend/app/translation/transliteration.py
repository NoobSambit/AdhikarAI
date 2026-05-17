from app.translation.language_detection import detect_romanised_language


def normalize_typed_text(text: str, is_asr_transcript: bool = False) -> tuple[str, str | None]:
    if is_asr_transcript:
        return text, None
    detected = detect_romanised_language(text)
    if detected is None:
        return text, None
    return detected.normalized_text, detected.language_code
