from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "Self-Hosted AI Platform"
    app_env: str = "development"
    host: str = "127.0.0.1"
    port: int = 8000

    ollama_base_url: str = "http://localhost:11434"
    ollama_chat_model: str = "llama3.2:3b"
    ollama_embedding_model: str = "nomic-embed-text"
    request_timeout_seconds: int = 120

    max_upload_mb: int = 20
    database_path: str = "data/platform.db"
    chroma_path: str = "data/chroma_db"

    jwt_secret: str = "CHANGE_THIS_SECRET"
    access_token_minutes: int = 60

    image_model_path: str = "C:/AI-Models/tiny-sd"
    image_output_dir: str = "data/generated_images"

    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()