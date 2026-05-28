import re
from dataclasses import dataclass, field
from typing import Any


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
STRUCTURED_CUSTOM_FIELDS = {"has_bank_account", "has_land_record", "ration_card_type"}
SENSITIVE_STRUCTURED_KEYS = {"aadhaar", "aadhar", "aadhaar_number", "otp", "bank_account", "bank_account_number", "account_number"}
BPL_RATION_TYPES = {"bpl", "aay", "antyodaya"}


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
        if key in {"has_bank_account", "has_land_record"}:
            lowered = value.lower()
            if lowered in {"true", "yes", "1"}:
                return True
            if lowered in {"false", "no", "0"}:
                return False
            return None
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
