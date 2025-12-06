import os
from dotenv import load_dotenv
from supabase import create_client
from langchain_community.vectorstores import SupabaseVectorStore
from langchain_huggingface import HuggingFaceEmbeddings

load_dotenv()

# 1. Setup Supabase Client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase = create_client(supabase_url, supabase_key)

# 2. Setup Embeddings (The "Translator" that turns text into numbers)
# We use 'all-MiniLM-L6-v2' because it is FREE, FAST, and runs on your laptop.
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

def upload_document_to_db(docs):
    """
    Takes a list of LangChain Documents and uploads them to Supabase.
    """
    print(f"--- Uploading {len(docs)} chunks to Supabase ---")
    
    # Add sequential IDs to avoid UUID/bigint conflicts
    for idx, doc in enumerate(docs):
        if not hasattr(doc, 'metadata') or doc.metadata is None:
            doc.metadata = {}
        # Use timestamp + index for unique ID
        import time
        doc.metadata['id'] = int(time.time() * 1000) + idx
    
    vector_store = SupabaseVectorStore.from_documents(
        docs,
        embeddings,
        client=supabase,
        table_name="documents",
        query_name="match_documents"
    )
    print("--- Upload Complete ---")

def search_documents(query):
    """
    Searches Supabase for text similar to the query.
    """
    print(f"--- Searching for: {query} ---")
    
    vector_store = SupabaseVectorStore(
        embedding=embeddings,
        client=supabase,
        table_name="documents",
        query_name="match_documents"
    )
    
    # Return top 3 most similar chunks
    matched_docs = vector_store.similarity_search(query, k=3)
    return matched_docs