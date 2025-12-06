import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import LangChain tools
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Import our custom services
from app.services.vector_store import upload_document_to_db, search_documents
from app.services.llm_engine import generate_answer
from app.routers.video import router as video_router

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- DATA MODELS (The Schema) ---
class ChatRequest(BaseModel):
    question: str

# --- ENDPOINTS ---

@app.get("/")
def health_check():
    return {"status": "Backend is running!", "project": "Auto-Didact"}

@app.post("/test-ingest")
async def ingest_pdf():
    """
    1. Loads 'sample.pdf' (Make sure this file exists in backend/ folder!)
    2. Splits it into chunks
    3. Uploads to Supabase
    """
    file_path = "sample.pdf"
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="sample.pdf not found in backend folder")

    # 1. Load PDF
    loader = PyPDFLoader(file_path)
    docs = loader.load()

    # 2. Split Text (Crucial Step!)
    # LLMs can't read a whole book at once. We verify 'chunk_size' is small enough for the embedding model.
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    split_docs = splitter.split_documents(docs)

    # 3. Upload to Supabase
    upload_document_to_db(split_docs)

    return {"status": "Success", "chunks_uploaded": len(split_docs)}


@app.post("/test-ask")
async def ask_question(request: ChatRequest):
    """
    1. Search Supabase for relevant chunks
    2. Send chunks + question to Groq
    3. Return answer
    """
    # 1. Search Database
    relevant_docs = search_documents(request.question)
    
    # Combine the content of the found docs into one string
    context_text = "\n\n".join([doc.page_content for doc in relevant_docs])

    if not context_text:
        return {"answer": "I couldn't find any relevant information in the database."}

    # 2. Generate Answer
    answer = generate_answer(request.question, context_text)

    return {"answer": answer, "sources": [doc.page_content[:100] + "..." for doc in relevant_docs]}


# Video generation router (media engine)
app.include_router(video_router)