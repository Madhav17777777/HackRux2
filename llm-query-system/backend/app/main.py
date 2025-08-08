# ---------- main.py ----------
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.ingest import load_and_split_documents
from app.embeddings import embed_and_store, cleanup_embeddings
from app.retrieval import retrieve_clauses
from app.evaluate import evaluate_decision
from app.memory_store import clause_memory
from app.utils import log_memory_usage, check_memory_limit, force_memory_cleanup, optimize_memory_settings
import uvicorn
import gc
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
    documents: str  # PDF file path or base64 string
    questions: list[str]

# Render Free Tier Safe Memory Limit
SAFE_MEMORY_MB = 500  # keep below 512 MB

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

        answers = []
        page_batch_size = 5  # process in small chunks to avoid memory spikes

        # Process each question independently
        for q_index, question in enumerate(request.questions, start=1):
            print(f"❓ Question {q_index}/{len(request.questions)}: {question}")

            if not check_memory_limit(SAFE_MEMORY_MB):
                answers.append("⚠️ Stopped due to high memory usage.")
                break

            relevant_clauses_accum = []

            # Create a fresh iterator for every question
            pages_iter = load_and_split_documents(request.documents, stream_mode=True)

            # Process document in batches
            for batch_number, batch in enumerate(iter(lambda: list(itertools.islice(pages_iter, page_batch_size)), []), start=1):
                if not batch:
                    break

                embed_and_store(batch)
                clauses = retrieve_clauses(question)
                if clauses:
                    relevant_clauses_accum.extend(clauses)

                # Clear embeddings to free RAM
                cleanup_embeddings()
                clause_memory.clear()
                gc.collect()

                if not check_memory_limit(SAFE_MEMORY_MB - 50):
                    print("⚠️ Memory high, breaking batch loop.")
                    break

            if not relevant_clauses_accum:
                answers.append("No relevant clauses found.")
                continue

            decision = evaluate_decision(question, relevant_clauses_accum)
            answers.append(decision.get("justification", "No answer available."))

            # Cleanup after each question
            del relevant_clauses_accum
            del decision
            gc.collect()
            force_memory_cleanup()

        log_memory_usage("After All Questions")
        return {"answers": answers}

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        cleanup_embeddings()
        clause_memory.clear()
        gc.collect()
        return JSONResponse(status_code=500, content={"error": str(e)})

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
