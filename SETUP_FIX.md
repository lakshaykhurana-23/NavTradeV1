# Setup Fix - If You See Build Errors

## Error You Might See:
```
error: Multiple top-level packages discovered in a flat-layout: ['backend', 'frontend'].
```

## ✅ Solution (Already Fixed!)

The `pyproject.toml` has been updated to work as a **script-based project** instead of a package.

## How to Use:

### 1. First Time Setup
```bash
cd document-processor

# Install dependencies
uv sync

# Install Playwright
uv run playwright install chromium

# Install LibreOffice (system dependency)
# Ubuntu/Debian:
sudo apt-get install -y libreoffice

# macOS:
brew install libreoffice
```

### 2. Run the Project

**Option A: Interactive Menu**
```bash
./run.sh
```

**Option B: Manual Commands**
```bash
# Terminal 1 - Backend
uv run uvicorn backend.main:app --reload

# Terminal 2 - Frontend (in another terminal)
uv run streamlit run frontend/chat.py
```

## Key Points:

- ✅ No need to install the project as a package
- ✅ UV will install all dependencies in `.venv`
- ✅ Run commands with `uv run` prefix
- ✅ The project works as a script-based application

## Verify It Works:

```bash
# Check if backend starts
uv run uvicorn backend.main:app --reload

# You should see:
# INFO:     Uvicorn running on http://127.0.0.1:8000
```

## Still Having Issues?

### Make sure you're in the right directory:
```bash
pwd
# Should show: /path/to/document-processor

ls
# Should show: backend/ frontend/ data/ pyproject.toml run.sh
```

### Delete .venv and start fresh:
```bash
rm -rf .venv
uv sync
```

### Check UV version:
```bash
uv --version
# Should be 0.4.0 or higher
```

## What Changed?

The original `pyproject.toml` had:
```toml
[build-system]
requires = ["setuptools>=68.0.0"]
build-backend = "setuptools.build_meta"
```

This has been **removed** because we don't need to build/publish this as a package.
We just need UV to manage dependencies, which it does through the `[project]` section.

---

**You're all set! Just run `uv sync` and then `./run.sh`** 🚀
