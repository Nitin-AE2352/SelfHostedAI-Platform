import requests

from app.core.config import settings


def check_ollama() -> dict:
    url = f"{settings.ollama_base_url.rstrip('/')}/api/tags"

    try:
        response = requests.get(
            url,
            timeout=min(settings.request_timeout_seconds, 10),
        )
        response.raise_for_status()
        return {"reachable": True, "detail": "Ollama API responded"}
    except requests.RequestException as exc:
        return {"reachable": False, "detail": str(exc)}


def generate_answer(message: str) -> str:
    url = f"{settings.ollama_base_url.rstrip('/')}/api/generate"

    payload = {
        "model": settings.ollama_chat_model,
        "prompt": message,
        "stream": False,
        "keep_alive": "30m",
        "options": {
            "num_predict": 80,
            "num_ctx": 1536,
            "temperature": 0.1,
        },
    }

    response = requests.post(
        url,
        json=payload,
        timeout=settings.request_timeout_seconds,
    )
    response.raise_for_status()

    data = response.json()
    answer = data.get("response", "").strip()

    if not answer:
        raise RuntimeError("Ollama returned an empty answer.")

    return answer
