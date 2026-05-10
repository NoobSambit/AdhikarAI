from app.schemas.match import MatchProfileResponse


def format_match_result(result: MatchProfileResponse) -> str:
    if result.matched_schemes:
        first = result.matched_schemes[0].scheme.name
        count = len(result.matched_schemes)
        return f"You appear eligible for {count} scheme{'s' if count != 1 else ''}. The strongest match is {first}."
    if result.near_miss_schemes:
        first = result.near_miss_schemes[0].scheme.name
        return f"You are close to qualifying for {first}. I will show what is missing."
    return (
        "I could not find a matching scheme from the current list. "
        "You can try again after adding income, caste, disability, or pregnancy details."
    )
