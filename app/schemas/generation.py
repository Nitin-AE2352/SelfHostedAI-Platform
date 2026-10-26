
from typing import Literal

from pydantic import BaseModel, Field


class GenerationRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=12000)
    language: str = Field(default="English", max_length=50)
    tone: str = Field(default="Professional", max_length=50)
    length: Literal["short", "medium", "long"] = "medium"
    complexity: Literal["simple", "intermediate", "advanced"] = "intermediate"
    output_format: Literal["text", "markdown", "json"] = "markdown"


class GenerationResponse(BaseModel):
    text: str
    model: str
