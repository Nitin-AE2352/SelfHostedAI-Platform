# Architecture Notes

## Initial request flow
Browser/client -> FastAPI -> Ollama local HTTP API -> response to client

## Planned expanded flow
Client -> API gateway/auth -> request validation/rate limits -> job queue where
needed -> LLM inference server -> response/status endpoint.

RAG flow:
file upload -> validation -> text extraction -> chunking -> embeddings -> vector
search -> retrieved context -> LLM -> answer with source metadata.

## Design principles
- Keep provider/model calls in `app/services/`.
- Keep request/response models in `app/schemas/`.
- Keep routes thin; put business logic in services.
- Keep credentials in environment variables, never committed source.
- Add tenant-aware authorization before exposing private documents.
- Benchmark before claiming 300 concurrent generation capacity.
