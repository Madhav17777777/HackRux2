# ingest.py
import fitz  # PyMuPDF
import requests
import io

def load_and_split_documents(pdf_url):
    print("📥 Downloading PDF from:", pdf_url)

    response = requests.get(pdf_url)
    if response.status_code != 200:
        raise Exception("Failed to download PDF")

    doc = fitz.open(stream=io.BytesIO(response.content), filetype="pdf")
    pages = [page.get_text() for page in doc]

    print("📄 Extracted", len(pages), "pages from PDF.")
    return pages
