from typing import Annotated, Any, TypedDict

try:
    from langgraph.graph.message import add_messages
except Exception:  # pragma: no cover - dependency is declared; fallback keeps imports testable.
    def add_messages(left, right):
        return (left or []) + (right or [])


class AdhikarAgentState(TypedDict, total=False):
    session_id: str
    organisation_id: str
    messages: Annotated[list[dict[str, str]], add_messages]
    user_profile: dict[str, Any]
    household: dict[str, Any]
    active_member_id: str
    asked_fields: list[str]
    remaining_required_fields: list[str]
    confidence_score: float
    profile_completeness: int
    language_code: str
    last_match_result: dict[str, Any] | None
    turn_count_since_result: int
