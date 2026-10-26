# Self-Hosted AI Platform (Starter)

A beginner-friendly starter scaffold for a company-hosted Generative AI platform.
The first milestone is a FastAPI backend connected to a local Ollama model. RAG,
image generation, authentication, background jobs, and load testing are planned
as separate milestones rather than being falsely marked as complete.

## Prerequisites
- Windows 10/11 (PowerShell), Python 3.12
- Ollama installed: https://ollama.com/download
- Git (optional)

## 1. Create and activate a virtual environment
Open PowerShell in this folder:

```powershell
py -3.12 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 2. Configure environment
```powershell
Copy-Item .env.example .env
```
Edit `.env` if your Ollama URL or model name differs.

## 3. Start Ollama and download a model
In a terminal:
```powershell
ollama pull llama3.2:3b
ollama serve
```
If Ollama is already running as a Windows app/service, you usually do not need
to run `ollama serve` again. Keep the model name in `.env` aligned with the
model you pulled.

## 4. Run the API
From the project root, with `.venv` activated:
```powershell
uvicorn app.main:app --reload
```
Open:
- API health: http://127.0.0.1:8000/health
- Interactive API docs: http://127.0.0.1:8000/docs

## Current starter endpoints
- `GET /health` — checks that the API is running.
- `POST /api/v1/chat` — sends a prompt to the local Ollama model.

Example request body:
```json
{
  "message": "Explain RAG in simple Hinglish",
  "stream": false
}
```

## Planned milestones
1. Local model API (current scaffold)
2. Document upload + text extraction
3. Embeddings + vector search + RAG
4. Authentication, authorization, and tenant isolation
5. Background jobs and queue
6. Image-generation service
7. Load testing (10 → 25 → 50 → 100 → 300 simulated clients)
8. Monitoring, security review, deployment documentation

## Important
This starter does **not** prove capacity for 300 concurrent generations. That
requires choosing a model/hardware configuration and measuring latency,
throughput, queue time, errors, GPU utilization, and VRAM under load.
Do not put secrets in source control. `.env` is excluded by `.gitignore`.
