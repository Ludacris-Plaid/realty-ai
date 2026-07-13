import uuid
import os
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from .db import engine

router = APIRouter()

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "uploads", "documents")
os.makedirs(UPLOAD_DIR, exist_ok=True)

DEFAULT_AGENT_ID = "b2c3d4e5-f6a7-8901-bcde-f12345678901"


def _row_to_dict(r):
    doc = {
        "id": str(r[0]),
        "agent_id": str(r[1]) if r[1] else None,
        "property_id": str(r[2]) if r[2] else None,
        "client_id": str(r[3]) if r[3] else None,
        "filename": r[4],
        "file_path": r[5],
        "file_size_bytes": r[6],
        "content_type": r[7],
        "category": r[8],
        "title": r[9],
        "description": r[10],
        "extracted_text": r[11],
        "vector_embedding_id": r[12],
        "created_at": r[13].isoformat() if r[13] else None,
        "updated_at": r[14].isoformat() if r[14] else None,
    }
    return doc


_COLUMNS = """
    id, agent_id, property_id, client_id, filename, file_path,
    file_size_bytes, content_type, category, title, description,
    extracted_text, vector_embedding_id, created_at, updated_at
"""


@router.get("/")
def list_documents(property_id: Optional[str] = None, category: Optional[str] = None):
    query = f"SELECT {_COLUMNS} FROM documents WHERE 1=1"
    params = {}
    if property_id:
        query += " AND property_id = :property_id"
        params["property_id"] = property_id
    if category:
        query += " AND category = :category"
        params["category"] = category
    query += " ORDER BY created_at DESC"

    with Session(engine) as session:
        rows = session.execute(text(query), params).fetchall()

    return {"documents": [_row_to_dict(r) for r in rows], "total": len(rows)}


@router.get("/{doc_id}")
def get_document(doc_id: str):
    with Session(engine) as session:
        row = session.execute(
            text(f"SELECT {_COLUMNS} FROM documents WHERE id = :id"),
            {"id": doc_id},
        ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Document not found")
    return _row_to_dict(row)


@router.post("/upload", status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    property_id: Optional[str] = Form(None),
    client_id: Optional[str] = Form(None),
    category: Optional[str] = Form("other"),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
):
    doc_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename or "unknown")[1] or ""
    safe_filename = f"{doc_id}{ext}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    with Session(engine) as session:
        session.execute(
            text("""
                INSERT INTO documents
                    (id, agent_id, property_id, client_id, filename, file_path,
                     file_size_bytes, content_type, category, title, description)
                VALUES
                    (:id, :agent_id, :property_id, :client_id, :filename, :file_path,
                     :size, :content_type, :category, :title, :description)
            """),
            {
                "id": doc_id,
                "agent_id": DEFAULT_AGENT_ID,
                "property_id": property_id,
                "client_id": client_id,
                "filename": file.filename or safe_filename,
                "file_path": file_path,
                "size": len(content),
                "content_type": file.content_type,
                "category": category,
                "title": title,
                "description": description,
            },
        )
        session.commit()

    return get_document(doc_id)


@router.delete("/{doc_id}")
def delete_document(doc_id: str):
    with Session(engine) as session:
        row = session.execute(
            text("SELECT file_path FROM documents WHERE id = :id"),
            {"id": doc_id},
        ).fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Document not found")

        result = session.execute(
            text("DELETE FROM documents WHERE id = :id"),
            {"id": doc_id},
        )
        session.commit()

    if os.path.exists(row[0]):
        os.remove(row[0])

    return {"status": "deleted", "id": doc_id}


@router.post("/{doc_id}/extract")
def extract_document_text(doc_id: str):
    with Session(engine) as session:
        row = session.execute(
            text("SELECT file_path, content_type FROM documents WHERE id = :id"),
            {"id": doc_id},
        ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Document not found")

    file_path = row[0]
    content_type = row[1] or ""
    extracted = ""

    try:
        import fitz
        if content_type == "application/pdf" or file_path.lower().endswith(".pdf"):
            doc = fitz.open(file_path)
            extracted = "\n".join(page.get_text() for page in doc)
            doc.close()
        else:
            with open(file_path, "r", errors="ignore") as f:
                extracted = f.read()
    except ImportError:
        extracted = f"[Text extraction placeholder. File: {os.path.basename(file_path)}, Type: {content_type}]"
    except Exception as e:
        extracted = f"[Extraction error: {e}]"

    with Session(engine) as session:
        session.execute(
            text("UPDATE documents SET extracted_text = :text, updated_at = NOW() WHERE id = :id"),
            {"id": doc_id, "text": extracted},
        )
        session.commit()

    return {"id": doc_id, "extracted_text": extracted, "char_count": len(extracted)}


class AskRequest(BaseModel):
    question: str


@router.post("/{doc_id}/ask")
def ask_document(doc_id: str, body: AskRequest):
    with Session(engine) as session:
        row = session.execute(
            text("SELECT filename, extracted_text FROM documents WHERE id = :id"),
            {"id": doc_id},
        ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Document not found")

    extracted = row[1] or "[No extracted text available]"
    text_preview = extracted[:2000]

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "packages", "ai"))
    try:
        from agent import ask
        prompt = (
            f"Document: {row[0]}\n\n"
            f"Content:\n{text_preview}\n\n"
            f"Question: {body.question}\n\n"
            f"Answer based on the document content above."
        )
        result = ask(prompt, override_model="fast-model")
        answer = result.get("response", "")
    except Exception:
        answer = (
            f"[Template analysis]\n"
            f"Document: {row[0]}\n"
            f"Question: {body.question}\n"
            f"Text available: {len(extracted)} characters.\n"
            f"Full document analysis requires the AI agent to be running."
        )

    return {"document_id": doc_id, "question": body.question, "answer": answer}
