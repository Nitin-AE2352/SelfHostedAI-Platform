
import os

import requests
from dotenv import dotenv_values
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()

env = dotenv_values(".env")

OLLAMA_URL = (
    os.getenv("OLLAMA_BASE_URL")
    or env.get("OLLAMA_BASE_URL")
    or "http://localhost:11434"
).rstrip("/")

MODEL = (
    os.getenv("OLLAMA_CHAT_MODEL")
    or env.get("OLLAMA_CHAT_MODEL")
    or "llama3.2:3b"
)


class QuestionRequest(BaseModel):
    source_text: str = Field(min_length=10, max_length=15000)
    question_type: str = Field(default="MCQ", max_length=50)
    count: int = Field(default=5, ge=1, le=20)
    difficulty: str = Field(default="Medium", max_length=30)
    language: str = Field(default="English", max_length=50)
    include_answers: bool = True
    include_topics: bool = False


class QuestionResponse(BaseModel):
    text: str
    model: str


@router.post("/questions/generate", response_model=QuestionResponse)
def generate_questions(request: QuestionRequest):
    allowed_types = {
        "MCQ",
        "Multiple Choice",
        "True/False",
        "Fill in the Blank",
        "Short Answer",
        "Long Answer",
        "Scenario-Based",
    }

    if request.question_type not in allowed_types:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported question type: {request.question_type}",
        )

    answer_rule = (
        "Include the correct answer and a brief explanation."
        if request.include_answers
        else "Do not include answers or explanations."
    )

    topic_rule = (
        "Group questions under relevant topic headings."
        if request.include_topics
        else "Do not add separate topic headings."
    )

    system_prompt = f"""
You are a learning assessment assistant.

Generate exactly {request.count} questions using only the supplied source.
Question type: {request.question_type}
Difficulty: {request.difficulty}
Language: {request.language}

Requirements:
- {answer_rule}
- {topic_rule}
- Questions must be clear and relevant to the source.
- Do not invent facts that are not supported by the source.
- For MCQs, provide four options labelled A, B, C and D.
- For True/False, make each statement unambiguous.
- Number every question.
- Return readable Markdown.
- If the source does not contain enough information, state this clearly.
""".strip()

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": MODEL,
                "stream": False,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": (
                            "Create the requested questions from this material:\n\n"
                            + request.source_text
                        ),
                    },
                ],
                "options": {"temperature": 0.3},
            },
            timeout=180,
        )
        response.raise_for_status()
        data = response.json()
        text = data.get("message", {}).get("content", "").strip()

        if not text:
            raise HTTPException(
                status_code=502,
                detail="The local model returned an empty response.",
            )

        return QuestionResponse(
            text=text,
            model=data.get("model", MODEL),
        )

    except HTTPException:
        raise
    except requests.Timeout as exc:
        raise HTTPException(
            status_code=504,
            detail="Question generation timed out. Try less source text.",
        ) from exc
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=503,
            detail="Ollama is unavailable. Check the local model service.",
        ) from exc
