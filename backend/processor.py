"""
Document processor - handles business logic separately from API
"""
from pathlib import Path
from typing import Optional
import shutil

from backend.converters.html_to_pdf import convert_html_to_pdf_async
from backend.utils import detect_file_type, generate_output_path
from backend.config import INPUT_DIR, PDF_DIR, CHUNKS_DIR, MARKDOWN_DIR
from backend.converters import (
    convert_docx_to_pdf,
    convert_pdf_to_markdown,
    convert_markdown_to_chunks
)


class DocumentProcessor:
    """
    Handles document processing logic.
    Usage:
        processor = DocumentProcessor()
        result = processor.process_file("myfile.pdf", enable_ocr=False)
    """
    
    def __init__(self, input_dir: Path = INPUT_DIR):
        self.input_dir = input_dir
    
    async def process_file(self, file_path: str, enable_ocr: bool = False) -> dict:
        """
        Process a single document: convert to PDF → Markdown → Chunks
        
        Args:
            file_path: Path to file (relative to input_dir or absolute)
            enable_ocr: Whether to enable OCR for PDFs
            
        Returns:
            dict with: success, chunks_path, message, file_type
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file type not supported
        """
        # Resolve path
        input_path = Path(file_path)
        if not input_path.is_absolute():
            input_path = self.input_dir / file_path
        
        # Check exists
        if not input_path.exists():
            raise FileNotFoundError(f"File not found: {input_path}")
        
        # Detect file type
        file_type = detect_file_type(input_path)
        if not file_type:
            raise ValueError(f"Unsupported file: {input_path.suffix}")
        
        # Step 1: Convert to PDF
        pdf_path = await self._convert_to_pdf(input_path, file_type)
        
        # Step 2: PDF → Markdown
        markdown_path = generate_output_path(pdf_path, MARKDOWN_DIR, ".md")
        convert_pdf_to_markdown(pdf_path, markdown_path, enable_ocr=enable_ocr)
        
        # Step 3: Markdown → Chunks
        chunks_path = generate_output_path(markdown_path, CHUNKS_DIR, ".json")
        convert_markdown_to_chunks(markdown_path, chunks_path)
        
        return {
            'success': True,
            'chunks_path': str(chunks_path),
            'message': f"Successfully processed {input_path.name}",
            'file_type': file_type
        }
    
    async def _convert_to_pdf(self, input_path: Path, file_type: str) -> Path:
        """Convert file to PDF based on type"""
        if file_type == "pdf":
            pdf_path = PDF_DIR / input_path.name
            if input_path != pdf_path:
                shutil.copy2(input_path, pdf_path)
            return pdf_path
        
        elif file_type == "docx":
            pdf_path = generate_output_path(input_path, PDF_DIR, ".pdf")
            convert_docx_to_pdf(input_path, pdf_path)
            return pdf_path
        
        elif file_type == "html":
            pdf_path = generate_output_path(input_path, PDF_DIR, ".pdf")
            from backend.converters.html_to_pdf import convert_html_to_pdf
            await convert_html_to_pdf_async(input_path, pdf_path)
            return pdf_path
        
        else:
            raise ValueError(f"Unsupported file type: {file_type}")