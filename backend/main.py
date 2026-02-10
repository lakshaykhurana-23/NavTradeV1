"""
FastAPI application - SIMPLIFIED with cache and batch processing
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pathlib import Path
from typing import List
import time

from backend.models import ProcessRequest, ProcessResponse, Item, Model
from backend.config import INPUT_DIR
from backend.simple_cache import SimpleCache  
from backend.processor import DocumentProcessor


app = FastAPI(title="Document Processor API", version="1.0.0")

# Initialize cache and processor
cache = SimpleCache()
processor = DocumentProcessor()

# Mock responses for chat models
RESPONSE_MODEL_A = "This is the response from Model A. " * 10
RESPONSE_MODEL_B = "This is the response from Model B. " * 10
RESPONSE_MODEL_C = "This is the response from Model C. " * 10


# ============================================================================
# CHAT ENDPOINTS (existing functionality)
# ============================================================================

def stream_text(text: str):
    """Generator to stream text character by character."""
    for ch in text:
        yield ch
        time.sleep(0.01)


@app.get("/")
async def root():
    """Root endpoint for health check."""
    return {"message": "Welcome to the Document Processor API!"}


@app.post("/result")
async def send_response(item: Item):
    """Stream chat response based on selected model."""
    if item.model == Model.MODEL_A:
        response = RESPONSE_MODEL_A
    elif item.model == Model.MODEL_B:
        response = RESPONSE_MODEL_B
    elif item.model == Model.MODEL_C:
        response = RESPONSE_MODEL_C
    else:
        response = "Model not supported."
    
    return StreamingResponse(stream_text(response), media_type="text/plain")


# ============================================================================
# DOCUMENT PROCESSING ENDPOINTS
# ============================================================================

@app.post("/process", response_model=ProcessResponse)
async def process_document(request: ProcessRequest):
    """
    Process a single document with caching.
    
    Flow:
    1. Check cache first
    2. If not cached, process: PDF → Markdown → Chunks
    3. Save to cache
    4. Return result
    """
    try:
        filename = Path(request.file_path).name
        
        # Check cache first
        cached_path = cache.get(filename)
        if cached_path:
            return ProcessResponse(
                success=True,
                chunks_path=cached_path,
                message=f"Retrieved from cache: {filename}",
                file_type="cached"
            )
        
        # Process file
        result = await processor.process_file(request.file_path, request.enable_ocr)
        
        # Save to cache
        cache.set(filename, result['chunks_path'])
        
        return ProcessResponse(**result)
        
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@app.post("/process-all")
async def process_all_documents(enable_ocr: bool = False):
    """
    Process ALL documents in the input directory.
    
    Returns:
        List of processed files with their status
    """
    results = []
    
    # Get all supported files
    supported_extensions = ['.pdf', '.docx', '.html']
    files = [
        f for f in INPUT_DIR.iterdir() 
        if f.is_file() and f.suffix.lower() in supported_extensions
    ]
    
    for file in files:
        filename = file.name
        
        try:
            # Check cache
            cached_path = cache.get(filename)
            if cached_path:
                results.append({
                    'filename': filename,
                    'status': 'cached',
                    'chunks_path': cached_path
                })
                continue
            
            # Process file
            result = await processor.process_file(file, enable_ocr)
            cache.set(filename, result['chunks_path'])
            
            results.append({
                'filename': filename,
                'status': 'processed',
                'chunks_path': result['chunks_path']
            })
            
        except Exception as e:
            results.append({
                'filename': filename,
                'status': 'failed',
                'error': str(e)
            })
    
    return {
        'total_files': len(files),
        'processed': len([r for r in results if r['status'] == 'processed']),
        'cached': len([r for r in results if r['status'] == 'cached']),
        'failed': len([r for r in results if r['status'] == 'failed']),
        'results': results
    }


@app.post("/clear-cache")
async def clear_cache():
    """Clear the processing cache."""
    cache.clear()
    return {"message": "Cache cleared successfully"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}