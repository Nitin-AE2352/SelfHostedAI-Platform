
import os
import uuid
from pathlib import Path
from threading import Lock

import torch
from diffusers import StableDiffusionPipeline


# Model aur output folder ki settings .env se read hongi.
MODEL_PATH = Path(
    os.getenv("IMAGE_MODEL_PATH", "C:/AI-Models/tiny-sd")
)
OUTPUT_DIR = Path(
    os.getenv("IMAGE_OUTPUT_DIR", "data/generated_images")
)

_pipeline = None
_pipeline_lock = Lock()


def load_image_model():
    """AI image model ko load karke reuse karna."""
    global _pipeline

    with _pipeline_lock:
        if _pipeline is not None:
            return _pipeline

        if not (MODEL_PATH / "model_index.json").is_file():
            raise FileNotFoundError(
                f"Model nahi mila: {MODEL_PATH}. "
                "Pehle model download karo."
            )

        device = "cuda" if torch.cuda.is_available() else "cpu"

        _pipeline = StableDiffusionPipeline.from_pretrained(
            str(MODEL_PATH),
            torch_dtype=torch.float32,
            local_files_only=True,
        )

        _pipeline = _pipeline.to(device)
        return _pipeline


def generate_image(prompt: str) -> Path:
    """Prompt se image generate karke PNG file save karna."""
    prompt = prompt.strip()

    if not prompt:
        raise ValueError("Image prompt khaali nahi ho sakta.")

    if len(prompt) > 1000:
        raise ValueError("Prompt 1000 characters se chhota rakho.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    pipeline = load_image_model()

    result = pipeline(
        prompt=prompt,
        num_inference_steps=15,
        guidance_scale=7.5,
        height=512,
        width=512,
    )

    image = result.images[0]
    image_path = OUTPUT_DIR / f"{uuid.uuid4().hex}.png"
    image.save(image_path)

    return image_path
