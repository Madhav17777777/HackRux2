# ingest.py
import fitz  # PyMuPDF
import requests
import io
import gc

def load_and_split_documents(pdf_url, max_pages=None):
    print("📥 Downloading PDF from:", pdf_url)

    try:
        response = requests.get(pdf_url, timeout=30)
        if response.status_code != 200:
            raise Exception("Failed to download PDF")

        # Use stream to avoid loading entire PDF into memory at once
        doc = fitz.open(stream=io.BytesIO(response.content), filetype="pdf")
        
        # Limit pages if specified to prevent memory issues
        if max_pages and len(doc) > max_pages:
            print(f"⚠️ PDF has {len(doc)} pages, limiting to {max_pages}")
            pages_to_process = max_pages
        else:
            pages_to_process = len(doc)

        pages = []
        # Process pages in smaller batches
        batch_size = 10
        
        for i in range(0, pages_to_process, batch_size):
            batch_end = min(i + batch_size, pages_to_process)
            batch_pages = []
            
            for j in range(i, batch_end):
                page = doc[j]
                text = page.get_text()
                # Clean and truncate text to reduce memory usage
                text = text.strip()[:5000]  # Limit to 5000 chars per page
                if text:  # Only add non-empty pages
                    batch_pages.append(text)
                
                # Clean up page object
                del page
            
            pages.extend(batch_pages)
            
            # Force garbage collection after each batch
            gc.collect()

        doc.close()
        
        # Clean up response content
        del response.content
        gc.collect()

        print("📄 Extracted", len(pages), "pages from PDF.")
        return pages
        
    except Exception as e:
        print(f"❌ Error loading PDF: {e}")
        raise
    finally:
        # Ensure cleanup
        gc.collect()
