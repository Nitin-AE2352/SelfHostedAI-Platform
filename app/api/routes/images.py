
import base64
import json
import os
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from threading import Lock

import torch
from dotenv import dotenv_values
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, ValidationError

from app.core.config import settings

router = APIRouter()
generation_lock = Lock()

env_values = dotenv_values(Path.cwd() / ".env")

IMAGE_MODEL_PATH = (
    os.getenv("IMAGE_MODEL_PATH")
    or env_values.get("IMAGE_MODEL_PATH")
    or settings.image_model_path
    or "C:/AI-Models/tiny-sd"
)


class ImageRequest(BaseModel):
    prompt: str = Field(min_length=3, max_length=1000)
    width: int = Field(default=512, ge=256, le=512)
    height: int = Field(default=512, ge=256, le=512)
    steps: int = Field(default=15, ge=1, le=30)


class ImageResponse(BaseModel):
    image_base64: str
    mime_type: str = "image/png"
    model: str


@lru_cache(maxsize=1)
def load_pipeline():
    """Local image model ko ek baar load karke reuse karo."""
    try:
        from diffusers import DiffusionPipeline

        model_path = Path(IMAGE_MODEL_PATH).expanduser().resolve()

        if not (model_path / "model_index.json").is_file():
            raise FileNotFoundError(
                f"Model configuration nahi mili: {model_path}"
            )

        pipeline = DiffusionPipeline.from_pretrained(
            str(model_path),
            torch_dtype=torch.float32,
            local_files_only=True,
        )

        device = "cuda" if torch.cuda.is_available() else "cpu"
        pipeline = pipeline.to(device)
        pipeline.set_progress_bar_config(disable=True)

        return pipeline, model_path.name

    except Exception as exc:
        raise RuntimeError(
            f"Image model load failed: {type(exc).__name__}: {exc}"
        ) from exc


@router.post("/images/generate", response_model=ImageResponse)
async def generate_image(request: Request):
    """JSON object aur double-encoded JSON string dono accept karo."""

    try:
        payload = await request.json()

        if isinstance(payload, str):
            payload = json.loads(payload)

        if not isinstance(payload, dict):
            raise HTTPException(
                status_code=422,
                detail="Request body valid JSON object hona chahiye.",
            )

        image_request = ImageRequest.model_validate(payload)

    except HTTPException:
        raise

    except (json.JSONDecodeError, UnicodeDecodeError):
        raise HTTPException(
            status_code=400,
            detail="Request body valid JSON nahi hai.",
        )

    except ValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=exc.errors(include_input=False),
        )

    prompt = image_request.prompt.strip()

    if len(prompt) < 3:
        raise HTTPException(
            status_code=422,
            detail="Prompt kam se kam 3 characters ka hona chahiye.",
        )

    try:
        with generation_lock:
            pipeline, model_name = load_pipeline()

            result = pipeline(
                prompt=prompt,
                negative_prompt=(
                    "blurry, low quality, distorted, malformed, "
                    "unwanted objects, duplicate objects, "
                    "text, watermark"
                ),
                width=image_request.width,
                height=image_request.height,
                num_inference_steps=image_request.steps,
                guidance_scale=7.5,
            )

            if not result.images:
                raise RuntimeError(
                    "Model ne koi image return nahi ki."
                )

            buffer = BytesIO()
            result.images[0].save(buffer, format="PNG")

        return ImageResponse(
            image_base64=base64.b64encode(
                buffer.getvalue()
            ).decode("ascii"),
            mime_type="image/png",
            model=model_name,
        )

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                f"Image generation failed: "
                f"{type(exc).__name__}: {exc}"
            ),
        ) from exc
