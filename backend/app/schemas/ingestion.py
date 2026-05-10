from typing import Literal

from pydantic import BaseModel


class MySchemeIngestionRequest(BaseModel):
    organisation_id: str
    mode: Literal["api", "json_file", "csv"]
    source_uri: str | None = None
    dry_run: bool = False


class MySchemeIngestionResponse(BaseModel):
    ingestion_run_id: str
    status: str

