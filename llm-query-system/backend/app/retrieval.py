# retrieval.py
from app.embeddings import model, index
from app.memory_store import clause_memory
import numpy as np

def retrieve_clauses(query, top_k=5):
    if clause_memory.is_empty():
        print("❌ Clause store is empty!")
        return []

    query_embedding = model.encode([query])
    D, I = index.search(np.array(query_embedding), top_k)

    all_clauses = clause_memory.get_all()
    top_clauses = []
    for i in I[0]:
        if 0 <= i < len(all_clauses):
            top_clauses.append(all_clauses[i])
    return top_clauses
