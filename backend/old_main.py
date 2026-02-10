"""
FastAPI application for document processing and chat.
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
import time
from pathlib import Path

from backend.models import ProcessRequest, ProcessResponse, Item, Model
from backend.utils import detect_file_type, ensure_path_exists, generate_output_path
from backend.config import INPUT_DIR, PDF_DIR, CHUNKS_DIR , MARKDOWN_DIR
from backend.converters import (
    convert_docx_to_pdf,
    convert_html_to_pdf,
    convert_pdf_to_markdown,
    convert_markdown_to_chunks
)

app = FastAPI(title="Document Processor API", version="1.0.0")

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
    """
    Stream chat response based on selected model.
    
    Args:
        item: Chat request with user input, model, and thread ID
        
    Returns:
        Streaming response with model output
    """
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
# DOCUMENT PROCESSING ENDPOINT
# ============================================================================

@app.post("/process", response_model=ProcessResponse)
async def process_document(request: ProcessRequest):
    """
    Process a document: convert to PDF (if needed) → Markdown → JSON chunks.
    
    Flow:
    1. Detect file type (PDF, DOCX, or HTML) from data/input/
    2. Convert to PDF if necessary → save to data/pdf/
    3. Convert PDF to Markdown using Docling → save to data/markdown/
    4. Convert Markdown to hierarchical chunks with UUIDs → save to data/chunks/
    5. Return path to final chunks
    
    Args:
        request: Processing request with file path (relative to data/input/)
        
    Returns:
        ProcessResponse with status and output path
        
    Example:
        Request: {"file_path": "report.docx"}
        → Looks for: data/input/report.docx
        → Creates: data/pdf/report.pdf
        → Creates: data/markdown/report.md
        → Creates: data/chunks/report.json
        
    Raises:
        HTTPException: If file is not found or processing fails
    """
    try:
        # Handle both absolute and relative paths
        # User can provide: "report.docx" or "/absolute/path/to/report.docx"
        input_path = Path(request.file_path)
        
        # If absolute path is provided, use it directly
        # If relative path, assume it's relative to INPUT_DIR
        if not input_path.is_absolute():
            input_path = INPUT_DIR / request.file_path
        
        # Validate input file exists
        if not input_path.exists():
            # Provide helpful error message based on path type
            if Path(request.file_path).is_absolute():
                raise HTTPException(
                    status_code=404,
                    detail=f"File not found: {request.file_path}"
                )
            else:
                raise HTTPException(
                    status_code=404,
                    detail=f"File not found in data/input/: {request.file_path}. Please check that the file exists in the input directory."
                )
        
        # Detect file type
        file_type = detect_file_type(input_path)
        if not file_type:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {input_path.suffix}"
            )
        
        # Step 1: Convert to PDF if needed → save to data/pdf/
        if file_type == "pdf":
            pdf_path = PDF_DIR / input_path.name  # Copy to pdf folder for consistency
            if input_path != pdf_path:
                import shutil
                shutil.copy2(input_path, pdf_path)
        elif file_type == "docx":
            pdf_path = generate_output_path(input_path, PDF_DIR, ".pdf")
            convert_docx_to_pdf(input_path, pdf_path)
        elif file_type == "html":
            pdf_path = generate_output_path(input_path, PDF_DIR, ".pdf")
            # Use async version of HTML to PDF converter
            from backend.converters.html_to_pdf import convert_html_to_pdf_async
            await convert_html_to_pdf_async(input_path, pdf_path)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_type}")
        
        # Step 2: Convert PDF to Markdown → save to data/markdown/
        markdown_path = generate_output_path(pdf_path, MARKDOWN_DIR, ".md")
        convert_pdf_to_markdown(pdf_path, markdown_path, enable_ocr=request.enable_ocr)
        
        # Step 3: Convert Markdown to chunks → save to data/chunks/
        chunks_path = generate_output_path(markdown_path, CHUNKS_DIR, ".json")
        convert_markdown_to_chunks(markdown_path, chunks_path)
        
        return ProcessResponse(
            success=True,
            chunks_path=str(chunks_path),
            message=f"Successfully processed {input_path.name}",
            file_type=file_type
        )
        
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)