from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class LifeEvent:
    event_type: str
    profile_patch: dict[str, Any] = field(default_factory=dict)
    member_patch: dict[str, Any] = field(default_factory=dict)


def detect_life_event(message: str, llm: object | None = None) -> LifeEvent | None:
    lower = message.lower()
    if "married" in lower or "wedding" in lower:
        return LifeEvent(event_type="marriage", profile_patch={"marital_status": "married"})
    child_words = ["had a baby", "gave birth", "child birth", "newborn", "baby girl", "baby boy"]
    if any(word in lower for word in child_words):
        gender = "female" if "girl" in lower else "male" if "boy" in lower else "unknown"
        return LifeEvent(
            event_type="child_birth",
            member_patch={"relationship_to_primary": "child", "age": 0, "gender": gender},
        )
    return None
