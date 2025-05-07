from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import fitz
import os
import uuid
import sys
import openai 

try:
    from llama_index.core import VectorStoreIndex, Document, Settings
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding
except ImportError as e:
    print(f"Error importing from llama_index: {e}")
    print("Trying alternative import paths...")
    try:
        from llama_index import VectorStoreIndex, Document
        from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    except ImportError as e2:
        print(f"Alternative import also failed: {e2}")
        print("Please ensure llama_index and sentence-transformers are installed:")
        print("pip install llama_index sentence-transformers")
        sys.exit(1)

app = FastAPI()

openai.api_key = "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"  # Replace with your actual OpenAI API key

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("Setting up embedding model...")
try:
    embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
    print("Using sentence-transformers/all-MiniLM-L6-v2 embedding model")
except Exception as e:
    print(f"Error loading all-MiniLM-L6-v2: {e}")
    try:
        embed_model = HuggingFaceEmbedding(model_name="distilbert-base-uncased")
        print("Using distilbert-base-uncased embedding model")
    except Exception as e2:
        print(f"Error loading alternative model: {e2}")
        print("Using default local embedding")
        embed_model = "local"

try:
    if hasattr(Settings, "embed_model"):
        Settings.embed_model = embed_model
        print("Successfully set embedding model in Settings")
    else:
        print("Settings.embed_model not available, trying alternative configuration")
        from llama_index.core import Settings as LlamaIndexSettings
        LlamaIndexSettings.embed_model = embed_model
except Exception as e:
    print(f"Failed to set embedding model: {e}")
    print("Will rely on default embedding configuration when creating index")

UPLOAD_DIR = "uploaded_pdfs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

documents = {}

class QuestionRequest(BaseModel):
    document_id: str
    question: str

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload and process a PDF file.
    Returns a document_id that can be used for asking questions.
    """
    if not file.filename.endswith(".pdf"):
        return {"error": "Only PDF files are allowed."}

    doc_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{doc_id}.pdf")

    print(f"Saving file to: {file_path}")

    try:
        with open(file_path, "wb") as f:
            file_content = await file.read()
            f.write(file_content)

        print(f"File {file.filename} uploaded successfully.")

        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()

        documents[doc_id] = text
        return {"document_id": doc_id, "message": "PDF uploaded and processed"}
    
    except Exception as e:
        print(f"Error while saving or processing file: {str(e)}")
        return {"error": f"Failed to process PDF: {str(e)}"}

@app.post("/ask")
def ask_question(request: QuestionRequest):
    """
    Ask a question about a previously uploaded document.
    """
    document_text = documents.get(request.document_id)
    if not document_text:
        return {"error": "Invalid document ID."}

    try:
        docs = [Document(text=document_text)]
        
        index = VectorStoreIndex.from_documents(
            docs,
            embed_model=embed_model
        )
        
        engine = index.as_query_engine()
        
        response = engine.query(request.question)
        return {"answer": str(response)}
    except Exception as e:
        return {"error": f"Error processing question: {str(e)}.\n\nPlease make sure you have installed required packages: pip install sentence-transformers"}

@app.get("/")
def read_root():
    return {"message": "PDF Question Answering API using local embeddings is running. Upload a PDF and ask questions!"}

@app.get("/documents")
def list_documents():
    return {"document_ids": list(documents.keys())}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
