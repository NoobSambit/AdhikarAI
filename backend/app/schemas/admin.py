from pydantic import BaseModel


class IndexRebuildRequest(BaseModel):
    organisation_id: str
    index_name: str = "schemes_active"


class IndexRebuildResponse(BaseModel):
    index_name: str
    scheme_count: int
    embedding_model: str
    status: str

