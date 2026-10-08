import uuid
from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict

class DocumentCreate(BaseModel):
    filename: str


class DocumentResponse(BaseModel):
    id: uuid.UUID
    filename: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentProcessResponse(BaseModel):
    document_id: uuid.UUID
    status: str
    chunks_created: int


class ChunkSearchResult(BaseModel):
    chunk_index: int
    page_number: int
    content: str
    distance: float

class DocumentSearchRespone(BaseModel):
    query: str
    results: List[ChunkSearchResult]