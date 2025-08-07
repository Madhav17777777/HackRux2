# embeddings.py
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from app.memory_store import clause_memory
import gc

# Lazy loading - model will be loaded only when first used
_model = None
_index = None

def get_model():
    global _model
    if _model is None:
        # Use a smaller model for better memory efficiency
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model

def get_index():
    global _index
    if _index is None:
        _index = faiss.IndexFlatL2(384)
    return _index

def embed_and_store(chunks):
    if not chunks:
        print("⚠️ No text chunks to embed.")
        return

    try:
        model = get_model()
        index = get_index()
        
        # Process in smaller batches to reduce memory usage
        batch_size = 50
        all_embeddings = []
        
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            batch_embeddings = model.encode(batch, show_progress_bar=False)
            all_embeddings.append(batch_embeddings)
            
            # Force garbage collection after each batch
            gc.collect()
        
        # Combine all embeddings
        embeddings = np.vstack(all_embeddings)
        
        # Reset index and add new embeddings
        index.reset()
        index.add(embeddings)
        clause_memory.store(chunks)
        
        print(f"✅ Embedded and stored {len(chunks)} clauses.")
        
        # Clear embeddings from memory
        del embeddings, all_embeddings
        gc.collect()
        
    except Exception as e:
        print(f"❌ Error in embedding: {e}")
        raise

def cleanup_embeddings():
    """Clean up embeddings to free memory"""
    global _model, _index
    if _model is not None:
        del _model
        _model = None
    if _index is not None:
        del _index
        _index = None
    gc.collect()
