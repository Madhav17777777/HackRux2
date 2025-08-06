# embeddings.py
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from app.memory_store import clause_memory

model = SentenceTransformer("all-MiniLM-L6-v2")
index = faiss.IndexFlatL2(384)

def embed_and_store(chunks):
    if not chunks:
        print("⚠️ No text chunks to embed.")
        return

    embeddings = model.encode(chunks)
    index.reset()
    index.add(np.array(embeddings))
    clause_memory.store(chunks)
    print(f"✅ Embedded and stored {len(chunks)} clauses.")
