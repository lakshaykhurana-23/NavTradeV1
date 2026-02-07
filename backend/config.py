"""
Configuration settings for the document processor.
"""
from pathlib import Path
import os

# Base directories
BASE_DIR = Path(__file__).parent.parent

# Allow custom data directory via environment variable
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))

# Data subdirectories - NEW STRUCTURE
INPUT_DIR = DATA_DIR / "input"          # All raw input files (PDF, DOCX, HTML)
PDF_DIR = DATA_DIR / "pdf"              # All converted PDFs
MARKDOWN_DIR = DATA_DIR / "markdown"    # All converted Markdown files
CHUNKS_DIR = DATA_DIR / "chunks"        # All final JSON chunks

# Create directories if they don't exist
INPUT_DIR.mkdir(parents=True, exist_ok=True)
PDF_DIR.mkdir(parents=True, exist_ok=True)
MARKDOWN_DIR.mkdir(parents=True, exist_ok=True)
CHUNKS_DIR.mkdir(parents=True, exist_ok=True)

# Supported file types
SUPPORTED_FORMATS = {
    "pdf": [".pdf"],
    "docx": [".docx", ".doc"],
    "html": [".html", ".htm"]
}

# Processing settings
CHUNK_HEADERS = [
    ("#", "header1"),
    ("##", "header2"),
    ("###", "header3"),
]