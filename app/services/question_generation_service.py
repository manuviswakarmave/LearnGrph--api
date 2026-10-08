import uuid

from sqlalchemy.orm import Session

from app.services.retrieval_service import search_document_chunks
from app.services.llm_service import generate_questions
from app.schemas.generation import QuestionGenerationResponse


def generate_document_questions(
    db: Session,
    document_id: uuid.UUID,
    topic: str,
    number_of_questions: int = 3,
) -> QuestionGenerationResponse:

    # 1. Retrieve relevant chunks from PostgreSQL
    results = search_document_chunks(
        db=db,
        document_id=document_id,
        query=topic,
        limit=5,
    )

    if not results:
        return QuestionGenerationResponse(questions=[])

    # 2. Prepare context and collect valid source IDs
    context_parts = []
    allowed_chunk_ids = set()

    for chunk, distance in results:
        allowed_chunk_ids.add(chunk.id)

        context_parts.append(
            f"""
SOURCE CHUNK ID: {chunk.id}
PAGE NUMBER: {chunk.page_number}
CONTENT:
{chunk.content}
"""
        )

    # 3. Combine all retrieved chunks into one context
    context = "\n\n".join(context_parts)

    # 4. Call Qwen ONCE using the complete context
    response = generate_questions(
        context=context,
        number_of_questions=number_of_questions,
    )

    # 5. Validate generated source chunk IDs
    validated_questions = []

    for question in response.questions:
        if all(
            chunk_id in allowed_chunk_ids
            for chunk_id in question.source_chunk_ids
        ):
            validated_questions.append(question)

    # 6. Return only questions with valid source references
    return QuestionGenerationResponse(
        questions=validated_questions
    )