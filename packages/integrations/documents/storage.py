from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


MOCK_DOCUMENTS = [
    {
        "id": "doc_001",
        "filename": "property_listing_123_main_st.pdf",
        "size_bytes": 245760,
        "content_type": "application/pdf",
        "uploaded_at": "2025-01-10T08:30:00Z",
    },
    {
        "id": "doc_002",
        "filename": "purchase_agreement_downtown_condo.docx",
        "size_bytes": 51200,
        "content_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "uploaded_at": "2025-01-12T14:00:00Z",
    },
    {
        "id": "doc_003",
        "filename": "client_disclosure_form_alice_j.pdf",
        "size_bytes": 102400,
        "content_type": "application/pdf",
        "uploaded_at": "2025-01-13T09:15:00Z",
    },
]


class DocumentStorage:
    def __init__(self, storage_dir: str | None = None) -> None:
        self.storage_dir = storage_dir or "/tmp/realtyai_docs"
        os.makedirs(self.storage_dir, exist_ok=True)
        self._documents: dict[str, dict[str, Any]] = {
            d["id"]: dict(d) for d in MOCK_DOCUMENTS
        }

    def upload_document(
        self, file_path: str, filename: str
    ) -> dict[str, Any]:
        """Upload a document from a local file path into storage."""
        logger.info("Uploading document %s as %s", file_path, filename)
        if not os.path.exists(file_path):
            return {"status": "error", "error": f"File not found: {file_path}"}

        dest_path = os.path.join(self.storage_dir, filename)
        import shutil

        shutil.copy2(file_path, dest_path)
        doc_id = f"doc_{len(self._documents) + 1:03d}"
        stat = os.stat(dest_path)
        doc_info = {
            "id": doc_id,
            "filename": filename,
            "size_bytes": stat.st_size,
            "content_type": self._guess_content_type(filename),
            "uploaded_at": datetime.utcnow().isoformat() + "Z",
            "path": dest_path,
        }
        self._documents[doc_id] = doc_info
        return {"status": "uploaded", **doc_info}

    def get_document(self, document_id: str) -> dict[str, Any]:
        """Retrieve document metadata by ID."""
        doc = self._documents.get(document_id)
        if doc is None:
            return {"status": "error", "error": f"Document {document_id} not found"}
        return {"status": "found", **doc}

    def list_documents(self) -> list[dict[str, Any]]:
        """List all stored documents."""
        return list(self._documents.values())

    def _guess_content_type(self, filename: str) -> str:
        ext = os.path.splitext(filename)[1].lower()
        mapping = {
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".doc": "application/msword",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".txt": "text/plain",
        }
        return mapping.get(ext, "application/octet-stream")
