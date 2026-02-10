# Quick Start Guide - NavTrade

Get NavTrade Document Processor running and process your documents with metadata in under 15 minutes.

## Prerequisites

Before you begin, ensure you have:
- **Operating System**: macOS, Linux, or Windows
- **Python**: Version 3.10 or higher
- **Disk Space**: At least 2GB free
- **Hardware**: Apple Silicon (M1/M2/M3) recommended for GPU acceleration

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

### 3. Install Additional Dependencies

```bash
uv add tiktoken pandas openpyxl
```

This adds:
- `tiktoken` - Token counting
- `pandas` - Config sheet reading
- `openpyxl` - Excel file support

### 4. Install LibreOffice (Required for DOCX Conversion)

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

### 5. Configure LibreOffice Path (If Needed)

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

### 6. Install Playwright Browsers

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

### 7. Verify Data Directories

The following directories should exist (created automatically):

```bash
ls -la data/
# Should show:
# data/input/     - Place your input files here
# data/pdf/       - PDF files are saved here
# data/markdown/  - Markdown files are saved here
# data/chunks/    - Final JSON chunks are saved here (folders per document)
```

## Setup Configuration

### Create Config Sheet

Create `config.xlsx` in the NavTradeV1 directory with these columns:

| Id | Format | Description | Keywords | Categories |
|----|--------|-------------|----------|------------|
| D01 | PDF | Tax form 1040 | tax, form, federal | C01_S02, C03_S01 |
| D02 | HTML | Python tutorial | python, programming | C02_S05 |
| D03 | DOCX | Sales report | sales, Q4, report | C01_S02 |

**Column Descriptions:**
- **Id**: Document ID (matches filename - D01.pdf, D02.html, etc.)
- **Format**: Document type (PDF, DOCX, HTML, etc.)
- **Description**: Brief description of the document
- **Keywords**: Comma-separated keywords
- **Categories**: Comma-separated category IDs (e.g., C01_S02, C03_S01)

**Important Rules:**
- File will only be processed if at least one of Keywords, Categories, or Description has content
- If all three are empty, file is skipped
- Filename must match Id (D01.pdf matches Id "D01")

## Running the Application

### Process Documents from Input Folder

**Step 1: Upload Files**

Upload files to `data/input/` with ID-based naming:

```bash
# Files must be named with document ID
cp your_tax_form.pdf data/input/D01.pdf
cp python_tutorial.html data/input/D02.html
cp sales_report.docx data/input/D03.docx
```

**Step 2: Run Processor**

```bash
cd NavTradeV1
python process_all.py
```

**Step 3: View Output**

Chunks are saved as individual files:

```
data/chunks/
├── D01/
│   ├── chunk_001.json
│   ├── chunk_002.json
│   └── chunk_003.json
├── D02/
│   └── chunk_001.json
└── D03/
    ├── chunk_001.json
    └── chunk_002.json
```

### Example Processing Output

```
📋 Using config: config.xlsx
📂 Processing files from: data/input/

Loaded config with 3 entries
Metadata available for 3 document IDs

======================================================================
PROCESSING ALL FILES FROM data/input/
======================================================================
Found 3 file(s) in data/input/

[1/3] File: D01.pdf
  Document ID: D01
  Type: PDF
  Keywords: ['tax', 'form', 'federal']
  Categories: ['C01_S02', 'C03_S01']
  Extracting text to Markdown...
detected formats: [<InputFormat.PDF: 'pdf'>]
Going to convert document batch...
Initializing pipeline for StandardPdfPipeline
Accelerator device: 'mps'  ← GPU acceleration (good!)
Finished converting document D01.pdf in 8.45 sec.
  Generating chunks with metadata and token counts...
  ✓ Success: data/chunks/D01
  ✓ Created 12 chunks

[2/3] File: D02.html
  Document ID: D02
  Type: HTML
  Keywords: ['python', 'programming']
  Categories: ['C02_S05']
  Converting HTML to PDF...
  Extracting text to Markdown...
Accelerator device: 'mps'
Finished converting document D02.pdf in 10.23 sec.
  Generating chunks with metadata and token counts...
  ✓ Success: data/chunks/D02
  ✓ Created 8 chunks

[3/3] File: D03.docx
  Document ID: D03
  Type: DOCX
  Keywords: ['sales', 'Q4', 'report']
  Categories: ['C01_S02']
  Converting DOCX to PDF...
  Extracting text to Markdown...
Accelerator device: 'mps'
Finished converting document D03.pdf in 9.12 sec.
  Generating chunks with metadata and token counts...
  ✓ Success: data/chunks/D03
  ✓ Created 15 chunks

======================================================================
PROCESSING SUMMARY
======================================================================
Total files found:              3
Successfully processed:         3
Skipped (no metadata):          0
Skipped (no ID):                0
Failed:                         0
Total chunks created:           35
======================================================================

✅ PROCESSING COMPLETE

📁 Chunks saved in: data/chunks/
   Structure: data/chunks/D01/chunk_001.json, chunk_002.json, ...
```

## Understanding GPU Acceleration

### What is "Accelerator device: 'mps'"?

**MPS = Metal Performance Shaders**

This is **Apple's GPU acceleration** for machine learning on macOS.

```
Accelerator device: 'mps'
```

**This is GOOD!** It means:
- ✅ You have Apple Silicon (M1/M2/M3 chip)
- ✅ GPU acceleration is enabled
- ✅ Processing is 2-4x faster

**Performance Comparison:**

| Hardware | PDF Processing Time |
|----------|---------------------|
| Apple Silicon (with MPS) | 5-15 seconds per page |
| Intel/AMD (CPU only) | 30-60 seconds per page |

**Your example:**
```
Finished converting document D01.pdf in 8.45 sec.
```
This is **fast** - with CPU only it might take 30+ seconds.

## Viewing the Output

### Check Individual Chunks

```bash
# View a specific chunk
cat data/chunks/D01/chunk_001.json

# View with pretty formatting (if jq is installed)
cat data/chunks/D01/chunk_001.json | jq .
```

### Example Chunk Output

```json
{
  "chunk": "Form 1040 is the standard federal income tax form...",
  "metadata": {
    "chunk_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "self": {
      "header": "h1",
      "title": "Form 1040 Instructions"
    },
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

### Count Total Chunks

```bash
# List all chunk files
find data/chunks -name "*.json" | wc -l

# Count chunks for specific document
ls data/chunks/D01/ | wc -l
```

## Common Tasks

### Add New Documents

```bash
# 1. Add new file to input
cp new_document.pdf data/input/D04.pdf

# 2. Add row to config.xlsx
# Id: D04
# Format: PDF
# Description: User manual
# Keywords: manual, guide
# Categories: C05_S01

# 3. Run processor again
python process_all.py
```

### Reprocess All Documents

```bash
# Simply run the processor again
# It will reprocess all files (no caching currently)
python process_all.py
```

### Clean Up Processed Files

```bash
# Remove all processed files (keeps input and config)
rm -rf data/pdf/*
rm -rf data/markdown/*
rm -rf data/chunks/*

# Then reprocess
python process_all.py
```

## Troubleshooting

### Issue: "Module not found" errors

```bash
# Solution: Reinstall dependencies
uv sync

# Install additional packages
uv add tiktoken pandas openpyxl

# If that doesn't work, recreate environment
rm -rf .venv
uv sync
uv add tiktoken pandas openpyxl
```

### Issue: "LibreOffice not found"

```bash
# Verify installation
which soffice  # Linux/macOS
where soffice  # Windows

# If not found, reinstall LibreOffice (see step 4)
# Then configure the path in .env (see step 5)
```

**Solution Steps:**
1. Find where LibreOffice is installed: `which soffice`
2. Create a `.env` file in the NavTradeV1 directory
3. Add the line: `LIBREOFFICE_BIN="/path/to/soffice"`
4. Run processor again

### Issue: "Playwright browser not found"

```bash
# Reinstall Chromium
uv run playwright install chromium

# Linux: Also install system dependencies
uv run playwright install-deps chromium
```

### Issue: File not processing

**Check:**
1. Is file in `data/input/`? → `ls data/input/`
2. Is filename correct format? → Should be `D01.pdf`, `D02.html`, etc.
3. Does config have matching Id? → Check `config.xlsx` has row with Id "D01"
4. Does config have metadata? → At least one of Keywords/Categories/Description must have content

**Common Problems:**
- ❌ Filename: `document.pdf` → Should be `D01.pdf`
- ❌ Config missing Id → Add row with Id "D01"
- ❌ All metadata empty → Add at least Keywords or Categories or Description

### Issue: "No metadata in config"

**Reason:** All of Keywords, Categories, and Description are empty for this document.

**Solution:**
1. Open `config.xlsx`
2. Find the row with matching Id
3. Add content to at least one of: Keywords, Categories, or Description
4. Save and run processor again

### Issue: Processing is slow

**If you don't see "Accelerator device: 'mps'":**
- You're not on Apple Silicon
- Processing uses CPU (slower but works)
- Expected times: 30-60 seconds per page instead of 5-15 seconds

**Solutions:**
- For faster processing, use Apple Silicon (M1/M2/M3) Mac
- Or use a machine with NVIDIA GPU (will use CUDA)
- Or accept slower CPU processing (still works!)

## Workflow Summary

```
1. Upload files to data/input/ (D01.pdf, D02.html, etc.)
         ↓
2. Create config.xlsx with metadata for each document
         ↓
3. Run: python process_all.py
         ↓
4. System:
   - Extracts ID from filename
   - Matches with config
   - Checks metadata (skip if all empty)
   - Converts to PDF
   - Extracts text with GPU acceleration (if available)
   - Generates chunks with metadata
   - Counts tokens
   - Saves individual chunk files
         ↓
5. View output in data/chunks/D01/, data/chunks/D02/, etc.
```

## Next Steps

Once everything is working:

1. ✅ Process your own documents
2. ✅ Customize metadata in config sheet
3. ✅ Use chunks in your application
4. ✅ Read the full README.md for advanced configuration
5. ✅ Review NEW_WORKFLOW_GUIDE.md for detailed explanations

## Getting Help

- **Check logs**: Terminal output shows detailed processing info
- **Read documentation**: README.md and NEW_WORKFLOW_GUIDE.md
- **Common issues**: See troubleshooting section above

## Summary of Commands

```bash
# Installation
curl -LsSf https://astral.sh/uv/install.sh | sh
cd NavTradeV1
uv sync
uv add tiktoken pandas openpyxl
brew install libreoffice  # or apt-get/dnf
uv run playwright install chromium

# Usage
# 1. Upload files to data/input/
cp file.pdf data/input/D01.pdf

# 2. Create config.xlsx

# 3. Process all
python process_all.py

# 4. View output
ls data/chunks/D01/
cat data/chunks/D01/chunk_001.json
```

You're all set! Start processing documents with NavTrade and metadata! 🎉