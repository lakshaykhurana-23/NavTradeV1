# NavTrade - Document Processor API

A production-ready document processing pipeline that converts various document formats (DOCX, HTML, PDF) into structured, hierarchical JSON chunks with UUID tracking. Built with FastAPI backend and Streamlit frontend for document processing and LLM chat interactions.

## Overview

NavTrade provides a complete document processing pipeline that:
- Accepts multiple file formats (DOCX, HTML, PDF)
- Converts everything to a standardized PDF format
- Extracts text with hierarchical structure preservation using Docling
- Generates JSON chunks with UUID-based parent-child relationships
- Provides a RESTful API for document processing
- Includes chat and comparison interfaces for LLM interactions

## Features

### Core Capabilities
- **Multi-Format Input Support**: Process DOCX, HTML, and PDF files
- **Standardized PDF Conversion**: All documents converted to PDF for consistent processing
- **Intelligent Text Extraction**: Uses Docling library with OCR support for scanned documents
- **Hierarchical Structure Preservation**: Maintains document hierarchy (H1, H2, H3)
- **UUID-Based Chunk Tracking**: Each section gets a unique identifier with parent relationships
- **RESTful API**: FastAPI-based endpoints for document processing
- **Interactive Frontends**: Streamlit-based chat and comparison interfaces

### Technical Features
- Async/sync converter support for optimal performance
- Configurable OCR processing
- Hierarchical postprocessing for improved structure detection
- Markdown intermediate format for better text handling
- JSON output with complete metadata

## Architecture

### Processing Pipeline

```
Input Document (DOCX/HTML/PDF)
         ↓
   [File Type Detection]
         ↓
    ┌────────────────┬─────────────────┬──────────────┐
    │   DOCX         │   HTML          │   PDF        │
    │   (LibreOffice)│   (Playwright)  │   (Direct)   │
    └────────────────┴─────────────────┴──────────────┘
         ↓
    [Unified PDF]
         ↓
    [Docling Conversion]
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
    [UUID Assignment & Parent Tracking]
    - Unique IDs for each chunk
    - Parent-child relationships
         ↓
    [JSON Output with Metadata]
```

### Directory Structure

```
NavTradeV1/
├── backend/
│   ├── converters/              # Document conversion modules
│   │   ├── __init__.py
│   │   ├── docx_to_pdf.py      # LibreOffice-based DOCX→PDF
│   │   ├── html_to_pdf.py      # Playwright-based HTML→PDF
│   │   ├── pdf_to_markdown.py  # Docling-based PDF→Markdown
│   │   └── markdown_to_chunks.py # Markdown→JSON chunks
│   ├── models/                  # Pydantic schemas
│   │   ├── __init__.py
│   │   └── schemas.py          # Request/response models
│   ├── __init__.py
│   ├── config.py               # Configuration & paths
│   ├── main.py                 # FastAPI application
│   └── utils.py                # Helper functions
├── frontend/
│   ├── __init__.py
│   ├── chat.py                 # Single model chat UI
│   └── compare.py              # Model comparison UI
├── data/
│   ├── input/                  # Raw input files (all formats)
│   ├── pdf/                    # Converted PDF files
│   ├── markdown/               # Intermediate markdown files
│   └── chunks/                 # Final JSON chunks output
├── pyproject.toml              # Python dependencies (UV)
├── uv.lock                     # Dependency lock file
├── run.sh                      # Quick start launcher
├── README.md                   # This file
└── QUICKSTART.md              # Installation & running guide
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

# Install system dependencies (see QUICKSTART.md)

# Install Playwright browsers
uv run playwright install chromium
```

## LibreOffice Configuration

### Important: Custom LibreOffice Path

If LibreOffice is installed in a non-standard location, you need to configure the path:

**1. Create a `.env` file in the NavTradeV1 directory:**
```bash
touch .env
```

**2. Add the LibreOffice binary path:**

**macOS Example:**
```bash
LIBREOFFICE_BIN="/Applications/LibreOffice.app/Contents/MacOS/soffice"
```

**Linux Example:**
```bash
LIBREOFFICE_BIN="/usr/bin/soffice"
```

**Windows Example:**
```bash
LIBREOFFICE_BIN="C:\\Program Files\\LibreOffice\\program\\soffice.exe"
```

**3. Finding Your LibreOffice Path:**

**macOS:**
```bash
# Default location
/Applications/LibreOffice.app/Contents/MacOS/soffice

# Or find it
mdfind -name soffice | grep LibreOffice
```

**Linux:**
```bash
# Default location
/usr/bin/soffice

# Or find it
which soffice
# OR
whereis soffice
```

**Windows:**
```bash
# Default locations
C:\Program Files\LibreOffice\program\soffice.exe
C:\Program Files (x86)\LibreOffice\program\soffice.exe

# Or search in Command Prompt
where soffice
```

**Note:** The `LIBREOFFICE_BIN` environment variable is read by `backend/converters/docx_to_pdf.py`. If not set, it will use system defaults.

## API Documentation

### Endpoints

#### 1. Health Check
```http
GET /
GET /health
```

**Response:**
```json
{
  "message": "Welcome to the Document Processor API!",
  "status": "healthy"
}
```

#### 2. Process Document
```http
POST /process
Content-Type: application/json
```

**Request Body:**
```json
{
  "file_path": "example.docx",
  "enable_ocr": false
}
```

**Parameters:**
- `file_path` (string, required): Path to input file relative to `data/input/` directory or absolute path
- `enable_ocr` (boolean, optional): Enable OCR for scanned PDFs (default: false)

**Response:**
```json
{
  "success": true,
  "chunks_path": "data/chunks/example.json",
  "message": "Successfully processed example.docx",
  "file_type": "docx"
}
```

**Supported File Types:**
- `.pdf` - PDF documents
- `.docx`, `.doc` - Microsoft Word documents
- `.html`, `.htm` - HTML files

#### 3. Chat Response (Streaming)
```http
POST /result
Content-Type: application/json
```

**Request Body:**
```json
{
  "userInput": "Your message here",
  "model": "model_a",
  "threadId": "unique-thread-id"
}
```

**Response:** Streaming text/plain response

## Output Format

### JSON Chunk Structure

Each processed document generates a JSON file with the following structure:

```json
[
  {
    "chunk_id": "550e8400-e29b-41d4-a716-446655440000",
    "self": {
      "header": "h2",
      "title": "Section Title"
    },
    "parents": [
      {
        "id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
        "header": "h1",
        "title": "Parent Section"
      }
    ],
    "text": "The actual content of this section..."
  }
]
```

**Field Descriptions:**
- `chunk_id`: UUID v4 unique identifier for this chunk
- `self.header`: Header level (h1, h2, h3, or null for content without headers)
- `self.title`: Title of this section
- `parents`: Array of parent sections in hierarchical order
- `text`: The actual text content of the chunk

## Usage Examples

### Python Example
```python
import requests

# Process a document
response = requests.post(
    "http://localhost:8000/process",
    json={
        "file_path": "report.docx",
        "enable_ocr": False
    }
)

result = response.json()
print(f"Success: {result['success']}")
print(f"Output: {result['chunks_path']}")
```

### cURL Example
```bash
# Process a PDF with OCR
curl -X POST "http://localhost:8000/process" \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "scanned_document.pdf",
    "enable_ocr": true
  }'
```

### Using Absolute Paths
```python
# You can also provide absolute paths
response = requests.post(
    "http://localhost:8000/process",
    json={
        "file_path": "/absolute/path/to/document.pdf",
        "enable_ocr": False
    }
)
```

## Configuration

### Environment Variables

Create a `.env` file in the NavTradeV1 directory:

```bash
# LibreOffice binary path (required if non-standard installation)
LIBREOFFICE_BIN="/Applications/LibreOffice.app/Contents/MacOS/soffice"

# Data directory (optional, defaults to ./data)
DATA_DIR="/custom/path/to/data"
```

### Configuration File

Edit `backend/config.py` to customize:

**Directory Paths:**
```python
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
INPUT_DIR = DATA_DIR / "input"
PDF_DIR = DATA_DIR / "pdf"
MARKDOWN_DIR = DATA_DIR / "markdown"
CHUNKS_DIR = DATA_DIR / "chunks"
```

**Supported Formats:**
```python
SUPPORTED_FORMATS = {
    "pdf": [".pdf"],
    "docx": [".docx", ".doc"],
    "html": [".html", ".htm"]
}
```

**Chunk Headers:**
```python
CHUNK_HEADERS = [
    ("#", "header1"),
    ("##", "header2"),
    ("###", "header3"),
]
```

## Development

### Running in Development Mode

**Start Backend with Auto-reload:**
```bash
uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

**Start Frontend Applications:**
```bash
# Chat interface
uv run streamlit run frontend/chat.py

# Comparison interface
uv run streamlit run frontend/compare.py
```

### API Documentation

Once the backend is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Code Quality Tools

Install development dependencies:
```bash
uv sync --extra dev
```

**Format Code:**
```bash
uv run black backend/ frontend/
```

**Lint Code:**
```bash
uv run ruff check backend/ frontend/
```

**Run Tests:**
```bash
uv run pytest
```

## Troubleshooting

### Common Issues

#### LibreOffice Not Found
```bash
# Verify LibreOffice installation
which soffice  # Linux/macOS
where soffice  # Windows

# Install if missing
brew install libreoffice  # macOS
sudo apt-get install libreoffice  # Ubuntu/Debian
```

**If LibreOffice is installed but not found:**
1. Find the LibreOffice binary path (see instructions above)
2. Create a `.env` file in NavTradeV1 directory
3. Add `LIBREOFFICE_BIN="/path/to/soffice"`

#### Playwright Browser Issues
```bash
# Reinstall Chromium browser
uv run playwright install chromium

# Install system dependencies (Linux only)
uv run playwright install-deps chromium
```

#### Port Already in Use
```bash
# Use a different port
uv run uvicorn backend.main:app --port 8001
```

#### Module Not Found Errors
```bash
# Reinstall all dependencies
uv sync

# Force reinstall
rm -rf .venv
uv sync
```

#### Permission Issues
```bash
# Ensure data directories are writable
chmod -R 755 data/
```

### OCR Performance

If OCR processing is slow:
- Reduce image resolution before processing
- Process only necessary pages
- Use `enable_ocr=False` for text-based PDFs

### Memory Issues

For large documents:
- Process documents in smaller batches
- Increase system RAM allocation
- Monitor memory usage during processing

## Performance Considerations

- **DOCX to PDF**: ~1-3 seconds per file (LibreOffice headless)
- **HTML to PDF**: ~2-5 seconds per file (Playwright rendering)
- **PDF to Markdown**: ~5-30 seconds depending on size and complexity
- **Markdown to Chunks**: <1 second for most documents
- **OCR Processing**: Adds 10-60 seconds per page for scanned documents

## Security Considerations

- Input validation performed on file paths
- Supported file type checking
- Isolated processing environment recommended for production
- No authentication included (add authentication layer for production use)
- File size limits should be implemented for production deployments

## Dependencies

### Core Libraries
- **FastAPI**: Modern web framework for building APIs
- **Uvicorn**: ASGI server implementation
- **Pydantic**: Data validation using Python type annotations
- **Docling**: Advanced PDF to Markdown conversion
- **LangChain Text Splitters**: Markdown header-based text splitting
- **Playwright**: Browser automation for HTML to PDF
- **Streamlit**: Frontend framework for web applications

### System Dependencies
- **LibreOffice**: Office document conversion
- **Chromium**: HTML rendering and PDF generation

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Run code quality checks
6. Submit a pull request

## Support

For issues, questions, or contributions:
- Create an issue in the repository
- Check existing documentation
- Review the code explanation guide

## Acknowledgments

- Docling team for the excellent PDF processing library
- FastAPI and Streamlit communities
- LangChain for text splitting utilities