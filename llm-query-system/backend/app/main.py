# ---------- main.py ----------
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.ingest import load_and_split_documents
from app.embeddings import embed_and_store
from app.retrieval import retrieve_clauses
from app.evaluate import evaluate_decision
import uvicorn

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

# API endpoint
@app.post("/api/v1/hackrx/run")
async def run_pipeline(request: QueryRequest):
    try:
        # Step 1: Load and chunk the document
        pages = load_and_split_documents(request.documents)
        print("📄 Document loaded. Total pages:", len(pages))

        # Step 2: Embed and store clauses in FAISS
        embed_and_store(pages)
        print("✅ Embeddings stored.")

        answers = []

        # Step 3: Process each question
        for question in request.questions:
            print(f"❓ Processing question: {question}")
            relevant_clauses = retrieve_clauses(question)
            if not relevant_clauses:
                answers.append("No relevant clauses found.")
                continue

            decision = evaluate_decision(question, relevant_clauses)
            answers.append(decision.get("justification", "No answer available."))

        # Step 4: Return structured output
        return {"answers": answers}

    except Exception as e:
        print("❌ Internal error:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

# Run app locally
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
