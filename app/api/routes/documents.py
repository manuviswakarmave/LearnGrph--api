from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas import DocumentResponse, DocumentCreate
from app.models.document import Document
import uuid

from fastapi import HTTPException

router = APIRouter(
    prefix="/documents",
    tags=["documents"]
)

@router.post(
    "",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_document(
        document_data: DocumentCreate,
        db: Session = Depends(get_db),

):
    document = Document(
        filename = document_data.filename,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    return document

@router.get(
    "/{document_id}",
    response_model=DocumentResponse
)
def get_document(
        document_id : uuid.UUID,
        db: Session = Depends(get_db),
):
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return document




