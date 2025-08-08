# ---------- app/ingest.py ----------
import base64
import io
import pdfplumber

def load_and_split_documents(doc_input, stream_mode=False):
    """
    Load PDF pages. If stream_mode=True, yield pages one-by-one (low memory).
    doc_input can be a file path or base64 string.
    """
    if isinstance(doc_input, str) and doc_input.strip().startswith("%PDF-"):
        # Raw PDF text input — unlikely but handle
        pdf_bytes = io.BytesIO(doc_input.encode("latin1"))
    elif isinstance(doc_input, str) and not doc_input.lower().endswith(".pdf"):
        # Base64 input
        pdf_bytes = io.BytesIO(base64.b64decode(doc_input))
    else:
        # File path
        pdf_bytes = open(doc_input, "rb")

    if stream_mode:
        with pdfplumber.open(pdf_bytes) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    yield text
    else:
        pages = []
        with pdfplumber.open(pdf_bytes) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)
        return pages
