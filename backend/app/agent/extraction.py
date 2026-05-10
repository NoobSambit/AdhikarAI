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
SENSITIVE_PATTERNS = [r"\baadhaar\b", r"\baadhar\b", r"\botp\b", r"\bbank account\b"]


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
