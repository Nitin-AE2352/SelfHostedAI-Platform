from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.api.routes import (
    auth,
    chat,
    health,
    documents,
    generation,
    questions,
    images,
)

# Project folders
PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description=(
        "Self-hosted Generative AI platform with local LLM, "
        "RAG, document Q&A, text generation, question generation, "
        "image generation, and authentication."
    ),
)

# Allow local frontend development servers.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:8010",
        "http://127.0.0.1:8010",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health routes
app.include_router(
    health.router,
    tags=["Health"],
)

# Authentication routes
app.include_router(
    auth.router,
    prefix="/api/v1/auth",
    tags=["Authentication"],
)

# Chat and RAG routes
app.include_router(
    chat.router,
    prefix="/api/v1",
    tags=["Chat"],
)

# Document upload and search routes
app.include_router(
    documents.router,
    prefix="/api/v1",
    tags=["Documents"],
)

# Text generation routes
app.include_router(
    generation.router,
    prefix="/api/v1",
    tags=["Generation"],
)

# Question generation routes
app.include_router(
    questions.router,
    prefix="/api/v1",
    tags=["Question Generation"],
)

# Image generation routes
app.include_router(
    images.router,
    prefix="/api/v1",
    tags=["Image Generation"],
)

# Serve frontend CSS.
css_dir = FRONTEND_DIR / "css"

if css_dir.is_dir():
    app.mount(
        "/css",
        StaticFiles(directory=str(css_dir)),
        name="frontend-css",
    )

# Serve frontend JavaScript.
js_dir = FRONTEND_DIR / "js"

if js_dir.is_dir():
    app.mount(
        "/js",
        StaticFiles(directory=str(js_dir)),
        name="frontend-js",
    )


def custom_openapi():
    """Customize Swagger schema for file upload selectors."""

    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    paths = schema.get("paths", {})
    components = schema.setdefault("components", {})
    schemas = components.setdefault("schemas", {})

    for path_item in paths.values():
        for operation in path_item.values():
            if not isinstance(operation, dict):
                continue

            request_body = operation.get("requestBody", {})
            content = request_body.get("content", {})
            multipart = content.get("multipart/form-data", {})
            body_schema = multipart.get("schema", {})

            # Resolve referenced request-body schemas.
            ref = body_schema.get("$ref")

            if ref and ref.startswith("#/components/schemas/"):
                schema_name = ref.rsplit("/", 1)[-1]
                body_schema = schemas.get(schema_name, {})

            properties = body_schema.get("properties", {})

            # Mark uploaded files as binary in Swagger UI.
            for prop in properties.values():
                if prop.get("type") == "array":
                    item_schema = prop.get("items", {})

                    if (
                        item_schema.get("type") == "string"
                        and item_schema.get("contentMediaType")
                        == "application/octet-stream"
                    ):
                        item_schema["format"] = "binary"
                        item_schema.pop("contentMediaType", None)

    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi


# Browser frontend
@app.get("/favicon.ico", include_in_schema=False)
@app.get("/favicon.svg", include_in_schema=False)
def favicon():
    return FileResponse(
        FRONTEND_DIR / "favicon.svg",
        media_type="image/svg+xml",
    )


@app.get("/", include_in_schema=False)
def root():
    index_file = FRONTEND_DIR / "index.html"

    if not index_file.is_file():
        return {
            "message": "Frontend index.html not found.",
            "expected_path": str(index_file),
            "docs": "/docs",
        }

    return FileResponse(index_file)


# API information
@app.get("/api-info", tags=["Health"])
def api_info():
    return {
        "message": "Welcome to the Self-Hosted AI Platform API",
        "version": app.version,
        "docs": "/docs",
        "openapi": "/openapi.json",
        "health": "/health",
        "frontend": "/",
        "authentication": {
            "register": "/api/v1/auth/register",
            "login": "/api/v1/auth/login",
            "current_user": "/api/v1/auth/me",
        },
        "chat": "/api/v1/chat",
        "documents": {
            "upload": "/api/v1/documents/upload",
            "search": "/api/v1/documents/search",
        },
        "text_generation": "/api/v1/generate",
        "question_generation": "/api/v1/questions/generate",
        "image_generation": "/api/v1/images/generate",
    }
