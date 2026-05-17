import pytest

from app.dashboard.bulk_eligibility import parse_beneficiary_csv
from app.core.errors import ApiError


def test_csv_rejects_unknown_aadhaar_header():
    content = b"name,state_code,language_code,aadhaar_number\nSita Devi,IN-BR,hi,123412341234\n"

    with pytest.raises(ApiError) as exc:
        parse_beneficiary_csv(content)

    assert exc.value.code == "CSV_INVALID_HEADERS"
    assert "aadhaar_number" in str(exc.value.details)


def test_csv_rejects_more_than_500_rows():
    rows = ["name,state_code,language_code"]
    rows.extend(f"Person {index},IN-BR,hi" for index in range(501))

    with pytest.raises(ApiError) as exc:
        parse_beneficiary_csv("\n".join(rows).encode())

    assert exc.value.code == "CSV_TOO_MANY_ROWS"
