import json
from pathlib import Path

from app.schemas.scheme import EligibilityCriteriaModel
from app.services.eligibility.validation import validate_rule


def test_seed_data_has_25_valid_central_schemes():
    data = json.loads((Path(__file__).resolve().parents[2] / "app/seeds/central_schemes.v1.json").read_text())
    assert len(data["schemes"]) >= 25
    ids = {item["id"] for item in data["schemes"]}
    for item in data["schemes"]:
        assert item["source_url"]
        assert data["source_last_checked_at"]
        assert item["verification_status"] == "needs_admin_review"
        criteria = EligibilityCriteriaModel.model_validate(item["eligibility_rule"])
        assert criteria.required_documents
        assert not validate_rule(criteria, ids)

