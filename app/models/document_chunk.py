import uuid
from datetime import datetime
from typing import List

from sqlalchemy import DateTime, ForeignKey, Integer, Text, func, UUID, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector
from app.db.base import Base

class DocumentChunk(Base):
    __tablename__ = 'document_chunk'

    __table_args__ = (
        UniqueConstraint(
            'document_id',
            'chunk_index',
            name= "uq_document_chunk_document_id_chunk_index",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,

    )

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('document.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )

    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    page_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    embedding: Mapped[List[float] | None] = mapped_column(
        Vector(384),
        nullable = True,
    )