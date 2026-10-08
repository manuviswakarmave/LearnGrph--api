from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document_chunk import DocumentChunk
from app.services.embedding_service import generate_embedding

def embed_document_chunks(
        db: Session,
        document_id,
)->int:

    chunks = db.scalars(
        select(DocumentChunk)
        .where(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index)
    ).all()

    embedded_count = 0

    for chunk in chunks:
        if chunk.embedding is not None:
            continue

        chunk.embedding = generate_embedding(chunk.content)
        embedded_count += 1

    db.commit()
    return embedded_count