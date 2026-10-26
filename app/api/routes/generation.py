
import os

import requests
from dotenv import dotenv_values
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()

env_values = dotenv_values(".env")

OLLAMA_BASE_URL = (
    os.getenv("OLLAMA_BASE_URL")
    or env_values.get("OLLAMA_BASE_URL")
    or "http://localhost:11434"
).rstrip("/")

OLLAMA_CHAT_MODEL = (
    os.getenv("OLLAMA_CHAT_MODEL")
    or env_values.get("OLLAMA_CHAT_MODEL")
    or "llama3.2:3b"
)


class GenerationRequest(BaseModel):
    prompt: str = Field(min_length=3, max_length=10000)
    language: str = Field(default="English", max_length=50)
    tone: str = Field(default="Professional", max_length=50)
    length: str = Field(default="Medium", max_length=30)
    complexity: str = Field(default="Intermediate", max_length=30)
    output_format: str = Field(default="Markdown", max_length=30)


class GenerationResponse(BaseModel):
    text: str
    model: str


@router.post("/generate", response_model=GenerationResponse)
def generate_content(request: GenerationRequest):
    prompt = request.prompt.strip()

    if len(prompt) < 3:
        raise HTTPException(
            status_code=422,
            detail="Prompt must contain at least 3 characters.",
        )

    # Normalize format names received from the frontend.
    raw_format = request.output_format.strip().lower()
    raw_format = raw_format.replace("_", " ").replace("-", " ")

    format_map = {
        "markdown": "Markdown",
        "json": "JSON",
        "plain text": "Plain text",
        "text": "Plain text",
    }

    output_format = format_map.get(raw_format)

    if output_format is None:
        raise HTTPException(
            status_code=422,
            detail="Output format must be Markdown, JSON, or Plain text.",
        )

    system_prompt = f"""
You are a helpful content-generation assistant running locally.

Follow these requirements:
- Language: {request.language}
- Tone: {request.tone}
- Length: {request.length}
- Complexity: {request.complexity}
- Output format: {output_format}

Rules:
- Follow the user's requested task.
- Do not invent factual information or claim unsupported facts.
- Use clear, relevant headings when appropriate.
- If information is missing, state the limitation.
- If JSON is requested, return valid JSON without Markdown fences.
- If Plain text is requested, avoid Markdown formatting.
- Do not claim to have accessed external services.
""".strip()

    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json={
                "model": OLLAMA_CHAT_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                "stream": False,
                "options": {
                    "temperature": 0.3,
                },
            },
            timeout=180,
        )

        response.raise_for_status()
        data = response.json()

        generated_text = (
            data.get("message", {}).get("content", "").strip()
        )

        if not generated_text:
            raise HTTPException(
                status_code=502,
                detail="The local model returned an empty response.",
            )

        return GenerationResponse(
            text=generated_text,
            model=data.get("model", OLLAMA_CHAT_MODEL),
        )

    except HTTPException:
        raise

    except requests.Timeout as exc:
        raise HTTPException(
            status_code=504,
            detail="Text generation timed out. Try a shorter prompt.",
        ) from exc

    except requests.RequestException as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Local Ollama service is unavailable. "
                "Check that Ollama is running and the model is installed."
            ),
        ) from exc

    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=502,
            detail="The local model returned an invalid response.",
        ) from exc
