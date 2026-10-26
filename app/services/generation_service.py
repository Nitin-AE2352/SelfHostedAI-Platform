
from app.core.config import settings
from app.services.ollama_service import generate_answer


def generate_content(
    prompt: str,
    language: str = "English",
    tone: str = "Professional",
    length: str = "medium",
    complexity: str = "intermediate",
    output_format: str = "markdown",
) -> str:
    length_instructions = {
        "short": "Keep the response concise.",
        "medium": "Provide a moderately detailed response.",
        "long": "Provide a detailed, well-structured response.",
    }

    complexity_instructions = {
        "simple": "Use simple, beginner-friendly language.",
        "intermediate": "Use clear language with useful details.",
        "advanced": "Include advanced concepts and technical detail.",
    }

    format_instructions = {
        "text": "Return plain text without Markdown formatting.",
        "markdown": "Use appropriate Markdown headings and lists.",
        "json": (
            "Return only valid JSON. Do not include Markdown code fences. "
            "If the requested content cannot naturally be represented as "
            "JSON, use a JSON object with a suitable content field."
        ),
    }

    full_prompt = f"""
You are a helpful local AI assistant.

Task:
{prompt}

Requirements:
- Language: {language}
- Tone: {tone}
- Length: {length_instructions[length]}
- Complexity: {complexity_instructions[complexity]}
- Output format: {format_instructions[output_format]}

Follow the requested language, tone, length, complexity and format.
Return the requested content directly.
"""

    return generate_answer(full_prompt)
