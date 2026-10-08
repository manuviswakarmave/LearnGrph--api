import httpx


from app.core.config import settings
from app.schemas.generation import QuestionGenerationResponse

def generate_questions(
        context: str,
        number_of_questions: int = 3,
)-> QuestionGenerationResponse:

    prompt = f"""
    You are a university-level educational question generator.
    
    LANGUAGE REQUIREMENTS:
    - You MUST generate all questions in English.
    - You MUST generate all answers in English.
    - All concept names must be written in English.
    - Do not generate Chinese, Hindi, German, or any other language.
    - Preserve mathematical notation and equations exactly as they appear.
    - Even if the source material contains another language, generate the output in English.

    Your task is to generate exactly {number_of_questions} questions
    based on the provided lecture material.

    The material may be short. Even a single paragraph can contain
    enough information to generate multiple conceptual questions.

    For each question:
    1. Write a clear question based on the lecture material.
    2. Provide an accurate answer supported by that material.
    3. Assign a difficulty: easy, medium, or hard.
    4. Identify the relevant concepts.
    5. Include the exact SOURCE CHUNK ID supporting the answer.

    IMPORTANT RULES:
    - Use ONLY the provided lecture material.
    - Do not invent facts or source chunk IDs.
    - Generate exactly {number_of_questions} questions if the material
      supports that many distinct questions.
    - If fewer distinct questions are supported, return fewer.
    - Return an empty list ONLY when the material contains no information
      relevant to generating educational questions.
    - Return valid JSON matching the requested schema.

    LECTURE MATERIAL:
    {context}
    """

    payload = {
        "model" : settings.ollama_model,
        "messages" : [
            {
                "role" : "user",
                "content" : prompt,
            }
        ],
        "stream" : False,
        "format": QuestionGenerationResponse.model_json_schema(),
        "options": {
            "temperature": 0.2,

        },

    }

    with httpx. Client(timeout=180.0) as client:
        response = client.post(
            f"{settings.ollama_base_url}/api/chat",
            json=payload,
        )

        response.raise_for_status()

    data = response.json()

    content = data.get("message", {}).get("content", "")

    if not content.strip():
        raise ValueError(
            "Ollama returned empty content. "
            f"Done reason: {data.get('done_reason')}"
        )

    return QuestionGenerationResponse.model_validate_json(content)
