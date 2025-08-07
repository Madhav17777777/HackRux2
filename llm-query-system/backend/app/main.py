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

# Initialize memory optimization settings
optimize_memory_settings()

app = FastAPI()

# Enable CORS for frontend interaction
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define request schema
class QueryRequest(BaseModel):
    documents: str
    questions: list[str]

# Memory management settings
MAX_PDF_PAGES = int(os.getenv("MAX_PDF_PAGES", "50"))  # Limit PDF pages
MAX_QUESTIONS = int(os.getenv("MAX_QUESTIONS", "10"))   # Limit questions per request
MEMORY_LIMIT_MB = int(os.getenv("MEMORY_LIMIT_MB", "400"))  # Memory limit in MB

@app.middleware("http")
async def memory_cleanup_middleware(request, call_next):
    """Middleware to clean up memory after each request"""
    log_memory_usage("Request Start")
    
    response = await call_next(request)
    
    # Force garbage collection after each request
    force_memory_cleanup()
    log_memory_usage("Request End")
    
    return response

# API endpoint
@app.post("/api/v1/hackrx/run")
async def run_pipeline(request: QueryRequest):
    try:
        log_memory_usage("Pipeline Start")
        
        # Check memory limit before processing
        if not check_memory_limit(MEMORY_LIMIT_MB):
            raise HTTPException(status_code=503, detail="Service temporarily unavailable due to high memory usage")
        
        # Validate request size
        if len(request.questions) > MAX_QUESTIONS:
            raise HTTPException(
                status_code=400, 
                detail=f"Too many questions. Maximum allowed: {MAX_QUESTIONS}"
            )
        
        # Step 1: Load and chunk the document with page limit
        pages = load_and_split_documents(request.documents, max_pages=MAX_PDF_PAGES)
        print("📄 Document loaded. Total pages:", len(pages))
        log_memory_usage("After PDF Loading")
        
        if not pages:
            raise HTTPException(status_code=400, detail="No content extracted from PDF")

        # Step 2: Embed and store clauses in FAISS
        embed_and_store(pages)
        print("✅ Embeddings stored.")
        log_memory_usage("After Embedding")

        answers = []

        # Step 3: Process each question with better memory management
        for i, question in enumerate(request.questions):
            print(f"❓ Processing question {i+1}/{len(request.questions)}: {question}")
            
            try:
                # Check memory before processing each question
                if not check_memory_limit(MEMORY_LIMIT_MB):
                    print("⚠️ Memory limit reached, stopping processing")
                    answers.append("Service temporarily unavailable due to high memory usage")
                    break
                
                relevant_clauses = retrieve_clauses(question)
                if not relevant_clauses:
                    answers.append("No relevant clauses found.")
                    continue

                decision = evaluate_decision(question, relevant_clauses)
                answers.append(decision.get("justification", "No answer available."))
                
                # Aggressive cleanup after each question
                del relevant_clauses
                del decision
                gc.collect()
                
                # Force memory cleanup every 3 questions
                if (i + 1) % 3 == 0:
                    force_memory_cleanup()
                
            except Exception as e:
                print(f"❌ Error processing question {i+1}: {e}")
                answers.append(f"Error processing question: {str(e)}")

        # Step 4: Clean up embeddings and memory
        cleanup_embeddings()
        clause_memory.clear()  # Clear stored clauses
        log_memory_usage("After Cleanup")
        
        # Step 5: Return structured output
        return {"answers": answers}

    except HTTPException:
        raise
    except Exception as e:
        print("❌ Internal error:", str(e))
        # Clean up on error
        cleanup_embeddings()
        clause_memory.clear()
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@app.get("/health")
async def health_check():
    from app.utils import get_memory_usage
    memory = get_memory_usage()
    return {
        "status": "healthy", 
        "memory_optimized": True,
        "memory_usage_mb": round(memory['rss_mb'], 1),
        "memory_percent": round(memory['percent'], 1)
    }

# Memory status endpoint
@app.get("/memory")
async def memory_status():
    from app.utils import get_memory_usage
    memory = get_memory_usage()
    return {
        "rss_mb": round(memory['rss_mb'], 1),
        "vms_mb": round(memory['vms_mb'], 1),
        "percent": round(memory['percent'], 1),
        "available_mb": round(memory['available_mb'], 1),
        "within_limit": check_memory_limit(MEMORY_LIMIT_MB)
    }

# Run app locally
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)  # Disable reload for production
