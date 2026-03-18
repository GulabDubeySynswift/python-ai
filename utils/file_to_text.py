import os
import tempfile
from typing import Optional

# PDF
import fitz  # pymupdf

# DOCX
from docx import Document

# CSV / Excel
import pandas as pd


async def file_to_text(file) -> str:
    """
    Convert uploaded file (FastAPI UploadFile) to text
    Supports: PDF, TXT, CSV, XLSX, DOCX
    """

    filename = file.filename.lower()
    content = await file.read()

    # Save temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=filename) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # -------- PDF --------
        if filename.endswith(".pdf"):
            return extract_pdf(tmp_path)

        # -------- TXT --------
        elif filename.endswith(".txt"):
            return content.decode("utf-8", errors="ignore")

        # -------- DOCX --------
        elif filename.endswith(".docx"):
            return extract_docx(tmp_path)

        # -------- CSV --------
        elif filename.endswith(".csv"):
            df = pd.read_csv(tmp_path)
            return df.to_string()

        # -------- Excel --------
        elif filename.endswith(".xlsx") or filename.endswith(".xls"):
            df = pd.read_excel(tmp_path)
            return df.to_string()

        # -------- Fallback --------
        else:
            return try_decode(content)

    finally:
        os.remove(tmp_path)


# ---------------- HELPERS ---------------- #

def extract_pdf(path: str) -> str:
    text = ""
    doc = fitz.open(path)
    for page in doc:
        text += page.get_text()
    return text


def extract_docx(path: str) -> str:
    doc = Document(path)
    return "\n".join([p.text for p in doc.paragraphs])


def try_decode(content: bytes) -> str:
    """
    Fallback for unknown file types
    """
    try:
        return content.decode("utf-8")
    except:
        try:
            return content.decode("latin-1")
        except:
            return "Unsupported file type or binary data"