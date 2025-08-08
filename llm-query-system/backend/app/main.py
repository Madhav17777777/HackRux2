# ---------- main.py ----------
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.ingest import load_and_split_documents
from app.embeddings import embed_and_store, cleanup_embeddings
from app.retrieval import retrieve_clauses
from app.evaluate import evaluate_decision
from app.memory_store import clause_memory
from app.utils import log_memory_usage, check_memory_limit, force_memory_cleanup, optimize_memory_settings
import uvicorn
import gc
import os
import itertools

# Optimize memory for container limits
optimize_memory_settings()

app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    documents: str  # PDF path or raw base64
    questions: list[str]

# --- CONFIG ---
SAFE_MEMORY_MB = 500  # Near Render free-tier limit (512MB)

@app.middleware("http")
async def memory_cleanup_middleware(request, call_next):
    log_memory_usage("Request Start")
    response = await call_next(request)
    force_memory_cleanup()
    log_memory_usage("Request End")
    return response

@app.post("/api/v1/hackrx/run")
async def run_pipeline(request: QueryRequest):
    try:
        log_memory_usage("Pipeline Start")

        # Step 1: Load document lazily
        # No hard limit, but we will process in batches to avoid memory spikes
        pages_iter = load_and_split_documents(request.documents, stream_mode=True)  # <-- needs stream mode in ingest
        print("📄 Document loaded in streaming mode.")

        answers = []
        page_batch_size = 5  # Small chunks to stay under memory cap

        # Process questions one by one
        for q_index, question in enumerate(request.questions, start=1):
            print(f"❓ Question {q_index}/{len(request.questions)}: {question}")

            if not check_memory_limit(SAFE_MEMORY_MB):
                answers.append("⚠️ Stopped due to high memory usage.")
                break

            relevant_clauses_accum = []

            # Step 2: Go through doc pages in batches, embed, search, discard
            batch_number = 0
            for batch in iter(lambda: list(itertools.islice(pages_iter, page_batch_size)), []):
                batch_number += 1
                if not batch:
                    break

                embed_and_store(batch)  # store batch in FAISS
                clauses = retrieve_clauses(question)
                if clauses:
                    relevant_clauses_accum.extend(clauses)

                # Free FAISS batch before next
                cleanup_embeddings()
                clause_memory.clear()
                gc.collect()

                # Extra cleanup if memory high
                if not check_memory_limit(SAFE_MEMORY_MB - 50):
                    print("⚠️ Memory high, breaking batch loop.")
                    break

            if not relevant_clauses_accum:
                answers.append("No relevant clauses found.")
                continue

            # Step 3: Evaluate decision
            decision = evaluate_decision(question, relevant_clauses_accum)
            answers.append(decision.get("justification", "No answer available."))

            # Clean up after each question
            del relevant_clauses_accum
            del decision
            gc.collect()
            force_memory_cleanup()

        log_memory_usage("After All Questions")
        return {"answers": answers}

    except HTTPException:
        raise
    except Exception as e:
        cleanup_embeddings()
        clause_memory.clear()
        gc.collect()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    from app.utils import get_memory_usage
    memory = get_memory_usage()
    return {
        "status": "healthy",
        "memory_usage_mb": round(memory['rss_mb'], 1),
        "memory_percent": round(memory['percent'], 1)
    }

@app.get("/memory")
async def memory_status():
    from app.utils import get_memory_usage
    memory = get_memory_usage()
    return {
        "rss_mb": round(memory['rss_mb'], 1),
        "vms_mb": round(memory['vms_mb'], 1),
        "percent": round(memory['percent'], 1),
        "available_mb": round(memory['available_mb'], 1),
        "within_limit": check_memory_limit(SAFE_MEMORY_MB)
    }

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
