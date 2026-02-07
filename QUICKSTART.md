# Quick Start Guide - NavTrade

Get the NavTrade Document Processor API running in under 10 minutes.

## Prerequisites

Before you begin, ensure you have:
- **Operating System**: macOS, Linux, or Windows
- **Python**: Version 3.10 or higher
- **Disk Space**: At least 2GB free

## Installation Steps

### 1. Install UV Package Manager

UV is a fast Python package manager that handles all dependencies.

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell):**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Verify Installation:**
```bash
uv --version
```

### 2. Install Python Dependencies

Navigate to the NavTradeV1 directory and install all Python packages:

```bash
cd NavTradeV1
uv sync
```

This command:
- Creates a virtual environment
- Installs all dependencies from `pyproject.toml`
- Locks dependency versions in `uv.lock`

### 3. Install LibreOffice (Required for DOCX Conversion)

LibreOffice is used to convert DOCX files to PDF format.

**macOS:**
```bash
brew install libreoffice
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y libreoffice
```

**Fedora/RHEL:**
```bash
sudo dnf install libreoffice
```

**Windows:**
1. Download from https://www.libreoffice.org/download/download/
2. Run the installer
3. Follow installation prompts

**Verify Installation:**
```bash
# macOS/Linux
which soffice
libreoffice --version

# Windows (Command Prompt)
where soffice
```

### 4. Configure LibreOffice Path (If Needed)

If LibreOffice is installed in a non-standard location, create a `.env` file:

```bash
# Create .env file in NavTradeV1 directory
cd NavTradeV1
touch .env
```

Add the LibreOffice binary path to `.env`:

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

**Finding Your LibreOffice Installation:**

**macOS:**
```bash
# Default location
ls /Applications/LibreOffice.app/Contents/MacOS/soffice

# Or search
mdfind -name soffice | grep LibreOffice
```

**Linux:**
```bash
# Common locations
which soffice
whereis soffice

# Check default path
ls /usr/bin/soffice
```

**Windows:**
```bash
# Search in Command Prompt
where soffice

# Common locations
C:\Program Files\LibreOffice\program\soffice.exe
C:\Program Files (x86)\LibreOffice\program\soffice.exe
```

### 5. Install Playwright Browsers

Playwright is used for converting HTML files to PDF.

```bash
uv run playwright install chromium
```

**Linux Additional Step:**
```bash
# Install system dependencies for Chromium
uv run playwright install-deps chromium
```

This downloads and configures Chromium browser (~300MB).

### 6. Verify Data Directories

The following directories should exist (created automatically):

```bash
ls -la data/
# Should show:
# data/input/     - Place your input files here
# data/pdf/       - PDF files are saved here
# data/markdown/  - Markdown files are saved here
# data/chunks/    - Final JSON chunks are saved here
```

## Running the Application

### Option 1: Quick Start Script (Recommended)

Run the interactive menu:

```bash
chmod +x run.sh  # First time only
./run.sh
```

This presents a menu to:
1. Start the backend server
2. Start the chat interface
3. Start the comparison interface
4. Start all services
5. Exit

### Option 2: Manual Commands

**Start the Backend API:**
```bash
uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: http://localhost:8000

**Start the Chat Interface (in a new terminal):**
```bash
uv run streamlit run frontend/chat.py
```

Opens in browser at: http://localhost:8501

**Start the Comparison Interface (in a new terminal):**
```bash
uv run streamlit run frontend/compare.py
```

Opens in browser at: http://localhost:8502

## Testing the Installation

### 1. Check API Health

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "healthy"}
```

### 2. View API Documentation

Open in browser: http://localhost:8000/docs

You should see the interactive Swagger UI documentation.

### 3. Process a Test Document

**Prepare a test file:**
```bash
# Copy any PDF, DOCX, or HTML file to the input directory
cp /path/to/your/document.pdf data/input/test.pdf
```

**Process via cURL:**
```bash
curl -X POST "http://localhost:8000/process" \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "test.pdf",
    "enable_ocr": false
  }'
```

**Expected response:**
```json
{
  "success": true,
  "chunks_path": "data/chunks/test.json",
  "message": "Successfully processed test.pdf",
  "file_type": "pdf"
}
```

**Verify output:**
```bash
cat data/chunks/test.json
```

You should see JSON with chunks containing `chunk_id`, `self`, `parents`, and `text` fields.

## Usage Examples

### Example 1: Process a DOCX File

```bash
# 1. Place your DOCX file in the input directory
cp /path/to/report.docx data/input/

# 2. Process it
curl -X POST "http://localhost:8000/process" \
  -H "Content-Type: application/json" \
  -d '{"file_path": "report.docx", "enable_ocr": false}'

# 3. View the output
cat data/chunks/report.json
```

### Example 2: Process an HTML File

```bash
# 1. Place HTML file
cp /path/to/webpage.html data/input/

# 2. Process it
curl -X POST "http://localhost:8000/process" \
  -H "Content-Type: application/json" \
  -d '{"file_path": "webpage.html", "enable_ocr": false}'

# 3. Check intermediate PDF
ls data/pdf/webpage.pdf

# 4. View final chunks
cat data/chunks/webpage.json
```

### Example 3: Process with OCR (Scanned PDF)

```bash
# For scanned documents or PDFs with images
curl -X POST "http://localhost:8000/process" \
  -H "Content-Type: application/json" \
  -d '{"file_path": "scanned.pdf", "enable_ocr": true}'
```

### Example 4: Using Python

```python
import requests
import json

# Process a document
response = requests.post(
    "http://localhost:8000/process",
    json={
        "file_path": "example.docx",
        "enable_ocr": False
    }
)

# Check result
result = response.json()
print(f"Success: {result['success']}")
print(f"Chunks saved to: {result['chunks_path']}")

# Read the chunks
with open(result['chunks_path'], 'r') as f:
    chunks = json.load(f)
    
print(f"Total chunks: {len(chunks)}")
for chunk in chunks[:3]:  # Print first 3 chunks
    print(f"\nChunk ID: {chunk['chunk_id']}")
    print(f"Header: {chunk['self']['header']}")
    print(f"Title: {chunk['self']['title']}")
    print(f"Text: {chunk['text'][:100]}...")  # First 100 chars
```

## Workflow Summary

```
1. Place file in data/input/
         ↓
2. Call /process API endpoint
         ↓
3. System detects file type (PDF/DOCX/HTML)
         ↓
4. Converts to PDF (if needed)
         ↓
5. Extracts text to Markdown
         ↓
6. Splits into hierarchical chunks
         ↓
7. Generates JSON with UUIDs
         ↓
8. Saves to data/chunks/
```

## Common Tasks

### Add and Process Multiple Documents

```bash
# Copy multiple files
cp document1.pdf document2.docx document3.html data/input/

# Process each one
for file in data/input/*; do
  filename=$(basename "$file")
  curl -X POST "http://localhost:8000/process" \
    -H "Content-Type: application/json" \
    -d "{\"file_path\": \"$filename\", \"enable_ocr\": false}"
done
```

### Check Processing Status

```bash
# View API logs (if running in terminal)
# Check the terminal where uvicorn is running

# List all processed chunks
ls -lh data/chunks/

# Count total chunks in a file
cat data/chunks/example.json | jq '. | length'
```

### Clean Up Processed Files

```bash
# Remove all processed files (keeps input)
rm -rf data/pdf/*
rm -rf data/markdown/*
rm -rf data/chunks/*

# Or remove everything including input
rm -rf data/input/*
rm -rf data/pdf/*
rm -rf data/markdown/*
rm -rf data/chunks/*
```

## Troubleshooting

### Issue: "Module not found" errors

```bash
# Solution: Reinstall dependencies
uv sync

# If that doesn't work, remove and recreate environment
rm -rf .venv
uv sync
```

### Issue: "Port 8000 already in use"

```bash
# Solution 1: Use a different port
uv run uvicorn backend.main:app --port 8001

# Solution 2: Find and kill the process using port 8000
# Linux/macOS:
lsof -ti:8000 | xargs kill -9

# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Issue: "LibreOffice not found"

```bash
# Verify installation
which soffice  # Linux/macOS
where soffice  # Windows

# If not found, reinstall LibreOffice (see step 3)
# Then configure the path in .env (see step 4)
```

**Solution Steps:**
1. Find where LibreOffice is installed using the commands above
2. Create a `.env` file in the NavTradeV1 directory
3. Add the line: `LIBREOFFICE_BIN="/path/to/soffice"`
4. Restart the backend server

### Issue: "Playwright browser not found"

```bash
# Reinstall Chromium
uv run playwright install chromium

# Linux: Also install system dependencies
uv run playwright install-deps chromium
```

### Issue: "Permission denied" errors

```bash
# Make data directories writable
chmod -R 755 data/

# Make run script executable
chmod +x run.sh
```

### Issue: Processing fails for specific document

```bash
# Try with OCR enabled
curl -X POST "http://localhost:8000/process" \
  -H "Content-Type: application/json" \
  -d '{"file_path": "problem.pdf", "enable_ocr": true}'

# Check the logs for detailed error messages
# The terminal running uvicorn will show detailed traceback
```

### Issue: Slow processing

**Causes and solutions:**
- **OCR is enabled**: Disable OCR for text-based PDFs
- **Large file**: Process smaller files or increase timeout
- **System resources**: Close other applications to free RAM
- **First run**: Initial processing may be slower due to model loading

## Next Steps

Once everything is working:

1. Explore the API documentation at http://localhost:8000/docs
2. Try the chat interface at http://localhost:8501
3. Test the comparison interface at http://localhost:8502
4. Process your own documents
5. Integrate the API into your application
6. Read the full README.md for advanced configuration
7. Review CODE_EXPLANATION.md to understand the implementation

## Getting Help

- **API Docs**: http://localhost:8000/docs
- **Check logs**: Terminal where uvicorn is running
- **Verify setup**: Run health check - `curl http://localhost:8000/health`
- **Read documentation**: README.md and CODE_EXPLANATION.md

## Summary of Commands

```bash
# Installation
curl -LsSf https://astral.sh/uv/install.sh | sh
cd NavTradeV1
uv sync
brew install libreoffice  # or apt-get/dnf
uv run playwright install chromium

# Running
uv run uvicorn backend.main:app --reload
uv run streamlit run frontend/chat.py
uv run streamlit run frontend/compare.py

# Testing
curl http://localhost:8000/health
curl -X POST "http://localhost:8000/process" \
  -H "Content-Type: application/json" \
  -d '{"file_path": "test.pdf"}'

# Viewing
open http://localhost:8000/docs
open http://localhost:8501
open http://localhost:8502
```

You're all set! Start processing documents with NavTrade.