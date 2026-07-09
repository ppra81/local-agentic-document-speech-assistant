from __future__ import annotations

import re

from fastapi import APIRouter, File, UploadFile

from assistant.api.schemas import IngestRequest, SearchRequest
from assistant.config import settings
from assistant.rag.chunker import chunk_text
from assistant.rag.retriever import Retriever
from assistant.utils.files import read_text_file
from assistant.utils.ids import stable_file_id

router = APIRouter(prefix="/documents", tags=["documents"])


def extract_text_from_upload_bytes(content: bytes, filename: str) -> str:
    suffix = filename.lower().rsplit(".", 1)[-1] if "." in filename else "txt"
    if suffix == "pdf":
        parsed = _extract_pdf_with_pymupdf(content)
        if parsed.strip():
            return parsed
        raw = content.decode("latin-1", errors="ignore")
        simple_lines = re.findall(r"\((.*?)\)\s*Tj", raw, flags=re.DOTALL)
        array_lines = re.findall(r"\[(.*?)\]\s*TJ", raw, flags=re.DOTALL)
        for array in array_lines:
            simple_lines.extend(re.findall(r"\((.*?)\)", array, flags=re.DOTALL))
        if simple_lines:
            return "\n".join(_decode_pdf_text(line) for line in simple_lines)
        return "This PDF does not expose embedded plain text in the local demo. Use a text file or connect a real OCR/PDF adapter."
    return content.decode("utf-8", errors="replace")


def _extract_pdf_with_pymupdf(content: bytes) -> str:
    try:
        import fitz  # type: ignore
    except Exception:
        return ""
    try:
        with fitz.open(stream=content, filetype="pdf") as document:
            return "\n".join(page.get_text("text") for page in document).strip()
    except Exception:
        return ""


def _decode_pdf_text(value: str) -> str:
    return (
        value.replace(r"\(", "(")
        .replace(r"\)", ")")
        .replace(r"\\", "\\")
        .replace(r"\n", "\n")
        .replace(r"\r", "\r")
        .replace(r"\t", "\t")
    )


@router.post("/ingest")
def ingest_document(payload: IngestRequest) -> dict:
    if payload.text is not None:
        text = payload.text
        source = payload.source_file
    elif payload.file_path:
        text = read_text_file(payload.file_path)
        source = payload.file_path
    else:
        raise ValueError("file_path or text is required")
    document_id = stable_file_id(source)
    chunks = chunk_text(text, document_id, source, settings.chunk_size, settings.chunk_overlap)
    Retriever().index(document_id, chunks)
    return {"document_id": document_id, "chunks": [c.model_dump() for c in chunks]}


@router.post("/search")
def search_documents(payload: SearchRequest) -> dict:
    return {"results": Retriever().search(payload.query, payload.top_k)}


@router.post("/extract-text")
async def extract_text(file: UploadFile = File(...)) -> dict:
    content = await file.read()
    text = extract_text_from_upload_bytes(content, file.filename or "uploaded.txt")
    return {"filename": file.filename, "text": text}
