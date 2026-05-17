import csv
from dataclasses import dataclass
from io import StringIO

from app.core.config import get_settings
from app.core.errors import ApiError


CSV_HEADERS = {
    "name",
    "phone_e164",
    "state_code",
    "district",
    "village",
    "language_code",
    "age",
    "gender",
    "caste_category",
    "annual_income",
    "land_holding_acres",
    "occupation_type",
    "marital_status",
    "existing_scheme_ids",
}
REQUIRED_HEADERS = {"name", "state_code", "language_code"}


@dataclass(frozen=True, slots=True)
class CsvBeneficiaryRow:
    row_number: int
    payload: dict[str, str]


def parse_beneficiary_csv(content: bytes) -> list[CsvBeneficiaryRow]:
    max_bytes = get_settings().bulk_eligibility_max_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise ApiError(413, "CSV_TOO_LARGE", "CSV must be 2 MB or smaller.", "file")
    reader = csv.DictReader(StringIO(content.decode("utf-8-sig")))
    headers = set(reader.fieldnames or [])
    missing = sorted(REQUIRED_HEADERS - headers)
    unknown = sorted(headers - CSV_HEADERS)
    if missing or unknown:
        raise ApiError(
            422,
            "CSV_INVALID_HEADERS",
            "CSV headers do not match the documented profile fields.",
            "file",
            {"missing": missing, "unknown": unknown},
        )
    rows = [CsvBeneficiaryRow(index, {key: value for key, value in row.items() if key}) for index, row in enumerate(reader, start=2)]
    if len(rows) > get_settings().bulk_eligibility_max_rows:
        raise ApiError(422, "CSV_TOO_MANY_ROWS", "CSV can include at most 500 rows.", "file")
    return rows
