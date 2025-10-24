from fastapi import FastAPI, BackgroundTasks, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from rag_engine.retriever import init_collection, add_document, get_collection_info
from rag_engine.generator import generate_answer
from rag_engine.updater import update_from_urls, update_single_url
from rag_engine.pdf_loader import load_pdf
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import tempfile
import os

app = FastAPI(title="CodeLens API", version="2.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "*"  # Development only
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request models
class QueryRequest(BaseModel):
    query: str
    top_k: int = 3

class DocumentRequest(BaseModel):
    text: str
    source: str = "manual_upload"

class URLUpdateRequest(BaseModel):
    urls: List[str]

class SingleURLRequest(BaseModel):
    url: str

# Predefined documentation sources
PREDEFINED_SOURCES = {
    "fastapi": [
        "https://fastapi.tiangolo.com/",
        "https://fastapi.tiangolo.com/tutorial/",
        "https://fastapi.tiangolo.com/advanced/"
    ],
    "langchain": [
        "https://python.langchain.com/docs/get_started/introduction",
        "https://python.langchain.com/docs/modules/model_io/"
    ],
    "pydantic": [
        "https://docs.pydantic.dev/latest/",
        "https://docs.pydantic.dev/latest/concepts/models/"
    ]
}

# ============================================
# AUTO-UPDATE SCHEDULER SETUP
# ============================================

scheduler = BackgroundScheduler()
last_update_time = None

def scheduled_update_job():
    """
    Scheduled job that runs automatically to update documentation.
    """
    global last_update_time
    print("\n" + "="*60)
    print(f"🔄 AUTO-UPDATE STARTED at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    all_urls = []
    for source_name, urls in PREDEFINED_SOURCES.items():
        print(f"📚 Adding {source_name} URLs...")
        all_urls.extend(urls)
    
    # Run the update
    result = update_from_urls(all_urls, batch_delay=2.0)
    
    last_update_time = datetime.now()
    
    print("\n" + "="*60)
    print(f"✅ AUTO-UPDATE COMPLETED")
    print(f"   Total URLs processed: {result['total_urls']}")
    print(f"   Successful: {result['successful']}")
    print(f"   Failed: {result['failed']}")
    print(f"   Total chunks added: {result['total_chunks']}")
    print(f"   Next update in 24 hours")
    print("="*60 + "\n")

# ============================================
# STARTUP & SHUTDOWN EVENTS
# ============================================

@app.on_event("startup")
async def startup_event():
    """Initialize Qdrant collection and start scheduler."""
    print("🚀 Starting CodeLens API...")
    init_collection()
    
    # Start the scheduler
    print("⏰ Starting auto-update scheduler...")
    
    # Schedule daily updates at 2 AM
    scheduler.add_job(
        scheduled_update_job,
        'cron',
        hour=2,
        minute=0,
        id='daily_doc_update',
        replace_existing=True
    )
    
    # Uncomment this for testing (updates every 30 minutes):
    # scheduler.add_job(
    #     scheduled_update_job,
    #     'interval',
    #     minutes=30,
    #     id='test_update',
    #     replace_existing=True
    # )
    
    scheduler.start()
    print("✅ Auto-update scheduler started (runs daily at 2 AM)")
    print("✅ CodeLens API ready!")

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown scheduler gracefully."""
    print("🛑 Shutting down scheduler...")
    scheduler.shutdown()
    print("✅ Scheduler stopped")

# ============================================
# BASIC ENDPOINTS
# ============================================

@app.get("/")
def root():
    return {
        "message": "CodeLens API is running",
        "status": "healthy",
        "version": "2.0.0",
        "features": [
            "RAG Question Answering",
            "Web Scraping",
            "PDF Upload",
            "Auto-Updates (Scheduled)",
            "Scheduler Control"
        ]
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

# ============================================
# RAG ENDPOINTS
# ============================================

@app.post("/ask")
def ask(request: QueryRequest):
    """
    Ask a question and get an AI-generated answer based on the knowledge base.
    """
    try:
        result = generate_answer(request.query, top_k=request.top_k)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/add_document")
def add_doc(request: DocumentRequest):
    """
    Manually add a document to the knowledge base.
    """
    try:
        chunks_added = add_document(
            text=request.text,
            metadata={"source": request.source}
        )
        return {
            "status": "success",
            "chunks_added": chunks_added,
            "source": request.source
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# WEB SCRAPING ENDPOINTS
# ============================================

@app.post("/update_from_urls")
def update_urls(request: URLUpdateRequest, background_tasks: BackgroundTasks):
    """
    Scrape content from multiple URLs and add to knowledge base.
    This runs in the background.
    """
    background_tasks.add_task(update_from_urls, request.urls)
    return {
        "status": "started",
        "message": f"Scraping {len(request.urls)} URLs in background",
        "urls": request.urls
    }

@app.post("/update_from_url")
def update_url(request: SingleURLRequest):
    """
    Scrape content from a single URL (synchronous).
    """
    try:
        result = update_single_url(request.url)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/update_predefined/{source}")
def update_predefined_source(source: str, background_tasks: BackgroundTasks):
    """
    Update from predefined documentation sources.
    Available sources: fastapi, langchain, pydantic
    """
    if source not in PREDEFINED_SOURCES:
        raise HTTPException(
            status_code=404,
            detail=f"Source '{source}' not found. Available: {list(PREDEFINED_SOURCES.keys())}"
        )
    
    urls = PREDEFINED_SOURCES[source]
    background_tasks.add_task(update_from_urls, urls)
    
    return {
        "status": "started",
        "source": source,
        "urls": urls,
        "message": f"Updating {source} documentation in background"
    }

@app.get("/available_sources")
def available_sources():
    """
    Get list of available predefined documentation sources.
    """
    return {
        "sources": list(PREDEFINED_SOURCES.keys()),
        "details": {k: len(v) for k, v in PREDEFINED_SOURCES.items()}
    }

# ============================================
# PDF UPLOAD ENDPOINT
# ============================================

@app.post("/upload_pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload a PDF file and add its content to the knowledge base.
    """
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        # Process the PDF
        result = load_pdf(tmp_path)
        
        # Clean up temp file
        os.unlink(tmp_path)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# COLLECTION INFO
# ============================================

@app.get("/collection_info")
def collection_info():
    """
    Get information about the vector database collection.
    """
    return get_collection_info()

# ============================================
# SCHEDULER CONTROL ENDPOINTS
# ============================================

@app.get("/scheduler/status")
def get_scheduler_status():
    """Get scheduler status and next run time."""
    jobs = scheduler.get_jobs()
    
    if jobs:
        next_run = jobs[0].next_run_time
        return {
            "status": "running",
            "scheduler_running": scheduler.running,
            "next_update": next_run.isoformat() if next_run else None,
            "last_update": last_update_time.isoformat() if last_update_time else None,
            "update_frequency": "daily at 2:00 AM"
        }
    else:
        return {
            "status": "no_jobs_scheduled",
            "scheduler_running": scheduler.running
        }

@app.post("/scheduler/trigger_now")
def trigger_update_now(background_tasks: BackgroundTasks):
    """
    Manually trigger an immediate update (without waiting for schedule).
    """
    background_tasks.add_task(scheduled_update_job)
    return {
        "status": "triggered",
        "message": "Manual update started in background"
    }

@app.post("/scheduler/pause")
def pause_scheduler():
    """Pause the auto-update scheduler."""
    scheduler.pause()
    return {"status": "paused", "message": "Scheduler paused"}

@app.post("/scheduler/resume")
def resume_scheduler():
    """Resume the auto-update scheduler."""
    scheduler.resume()
    return {"status": "resumed", "message": "Scheduler resumed"}
