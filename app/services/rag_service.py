
from app.services.document_service import search_documents
from app.services.ollama_service import generate_answer


def answer_from_documents(question: str, top_k: int = 4) -> dict:
    """Search documents and generate an answer from retrieved content."""
    matches = search_documents(query=question, top_k=top_k)

    context_parts = []
    citations = []

    for item in matches:
        content = (item.get("text") or "").strip()

        if not content:
            continue

        filename = item.get("filename", "Unknown document")
        location = item.get("source_location", "Location unavailable")
        chunk_index = item.get("chunk_index", "?")

        context_parts.append(
            f"[Source: {filename} | {location} | Chunk {chunk_index}]\n"
            f"{content}"
        )

        citation = f"{filename} — {location}"

        if citation not in citations:
            citations.append(citation)

    if not context_parts:
        return {
            "answer": (
                "Uploaded documents mein is question ke liye relevant "
                "information nahi mili. Relevant document upload karein "
                "ya query badal kar try karein."
            ),
            "sources": [],
            "matches": [],
        }

    context = "\n\n---\n\n".join(context_parts)

    prompt = f"""
You are a careful company-document assistant.

Answer the question using only the supplied document context.

Rules:
- Reply in the same language as the user's question.
- Do not invent facts, dates, amounts, or policies.
- If the context does not answer the question, say so clearly.
- Keep the answer concise.
- Do not invent page numbers or citations.

DOCUMENT CONTEXT:
{context}

USER QUESTION:
{question}

ANSWER:
""".strip()

    answer = generate_answer(prompt).strip()

    return {
        "answer": answer,
        "sources": citations,
        "matches": matches,
    }
