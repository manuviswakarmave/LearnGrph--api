import uuid

from enum import Enum
from pydantic import BaseModel, Field

class QuestionDifficulty(str,Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class GeneratedQuestion(BaseModel):
    question: str = Field(
        min_length= 10,
        max_length=1000,
    )

    answer: str = Field(
        min_length= 10,
        max_length=3000,
    )

    difficulty: QuestionDifficulty

    concepts: list[str] = Field(
        min_length = 1,
        max_length=10,
    )

    source_chunk_ids: list[uuid.UUID] = Field(
        min_length=1
    )

class QuestionGenerationResponse(BaseModel):
    questions: list[GeneratedQuestion]


class GenerateQuestionsRequest(BaseModel):
    topic: str = Field(min_length = 3, max_length = 200)
    number_of_questions: int = Field(default= 3 , ge =1 , le=10)