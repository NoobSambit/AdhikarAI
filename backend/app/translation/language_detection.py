from dataclasses import dataclass
import re

ROMANISED_TOKENS: dict[str, set[str]] = {
    "hi": {"meri", "mera", "maa", "vidhwa", "hai", "mujhe", "kisan", "yojana", "chahiye", "gaon"},
    "mr": {"majhi", "aai", "vidhwa", "aahe", "shetkari", "yojana"},
    "ta": {"en", "amma", "vivasayi", "venum", "thittam"},
    "bn": {"amar", "maa", "bidoba", "krishok", "chai"},
    "te": {"naa", "amma", "raithu", "kavali", "pathakam"},
    "gu": {"mari", "maa", "vidhva", "khedut", "yojana"},
}


@dataclass(frozen=True)
class RomanisedDetectionResult:
    language_code: str
    normalized_text: str
    matched_tokens: list[str]


def detect_romanised_language(text: str) -> RomanisedDetectionResult | None:
    if not text or not _is_latin_script(text):
        return None
    words = re.findall(r"[a-zA-Z]+", text.lower())
    best_lang = None
    best_matches: list[str] = []
    for lang, tokens in ROMANISED_TOKENS.items():
        matches = [word for word in words if word in tokens]
        if len(matches) > len(best_matches):
            best_lang = lang
            best_matches = matches
    if best_lang and len(set(best_matches)) >= 2:
        return RomanisedDetectionResult(best_lang, text.strip(), sorted(set(best_matches)))
    return None


def _is_latin_script(text: str) -> bool:
    letters = [char for char in text if char.isalpha()]
    return bool(letters) and all(ord(char) < 128 for char in letters)
