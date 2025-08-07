# retrieval.py
from app.embeddings import get_model, get_index
from app.memory_store import clause_memory
import numpy as np
import gc

def retrieve_clauses(query, top_k=5):
    if clause_memory.is_empty():
        print("❌ Clause store is empty!")
        return []

    try:
        model = get_model()
        index = get_index()
        
        query_embedding = model.encode([query], show_progress_bar=False)
        D, I = index.search(np.array(query_embedding), top_k)

        all_clauses = clause_memory.get_all()
        top_clauses = []
        for i in I[0]:
            if 0 <= i < len(all_clauses):
                top_clauses.append(all_clauses[i])
        
        # Clean up query embedding
        del query_embedding, D, I
        gc.collect()
        
        return top_clauses
        
    except Exception as e:
        print(f"❌ Error in retrieval: {e}")
        return []
