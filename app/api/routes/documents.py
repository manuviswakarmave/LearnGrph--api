from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from pathlib import Path
from sqlalchemy import select

from app.db.session import get_db
from app.schemas.document import DocumentResponse, DocumentCreate, DocumentProcessResponse, ChunkSearchResult, DocumentSearchRespone
from app.schemas.generation import GenerateQuestionsRequest, QuestionGenerationResponse
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.services.document_processor import extract_chunks
from app.services.chunk_embedding_service import embed_document_chunks
from app.services.retrieval_service import search_document_chunks
from app.services.question_generation_service import generate_document_questions


import uuid
import shutil

from fastapi import HTTPException, UploadFile, File


STORAGE_DIR = Path("storage/documents")
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

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
        file: UploadFile = File(...),
        db: Session = Depends(get_db),

):
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type",
        )

    document_id = uuid.uuid4()
    storage_path = STORAGE_DIR / f"{document_id}.pdf"

    try:
        with storage_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        if storage_path.stat().st_size == 0:
            storage_path.unlink()

            raise HTTPException(
                status_code = status.HTTP_400_BAD_REQUEST,
                detail = "File was empty",

            )
        document = Document(
            id=document_id,
            filename=file.filename,
            storage_path=str(storage_path)
        )
        db.add(document)
        db.commit()
        db.refresh(document)

        return document

    except Exception:
        db.rollback()

        if storage_path.exists():
            storage_path.unlink()

        raise




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

@router.post(
    "/{document_id}/process",
    response_model=DocumentProcessResponse
)
def process_document(
        document_id : uuid.UUID,
        db: Session = Depends(get_db),
):

    document = db.get(Document, document_id)

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    if document.status == "processed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT
            , detail="Document already processed"
        )

    existing_chunk = db.scalar(
        select(DocumentChunk.id)
        .where(DocumentChunk.document_id == document.id)
        .limit(1)
    )

    if existing_chunk is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Document already contains processed chunks"
        )


    document.status = "processing"
    db.commit()

    try:
        chunks = extract_chunks(document.storage_path)
        if not chunks:
            raise ValueError("No text could be extracted from the pdf")

        for chunk in chunks:
            document_chunk = DocumentChunk(
                document_id = document_id,
                chunk_index = chunk["chunk_index"],
                page_number = chunk["page_number"],
                content = chunk["content"],
            )
            db.add(document_chunk)

        document.status = "processed"
        db.commit()

        return DocumentProcessResponse(
            document_id = document_id,
            status = document.status,
            chunks_created=len(chunks),
        )

    except Exception:
        db.rollback()
        document.status = "failed"
        db.commit()
        raise

@router.post("/{document_id}/embed")
def embed_document(
    document_id : uuid.UUID,
     db: Session = Depends(get_db),
    ):

        document = db.get(Document, document_id)

        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )

        if document.status != "processed":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Document must be  processed before embedding can be generated"
            )

        embedded_count = embed_document_chunks(
            db = db,
            document_id = document.id,
        )

        return {
            "document_id": document.id,
            "embedded_created": embedded_count,
        }


@router.get(
    "/{document_id}/search",
    response_model=DocumentSearchRespone
)
def search_document(
        document_id : uuid.UUID,
        query: str,
        limit: int = 5,
        db: Session = Depends(get_db),

):
    document = db.get(Document, document_id)

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    results = search_document_chunks(
        db=db,
        document_id = document.id,
        query = query,
        limit = limit,
    )

    return DocumentSearchRespone(
        query = query,
        results = [
            ChunkSearchResult(
                chunk_index=chunk.chunk_index,
                page_number=chunk.page_number,
                content=chunk.content,
                distance=distance,
            )
            for chunk, distance in results
        ],
    )

@router.post(
    "/documents/{document_id}/generate-questions",
    response_model=QuestionGenerationResponse,
)
def generate_questions(
        document_id : uuid.UUID,
        request: GenerateQuestionsRequest,
        db : Session = Depends(get_db),
):
    return generate_document_questions(
        db=db,
        document_id = document_id,
        topic = request.topic,
        number_of_questions = request.number_of_questions,
    )










