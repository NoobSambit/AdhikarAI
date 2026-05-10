from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class DocumentCheckRequest(BaseModel):
    organisation_id: UUID
    profile_id: UUID | None = None
    documents_available: list[str] = Field(default_factory=list)


class MissingDocumentModel(BaseModel):
    name: str
    accepted_substitutes: list[dict[str, Any]] = Field(default_factory=list)
    original_document_instructions: str


class DocumentCheckResponse(BaseModel):
    is_sufficient: bool
    missing: list[MissingDocumentModel] = Field(default_factory=list)
    substitutes_available: list[dict[str, Any]] = Field(default_factory=list)
    matched_documents: list[str] = Field(default_factory=list)
