"""
Convert DOCX files to PDF using LibreOffice.
"""
from dotenv import load_dotenv
load_dotenv()
import subprocess
from pathlib import Path
import os 
LIBREOFFICE_BIN = os.getenv("LIBREOFFICE_BIN")


if not LIBREOFFICE_BIN:
    raise RuntimeError("LIBREOFFICE_BIN not set")

if not Path(LIBREOFFICE_BIN).exists():
    raise RuntimeError(f"LibreOffice not found at {LIBREOFFICE_BIN}")

def convert_docx_to_pdf(input_path: str | Path, output_path: str | Path) -> Path:
    """
    Convert DOCX file to PDF using LibreOffice headless mode.
    
    Args:
        input_path: Path to input DOCX file
        output_path: Path for output PDF file
        
    Returns:
        Path to the generated PDF file
        
    Raises:
        subprocess.CalledProcessError: If conversion fails
        FileNotFoundError: If input file doesn't exist
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # LibreOffice conversion command
    cmd = [
        LIBREOFFICE_BIN,
        "--headless",
        "--convert-to", "pdf",
        "--outdir", str(output_path.parent),
        str(input_path)
    ]
    
    # Run conversion
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    
    # LibreOffice creates the PDF with the same name as input
    generated_pdf = output_path.parent / f"{input_path.stem}.pdf"
    
    # Rename if needed
    if generated_pdf != output_path:
        generated_pdf.rename(output_path)
    
    return output_path
