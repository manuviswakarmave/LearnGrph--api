from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document_chunk import DocumentChunk
from app.services.embedding_service import generate_embedding

def search_document_chunks(
        db: Session,
        document_id,
        query: str,
        limit: int = 5,
):
    query_embedding = generate_embedding(query)

    distance = DocumentChunk.embedding.cosine_distance(query_embedding)

    statement = (
        select(
            DocumentChunk,
            distance.label("distance"),
        )
        .where(DocumentChunk.document_id == document_id)
        .where(DocumentChunk.embedding.isnot(None))
        .order_by(distance)
        .limit(limit)
    )

    results = db.execute(statement).all()

    return results