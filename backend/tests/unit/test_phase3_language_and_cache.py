from app.translation.cache import translation_cache_key
from app.translation.language_detection import detect_romanised_language
from app.tts.cache import tts_cache_key


def test_romanised_hindi_detection_for_typed_text():
    result = detect_romanised_language("meri maa vidhwa hai")

    assert result is not None
    assert result.language_code == "hi"
    assert result.normalized_text


def test_translation_cache_key_is_stable_for_same_request():
    first = translation_cache_key("I am a farmer.", "en", "hi", "local_indictrans2")
    second = translation_cache_key("I am a farmer.", "en", "hi", "local_indictrans2")

    assert first == second
    assert first.startswith("translation:")


def test_tts_cache_key_includes_speaking_rate():
    normal = tts_cache_key("आपकी उम्र कितनी है?", "hi", "hi-IN-Wavenet-A", 1.0)
    slow = tts_cache_key("आपकी उम्र कितनी है?", "hi", "hi-IN-Wavenet-A", 0.75)

    assert normal != slow
    assert normal.startswith("tts:")
