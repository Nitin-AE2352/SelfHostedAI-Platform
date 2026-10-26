
from datetime import datetime, timezone

import requests
from fastapi import APIRouter

from app.core.config import settings

router = APIRouter()


@router.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "Self-Hosted AI Platform",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/health/ready")
def readiness_check():
    base_url = settings.ollama_base_url.rstrip("/")

    try:
        response = requests.get(
            f"{base_url}/api/tags",
            timeout=5,
        )
        response.raise_for_status()
        data = response.json()

        models = [
            item.get("name")
            for item in data.get("models", [])
            if item.get("name")
        ]

        return {
            "status": "ready",
            "ollama": "connected",
            "installed_models": models,
        }

    except (requests.RequestException, ValueError):
        return {
            "status": "degraded",
            "ollama": "unavailable",
            "installed_models": [],
        }
