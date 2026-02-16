"""
Convert PDF files to Markdown using Docling with hierarchical processing.
"""
from pathlib import Path
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
from hierarchical.postprocessor import ResultPostprocessor


def create_converter(enable_ocr: bool = False) -> DocumentConverter:
    """
    Create a DocumentConverter with specified options.
    
    Args:
        enable_ocr: Whether to enable OCR for scanned PDFs
        
    Returns:
        Configured DocumentConverter instance
    """
    print("Creating converter with OCR enabled:", enable_ocr)
    print("ocr" , enable_ocr)
    print("Creating converter with OCR enabled:", enable_ocr)
    pipeline_options = PdfPipelineOptions(
        do_layout_analysis=True,
        extract_hierarchy=True,
        do_ocr=True,
        do_table_structure=True
    )
    
    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=pipeline_options,
                backend=PyPdfiumDocumentBackend
            )
        }
    )
    
    return converter


def convert_pdf_to_markdown(
    input_path: str | Path,
    output_path: str | Path,
    enable_ocr: bool = False
) -> Path:
    """
    Convert PDF to Markdown with hierarchical structure correction.
    
    Process:
    1. Convert PDF using Docling
    2. Apply hierarchical postprocessing to fix header hierarchy
    3. Export to Markdown format
    
    Args:
        input_path: Path to input PDF file
        output_path: Path for output Markdown file
        enable_ocr: Whether to enable OCR (slower but works with scanned PDFs)
        
    Returns:
        Path to the generated Markdown file
        
    Raises:
        FileNotFoundError: If input file doesn't exist
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create converter
    converter = create_converter(enable_ocr=enable_ocr)
    
    # Convert PDF
    result = converter.convert(str(input_path))
    
    # Apply hierarchical postprocessing (fixes header hierarchy)
    ResultPostprocessor(result, source=str(input_path)).process()
    
    # Export to Markdown
    markdown_content = result.document.export_to_markdown()
    
    # Save to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    return output_path
