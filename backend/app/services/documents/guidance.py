DEFAULT_ORIGINAL_DOCUMENT_INSTRUCTIONS = {
    "income certificate": "Visit the tehsil, revenue office, or state e-district portal to apply for an income certificate. Expected time: 7 to 21 days. Expected cost: INR 0 to 50 depending on state.",
    "aadhaar": "Visit an Aadhaar Seva Kendra or authorised enrolment centre to update or obtain Aadhaar details.",
    "bank passbook": "Visit your bank branch and ask for an updated passbook or account statement.",
    "ration card": "Visit the Food and Civil Supplies office or state ration card portal to apply for a ration card.",
}


def original_document_instructions(document_name: str) -> str:
    return DEFAULT_ORIGINAL_DOCUMENT_INSTRUCTIONS.get(
        document_name.strip().lower(),
        f"Visit the issuing office for {document_name} and ask how to obtain the original document.",
    )
