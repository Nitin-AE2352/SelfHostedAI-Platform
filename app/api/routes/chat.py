import re
from difflib import SequenceMatcher
from fastapi import APIRouter, HTTPException
from requests import RequestException

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.ollama_service import generate_answer
from app.services.document_service import search_documents

router = APIRouter()

STOP_WORDS = {
    "a", "an", "the", "is", "are", "was", "were",
    "what", "when", "where", "which", "who", "how", "why",
    "do", "does", "did", "in", "on", "at", "to", "for",
    "of", "and", "or", "my", "me", "i", "you", "your",
    "hai", "hain", "ka", "ki", "ke", "ko", "kya", "kab",
    "kahan", "kaise", "mera", "meri", "mere", "batao",
    "please", "tell", "about"
}


def get_terms(text: str) -> set[str]:
    words = re.findall(r"[a-zA-Z0-9]+", text.lower())
    return {
        word for word in words
        if len(word) > 1 and word not in STOP_WORDS
    }


def rerank_documents(question: str, matches: list) -> list:
    """Rank document chunks using similarity, keywords and question intent."""
    question_terms = get_terms(question)
    question_lower = question.lower()

    intent_terms = []
    if any(term in question_lower for term in [
        "stipend", "salary", "payment", "compensation", "milega", "paise"
    ]):
        intent_terms = ["stipend", "eligible", "monthly stipend"]
    elif any(term in question_lower for term in [
        "kab", "when", "start", "end", "date", "duration"
    ]):
        intent_terms = [
            "commence", "end on", "12th october 2026", "12th december 2026"
        ]
    elif any(term in question_lower for term in [
        "confidentiality", "non-disclosure", "agreement", "nda", "sign"
    ]):
        intent_terms = [
            "confidentiality", "non-disclosure", "effective date"
        ]

    ranked = []

    for position, item in enumerate(matches):
        text = item.get("text", "").strip()
        if not text:
            continue

        text_lower = text.lower()
        normalized = " ".join(re.findall(r"[a-z0-9]+", text_lower))
        filename = str(item.get("filename", "")).lower()
        base_name = re.sub(r"\.[^.]+$", "", filename)

        document_terms = get_terms(text)
        coverage = (
            len(question_terms & document_terms) / len(question_terms)
            if question_terms else 0.0
        )

        distance = item.get("distance")
        similarity = 0.0
        if isinstance(distance, (int, float)):
            similarity = max(0.0, min(1.0, 1.0 - float(distance)))

        intent_score = (
            sum(1 for term in intent_terms if term in text_lower)
            / len(intent_terms)
            if intent_terms else 0.0
        )

        rank_score = 1.0 / (position + 1)
        score = (
            0.40 * similarity
            + 0.25 * coverage
            + 0.10 * rank_score
            + 0.25 * intent_score
        )

        ranked.append({
            "item": item,
            "score": score,
            "position": position,
            "base_name": base_name,
            "normalized": normalized,
        })

    ranked.sort(key=lambda row: (-row["score"], row["position"]))

    selected = []
    for entry in ranked:
        duplicate = False

        for previous in selected:
            if (
                entry["base_name"]
                and entry["base_name"] == previous["base_name"]
                and entry["normalized"]
                and previous["normalized"]
            ):
                ratio = __import__("difflib").SequenceMatcher(
                    None,
                    entry["normalized"],
                    previous["normalized"],
                ).ratio()

                if ratio >= 0.82:
                    duplicate = True
                    break

        if not duplicate:
            selected.append(entry)

        if len(selected) >= 4:
            break

    return [entry["item"] for entry in selected]


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        question = request.message.strip()

        if not question:
            raise HTTPException(
                status_code=400,
                detail="Please enter a question."
            )

        # Retrieve more candidates, then rerank them.
        candidates = search_documents(query=question, top_k=12)
        matches = rerank_documents(question, candidates)

        if not matches:
            return ChatResponse(
                answer=(
                    "Uploaded documents mein relevant information nahi mili. "
                    "Question ko rephrase karein ya relevant document upload karein."
                ),
                model="local Ollama model",
                source="No relevant document found",
            )

        context_parts = []
        citations = []

        for item in matches:
            text = item.get("text", "").strip()
            filename = item.get("filename", "Unknown document")
            location = item.get("source_location", "Location unavailable")
            chunk_index = item.get("chunk_index", "?")

            if not text:
                continue

            context_parts.append(
                f"[Source: {filename} | {location} | Chunk {chunk_index}]\n"
                f"{text}"
            )

            citation = f"{filename} — {location}"
            if citation not in citations:
                citations.append(citation)

        if not context_parts:
            return ChatResponse(
                answer="Relevant document text nahi mil paya.",
                model="local Ollama model",
                source="No usable document text",
            )

        context = "\n\n---\n\n".join(context_parts)

        prompt = f"""
You are a careful document question-answering assistant.

Answer the user's question using the supplied document excerpts.

Rules:
- Answer in the same language as the user's question.
- Use only facts supported by the excerpts for document-specific questions.
- Never invent dates, amounts, names, policies or missing details.
- If the excerpts do not contain the answer, explicitly say so.
- Do not confuse a source citation with proof that the answer is correct.
- Keep the answer concise and directly answer the question.

DOCUMENT EXCERPTS:
{context}

USER QUESTION:
{question}

ANSWER:
"""

        answer = generate_answer(prompt).strip()

        if not answer:
            answer = (
                "Reliable answer generate nahi hua. "
                "Please question ko dobara try karein."
            )

        answer += "\n\nSources:\n" + "\n".join(
            f"- {citation}" for citation in citations
        )

        return ChatResponse(
            answer=answer,
            model="local Ollama model",
            source="; ".join(citations),
        )

    except HTTPException:
        raise
    except RequestException as exc:
        raise HTTPException(
            status_code=503,
            detail="Ollama ya embedding service unavailable hai."
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

