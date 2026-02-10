# NavTrade - Document Processor API

A production-ready document processing pipeline that converts various document formats (DOCX, HTML, PDF) into structured, hierarchical JSON chunks with UUID tracking and metadata. Built with FastAPI backend and Streamlit frontend.

## Overview

NavTrade provides a complete document processing pipeline that:
- Processes multiple file formats (DOCX, HTML, PDF) from a local input folder
- Matches files with metadata from a configuration sheet
- Converts documents to standardized PDF format
- Extracts text with hierarchical structure preservation using Docling
- Generates individual JSON chunk files with UUID-based parent-child relationships
- Includes token counting for each chunk
- Provides a RESTful API for document processing
- Includes chat and comparison interfaces for LLM interactions

## Features

### Core Capabilities
- **Multi-Format Input Support**: Process DOCX, HTML, and PDF files
- **Config-Based Metadata**: Match files with metadata from Excel/CSV config sheet
- **Smart Processing**: Only process files with meaningful metadata
- **Standardized PDF Conversion**: All documents converted to PDF for consistent processing
- **Intelligent Text Extraction**: Uses Docling library with GPU acceleration (MPS on Apple Silicon)
- **Hierarchical Structure Preservation**: Maintains document hierarchy (H1, H2, H3)
- **Individual Chunk Files**: Each document gets a folder with separate chunk files
- **Token Counting**: Automatic token count for each chunk using tiktoken
- **UUID-Based Chunk Tracking**: Each section gets a unique identifier with parent relationships
- **RESTful API**: FastAPI-based endpoints for document processing

### Technical Features
- GPU acceleration on Apple Silicon (MPS) for faster processing
- Async/sync converter support for optimal performance
- Configurable OCR processing
- Hierarchical postprocessing for improved structure detection
- Markdown intermediate format for better text handling
- JSON output with complete metadata and token counts

## Architecture

### Processing Pipeline

```
Files in data/input/ (D01.pdf, D02.html, etc.)
         ↓
   [Extract Document ID from Filename]
         ↓
   [Match with Config Sheet by Id Column]
         ↓
   [Check Metadata: Keywords/Categories/Description]
         ↓
   [Skip if all metadata empty]
         ↓
    ┌────────────────┬─────────────────┬──────────────┐
    │   DOCX         │   HTML          │   PDF        │
    │   (LibreOffice)│   (Playwright)  │   (Direct)   │
    └────────────────┴─────────────────┴──────────────┘
         ↓
    [Unified PDF]
         ↓
    [Docling Conversion with GPU Acceleration]
    - Layout analysis
    - Hierarchy extraction
    - OCR (optional)
    - Table structure detection
         ↓
    [Hierarchical Postprocessing]
    - Header hierarchy correction
    - Structure validation
         ↓
    [Markdown Export]
         ↓
    [LangChain Text Splitter]
    - Split by headers
    - Preserve metadata
         ↓
    [Token Counting (tiktoken)]
         ↓
    [UUID Assignment & Parent Tracking]
    - Unique IDs for each chunk
    - Parent-child relationships
         ↓
    [Individual Chunk Files with Metadata]
    → data/chunks/D01/chunk_001.json
    → data/chunks/D01/chunk_002.json
    → data/chunks/D02/chunk_001.json
```

### Directory Structure

```
NavTradeV1/
├── backend/
│   ├── converters/                  # Document conversion modules
│   │   ├── __init__.py
│   │   ├── docx_to_pdf.py          # LibreOffice-based DOCX→PDF
│   │   ├── html_to_pdf.py          # Playwright-based HTML→PDF
│   │   ├── pdf_to_markdown.py      # Docling-based PDF→Markdown
│   │   └── markdown_to_chunks.py   # Markdown→JSON chunks with tokens
│   ├── models/                      # Pydantic schemas
│   │   ├── __init__.py
│   │   └── schemas.py              # Request/response models
│   ├── __init__.py
│   ├── config.py                   # Configuration & paths
│   ├── main.py                     # FastAPI application
│   ├── input_folder_processor.py   # Process files from input folder
│   └── utils.py                    # Helper functions
├── frontend/
│   ├── __init__.py
│   ├── chat.py                     # Single model chat UI
│   └── compare.py                  # Model comparison UI
├── data/
│   ├── input/                      # Raw input files (D01.pdf, D02.html, etc.)
│   ├── pdf/                        # Converted PDF files
│   ├── markdown/                   # Intermediate markdown files
│   └── chunks/                     # Final JSON chunks (folders per document)
│       ├── D01/                    # Document D01 chunks
│       │   ├── chunk_001.json
│       │   ├── chunk_002.json
│       │   └── chunk_003.json
│       ├── D02/                    # Document D02 chunks
│       │   ├── chunk_001.json
│       │   └── chunk_002.json
│       └── ...
├── config.xlsx                     # Metadata configuration sheet
├── process_all.py                  # Script to process all input files
├── pyproject.toml                  # Python dependencies (UV)
├── uv.lock                         # Dependency lock file
├── README.md                       # This file
└── QUICKSTART.md                   # Installation & running guide
```

## System Requirements

### Software Requirements
- Python 3.10 or higher
- [UV](https://github.com/astral-sh/uv) package manager
- LibreOffice (for DOCX to PDF conversion)
- Chromium browser (installed via Playwright for HTML to PDF)

### Hardware Requirements
- Minimum 4GB RAM (8GB+ recommended for OCR)
- 2GB free disk space for dependencies and processing
- **Apple Silicon (M1/M2/M3)**: Benefits from GPU acceleration (MPS) - 2-4x faster
- **Intel/AMD**: Uses CPU processing (slower but functional)

## Installation

See [QUICKSTART.md](QUICKSTART.md) for detailed installation and running instructions.

**Quick Setup:**
```bash
# Install UV package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Navigate to project directory
cd NavTradeV1

# Install Python dependencies
uv sync

# Install additional dependencies
uv add tiktoken pandas openpyxl

# Install Playwright browsers
uv run playwright install chromium
```

## GPU Acceleration (Apple Silicon)

If you see this message during processing:
```
Accelerator device: 'mps'
```

**This is GOOD!** It means:
- ✅ You have Apple Silicon (M1/M2/M3)
- ✅ GPU acceleration is enabled
- ✅ Processing is 2-4x faster than CPU-only

**Performance:**
- With MPS (GPU): ~5-15 seconds per page
- CPU only: ~30-60 seconds per page

## Configuration

### Config Sheet Setup

Create `config.xlsx` in the NavTradeV1 directory with these columns:

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| **Id** | string | Document ID (matches filename) | D01, D02, D03 |
| Format | string | Document type | PDF, DOCX, Webpage |
| Description | string | Document description | "Tax form instructions" |
| Keywords | list | Comma-separated keywords | "tax, form, 2024" |
| Categories | list | Comma-separated category IDs | "C01_S02, C03_S01" |

**Example config.xlsx:**

| Id | Format | Description | Keywords | Categories |
|----|--------|-------------|----------|------------|
| D01 | PDF | Tax form 1040 | tax, form, federal | C01_S02, C03_S01 |
| D02 | HTML | Python tutorial | python, programming | C02_S05 |
| D03 | DOCX | Sales report | sales, Q4, report | C01_S02 |

**Processing Rules:**
- Files are matched by Id (D01.pdf → looks for Id "D01" in config)
- Only processes if at least one of Keywords, Categories, or Description has content
- If all three are empty, file is skipped

### LibreOffice Configuration

If LibreOffice is installed in a non-standard location, create a `.env` file in NavTradeV1:

**macOS:**
```bash
LIBREOFFICE_BIN="/Applications/LibreOffice.app/Contents/MacOS/soffice"
```

**Linux:**
```bash
LIBREOFFICE_BIN="/usr/bin/soffice"
```

**Windows:**
```bash
LIBREOFFICE_BIN="C:\\Program Files\\LibreOffice\\program\\soffice.exe"
```

## Usage

### Process All Files

**1. Upload files to data/input/:**
```bash
# Files must be named with document ID
cp your_file.pdf data/input/D01.pdf
cp another_file.html data/input/D02.html
cp document.docx data/input/D03.docx
```

**2. Create config.xlsx** with metadata for each document

**3. Run the processor:**
```bash
python process_all.py
```

### Example Output

```
======================================================================
PROCESSING ALL FILES FROM data/input/
======================================================================
Found 5 file(s) in data/input/

[1/5] File: D01.pdf
  Document ID: D01
  Type: PDF
  Keywords: ['tax', 'form', 'federal']
  Categories: ['C01_S02', 'C03_S01']
  Extracting text to Markdown...
Accelerator device: 'mps'  ← GPU acceleration active
  Generating chunks with metadata and token counts...
  ✓ Success: data/chunks/D01
  ✓ Created 12 chunks

======================================================================
PROCESSING SUMMARY
======================================================================
Total files found:              5
Successfully processed:         4
Skipped (no metadata):          1
Skipped (no ID):                0
Failed:                         0
Total chunks created:           55
======================================================================
```

## Output Format

### Chunk File Structure

Each document creates a folder with individual chunk files:

```
data/chunks/D01/
├── chunk_001.json
├── chunk_002.json
└── chunk_003.json
```

### Individual Chunk Format

```json
{
  "chunk": "Form 1040 is the standard federal income tax form...",
  "metadata": {
    "chunk_id": "uuid",
    "self": {"header": "h1", "title": "Form 1040 Instructions"},
    "parents": [],
    "tokens": "45",
    "document_id": "D01",
    "document_type": "PDF",
    "document_description": "Tax form 1040",
    "document_keywords": ["tax", "form", "federal"],
    "category_ids": ["C01_S02", "C03_S01"]
  }
}
```

## Performance

### Processing Times (with GPU acceleration on Apple Silicon):
- **DOCX to PDF**: ~1-3 seconds per file
- **HTML to PDF**: ~2-5 seconds per file
- **PDF to Markdown**: ~5-15 seconds with MPS (GPU)
- **PDF to Markdown**: ~30-60 seconds CPU only
- **Markdown to Chunks**: <1 second
- **OCR Processing**: Adds 10-30 seconds per page with MPS

### Hardware Acceleration:
- **Apple Silicon (M1/M2/M3)**: Uses MPS (Metal Performance Shaders) - 2-4x speedup
- **NVIDIA GPU**: Uses CUDA (if available)
- **Intel/AMD**: Falls back to CPU

## Troubleshooting

### File Not Processing

**Check:**
1. Is file in `data/input/`?
2. Is filename format correct? (D01.pdf, D02.html, etc.)
3. Does config have `Id` column with matching ID?
4. Does at least one of Keywords/Categories/Description have content?

### MPS/GPU Messages

If you see:
```
Accelerator device: 'mps'
```
This is **normal and good** - GPU acceleration is working!

### LibreOffice Not Found

1. Find LibreOffice path: `which soffice` (macOS/Linux) or `where soffice` (Windows)
2. Create `.env` file in NavTradeV1 directory
3. Add `LIBREOFFICE_BIN="/path/to/soffice"`

## Dependencies

### Core Libraries
- **FastAPI**: Web framework
- **Docling**: PDF processing with ML models
- **LangChain**: Text splitting
- **tiktoken**: Token counting
- **pandas/openpyxl**: Config sheet reading
- **Playwright**: HTML to PDF conversion

### System Dependencies
- **LibreOffice**: Office document conversion
- **Chromium**: HTML rendering

## License

MIT License

## Acknowledgments

- Docling team for PDF processing with GPU acceleration
- FastAPI and Streamlit communities
- LangChain for text splitting utilities
- OpenAI for tiktoken library