
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.services.document_service import ingest_document, search_documents
from app.services.rag_service import answer_from_documents

router = APIRouter()


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)
    top_k: int = Field(default=4, ge=1, le=10)


class AnswerRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)
    top_k: int = Field(default=4, ge=1, le=10)


@router.post("/documents/upload")
async def upload_documents(
    files: Annotated[
        list[UploadFile],
        File(description="Select PDF, DOCX, PPTX, or TXT files"),
    ],
):
    if len(files) > 10:
        raise HTTPException(
            status_code=400,
            detail="Maximum 10 files per upload request.",
        )

    results = []

    for file in files:
        filename = file.filename or "unknown"

        try:
            content = await file.read()
            result = ingest_document(filename, content)
            results.append(result)

        except ValueError as exc:
            results.append({
                "filename": filename,
                "status": "failed",
                "error": str(exc),
            })

        except Exception:
            results.append({
                "filename": filename,
                "status": "failed",
                "error": (
                    "Document processing failed. "
                    "Check the backend terminal for details."
                ),
            })

        finally:
            await file.close()

    return {
        "message": "Document upload processing finished.",
        "results": results,
    }


@router.post("/documents/search")
def search_uploaded_documents(request: SearchRequest):
    try:
        matches = search_documents(
            query=request.query,
            top_k=request.top_k,
        )

        return {
            "query": request.query,
            "count": len(matches),
            "results": matches,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Document search failed. Check Ollama and "
                "the embedding model."
            ),
        ) from exc


@router.post("/documents/answer")
def answer_from_uploaded_documents(request: AnswerRequest):
    try:
        result = answer_from_documents(
            question=request.query,
            top_k=request.top_k,
        )

        return {
            "query": request.query,
            "answer": result["answer"],
            "sources": result["sources"],
            "count": len(result["matches"]),
            "results": result["matches"],
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Document answer generation failed. Check Ollama "
                "and the embedding model."
            ),
        ) from exc
