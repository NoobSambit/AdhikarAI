from hashlib import sha256


def translation_cache_key(text: str, source_lang: str, target_lang: str, provider: str) -> str:
    digest = sha256(f"{provider}\0{source_lang}\0{target_lang}\0{text}".encode("utf-8")).hexdigest()
    return f"translation:{digest}"
