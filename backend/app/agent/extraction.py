import re
from dataclasses import dataclass, field
from typing import Any

import httpx

from app.core.config import get_settings


STATE_ALIASES = {
    "bihar": "IN-BR",
    "uttar pradesh": "IN-UP",
    "up": "IN-UP",
    "maharashtra": "IN-MH",
    "tamil nadu": "IN-TN",
    "west bengal": "IN-WB",
    "karnataka": "IN-KA",
    "kerala": "IN-KL",
    "gujarat": "IN-GJ",
    "punjab": "IN-PB",
    "odisha": "IN-OR",
    "orissa": "IN-OR",
    "telangana": "IN-TG",
}
SENSITIVE_PATTERNS = [
    r"\baadhaar\b",
    r"\baadhar\b",
    r"\botp\b",
    r"\bbank account\b",
    r"\bbank_account_number\b",
    r"\baccount_number\b",
]

STRUCTURED_DIRECT_FIELDS = {
    "display_name",
    "state_code",
    "district",
    "age",
    "gender",
    "occupation_type",
    "annual_income",
    "land_holding_acres",
}
STRUCTURED_CUSTOM_FIELDS = {"has_bank_account", "has_land_record", "ration_card_type", "is_pregnant", "child_order"}
SENSITIVE_STRUCTURED_KEYS = {"aadhaar", "aadhar", "aadhaar_number", "otp", "bank_account", "bank_account_number", "account_number"}
BPL_RATION_TYPES = {"bpl", "aay", "antyodaya"}
YES_WORDS = {"yes", "y", "haan", "ha", "correct", "right"}
NO_WORDS = {"no", "n", "nahin", "nahi", "wrong", "incorrect"}


@dataclass(frozen=True)
class ExtractedFact:
    field: str
    value: Any
    confidence: float
    member_reference: str = "self"


@dataclass(frozen=True)
class ExtractedFacts:
    facts: list[ExtractedFact] = field(default_factory=list)
    active_member_reference: str = "self"
    needs_confirmation: list[ExtractedFact] = field(default_factory=list)


class DeterministicFactExtractor:
    def extract(self, message: str) -> ExtractedFacts:
        lower = message.lower()
        if lower.strip().startswith("profile_facts:"):
            return self._extract_structured_profile(message)
        if any(re.search(pattern, lower) for pattern in SENSITIVE_PATTERNS):
            return ExtractedFacts()

        member = self._member_reference(lower)
        facts: list[ExtractedFact] = []
        age_match = re.search(r"\b(?:i am|age is|aged|she is|he is|mother is|father is)?\s*(\d{1,3})\s*(?:years?|yrs?)?\b", lower)
        if age_match:
            age = int(age_match.group(1))
            if 0 <= age <= 120:
                facts.append(ExtractedFact("age", age, 0.9, member))

        for name, code in STATE_ALIASES.items():
            if re.search(rf"\b{re.escape(name)}\b", lower):
                facts.append(ExtractedFact("state_code", code, 0.88, member))
                break

        if any(word in lower for word in ["farmer", "farming", "agriculture", "kisan"]):
            facts.append(ExtractedFact("occupation_type", "farmer", 0.86, member))
        elif any(word in lower for word in ["labour", "labor", "worker"]):
            facts.append(ExtractedFact("occupation_type", "labourer", 0.8, member))

        if any(word in lower for word in ["widow", "widowed"]):
            facts.append(ExtractedFact("marital_status", "widowed", 0.9, member))
            facts.append(ExtractedFact("gender", "female", 0.8, member))
        elif "married" in lower:
            facts.append(ExtractedFact("marital_status", "married", 0.86, member))

        if any(word in lower for word in ["woman", "female", "girl", "mother", "wife"]):
            facts.append(ExtractedFact("gender", "female", 0.82, member))
        elif any(word in lower for word in ["man", "male", "father", "husband"]):
            facts.append(ExtractedFact("gender", "male", 0.82, member))

        income = re.search(r"(?:income|earn|earning|around|about)\D+(\d{4,7})", lower)
        if income:
            facts.append(ExtractedFact("annual_income", int(income.group(1)), 0.78, member))

        land = re.search(r"(\d+(?:\.\d+)?)\s*(?:acre|acres)", lower)
        if land:
            facts.append(ExtractedFact("land_holding_acres", float(land.group(1)), 0.84, member))

        return ExtractedFacts(facts=facts, active_member_reference=member)

    @staticmethod
    def _member_reference(lower: str) -> str:
        for relation in ["mother", "father", "wife", "husband", "daughter", "son", "child"]:
            if relation in lower:
                return relation
        return "self"

    def _extract_structured_profile(self, message: str) -> ExtractedFacts:
        payload = message.split(":", 1)[1]
        parsed: dict[str, str] = {}
        for part in payload.split(";"):
            if "=" not in part:
                continue
            raw_key, raw_value = part.split("=", 1)
            key = raw_key.strip().lower()
            value = raw_value.strip()
            if not key or not value:
                continue
            if key in SENSITIVE_STRUCTURED_KEYS or any(re.search(pattern, value.lower()) for pattern in SENSITIVE_PATTERNS):
                return ExtractedFacts()
            parsed[key] = value

        facts: list[ExtractedFact] = []
        for key, raw_value in parsed.items():
            if key in STRUCTURED_DIRECT_FIELDS:
                value = self._coerce_structured_value(key, raw_value)
                if value is not None:
                    facts.append(ExtractedFact(key, value, 0.98))
            elif key in STRUCTURED_CUSTOM_FIELDS:
                value = self._coerce_structured_value(key, raw_value)
                if value is not None:
                    facts.append(ExtractedFact(f"custom_attributes.{key}", value, 0.98))
                    if key == "ration_card_type":
                        ration_type = str(value).lower()
                        is_bpl = ration_type in BPL_RATION_TYPES
                        facts.append(ExtractedFact("custom_attributes.is_bpl", is_bpl, 0.96))
                        facts.append(ExtractedFact("custom_attributes.bpl_card", is_bpl, 0.96))
                        if is_bpl:
                            facts.append(ExtractedFact("custom_attributes.poor_household", True, 0.96))
        return ExtractedFacts(facts=facts)

    @staticmethod
    def _coerce_structured_value(key: str, raw_value: str) -> Any | None:
        value = raw_value.strip()
        if key == "state_code":
            code = value.upper()
            return code if re.fullmatch(r"IN-[A-Z]{2}", code) else None
        if key == "age":
            if not value.isdigit():
                return None
            age = int(value)
            return age if 0 <= age <= 120 else None
        if key in {"annual_income"}:
            if not value.isdigit():
                return None
            return int(value)
        if key == "land_holding_acres":
            try:
                acres = float(value)
            except ValueError:
                return None
            return acres if acres >= 0 else None
        if key in {"has_bank_account", "has_land_record", "is_pregnant"}:
            lowered = value.lower()
            if lowered in {"true", "yes", "1"}:
                return True
            if lowered in {"false", "no", "0"}:
                return False
            return None
        if key == "child_order":
            if not value.isdigit():
                return None
            order = int(value)
            return order if 1 <= order <= 20 else None
        if key == "gender":
            lowered = value.lower()
            return lowered if lowered in {"female", "male", "other"} else None
        if key == "ration_card_type":
            lowered = value.lower().replace(" ", "_")
            return lowered if lowered in {"bpl", "aay", "antyodaya", "apl", "none"} else None
        if key in {"display_name", "district", "occupation_type"}:
            cleaned = re.sub(r"\s+", " ", value).strip()
            return cleaned[:80] if cleaned else None
        return None


def _is_sensitive_field_or_value(field: str, value: Any) -> bool:
    lowered_field = field.lower()
    if lowered_field in SENSITIVE_STRUCTURED_KEYS or any(re.search(pattern, lowered_field) for pattern in SENSITIVE_PATTERNS):
        return True
    lowered_value = str(value).lower()
    return any(re.search(pattern, lowered_value) for pattern in SENSITIVE_PATTERNS)


def _fact_from_payload(payload: dict[str, Any]) -> ExtractedFact | None:
    field_name = str(payload.get("field", "")).strip()
    if not field_name:
        return None
    value = payload.get("value")
    if _is_sensitive_field_or_value(field_name, value):
        return None
    try:
        confidence = float(payload.get("confidence", 0))
    except (TypeError, ValueError):
        confidence = 0
    if confidence < 0:
        confidence = 0
    if confidence > 1:
        confidence = 1
    return ExtractedFact(
        field=field_name,
        value=value,
        confidence=confidence,
        member_reference=str(payload.get("member_reference") or "self"),
    )


def _facts_from_payload(payload: dict[str, Any]) -> ExtractedFacts:
    facts = [_fact_from_payload(item) for item in payload.get("facts", []) if isinstance(item, dict)]
    confirmation = [_fact_from_payload(item) for item in payload.get("needs_confirmation", []) if isinstance(item, dict)]
    return ExtractedFacts(
        facts=[fact for fact in facts if fact is not None],
        active_member_reference=str(payload.get("active_member_reference") or "self"),
        needs_confirmation=[fact for fact in confirmation if fact is not None],
    )


async def extract_facts(message: str) -> ExtractedFacts:
    deterministic = DeterministicFactExtractor().extract(message)
    if message.lower().strip().startswith("profile_facts:"):
        return deterministic
    settings = get_settings()
    if settings.llm_provider not in {"ollama", "groq"}:
        return deterministic
    attempts = max(1, settings.agent_json_repair_retries + 1)
    for attempt in range(attempts):
        try:
            payload = await _call_llm_json(message, repair=attempt > 0)
            extracted = _facts_from_payload(payload)
            if extracted.facts or extracted.needs_confirmation:
                return extracted
        except Exception:
            continue
    return deterministic


async def _call_llm_json(message: str, repair: bool = False) -> dict[str, Any]:
    settings = get_settings()
    system = (
        "Extract welfare eligibility profile facts from the user message. Return strict JSON only with keys "
        "facts, active_member_reference, and needs_confirmation. Facts need field, value, confidence, and optional member_reference. "
        "Never include Aadhaar, OTP, bank account, or raw sensitive identifiers."
    )
    if repair:
        system = "Repair the previous extraction into strict JSON only. " + system
    body = {
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": message}],
        "temperature": settings.agent_temperature,
        "max_tokens": settings.agent_max_tokens,
    }
    timeout = httpx.Timeout(settings.agent_timeout_seconds)
    async with httpx.AsyncClient(timeout=timeout) as client:
        if settings.llm_provider == "ollama":
            response = await client.post(
                f"{settings.ollama_base_url.rstrip('/')}/api/chat",
                json={**body, "model": settings.ollama_model, "stream": False, "format": "json"},
            )
            response.raise_for_status()
            content = response.json().get("message", {}).get("content", "{}")
        elif settings.llm_provider == "groq" and settings.groq_api_key:
            response = await client.post(
                f"{settings.groq_base_url.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {settings.groq_api_key}"},
                json={**body, "model": settings.groq_chat_model, "response_format": {"type": "json_object"}},
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
        else:
            raise ValueError("unsupported provider")
    import json

    return json.loads(content)


def prepare_pending_confirmation(state, facts: list[ExtractedFact], profile: dict[str, Any]) -> dict[str, Any] | None:
    if state.pending_confirmation:
        return state.pending_confirmation
    for fact in facts:
        if 0.5 <= fact.confidence < 0.75:
            pending = {
                "fact": {
                    "field": fact.field,
                    "value": fact.value,
                    "confidence": fact.confidence,
                    "member_reference": fact.member_reference,
                }
            }
            state.pending_confirmation = pending
            return pending
    return None


def merge_confirmed_pending_fact(state, message: str, profile: dict[str, Any]) -> bool | None:
    if not state.pending_confirmation:
        return None
    answer = message.strip().lower()
    if answer not in YES_WORDS | NO_WORDS:
        return None
    fact_payload = state.pending_confirmation.get("fact", {})
    state.pending_confirmation = None
    if answer in NO_WORDS:
        return False
    fact = ExtractedFact(
        field=fact_payload["field"],
        value=fact_payload.get("value"),
        confidence=1.0,
        member_reference=fact_payload.get("member_reference", "self"),
    )
    if fact.field.startswith("custom_attributes."):
        profile.setdefault("custom_attributes", {})[fact.field.split(".", 1)[1]] = fact.value
    else:
        profile[fact.field] = fact.value
    return True
