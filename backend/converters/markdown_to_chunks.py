"""
Convert Markdown files to individual JSON chunk files with token counting.

Each chunk is saved as a separate file in a document-specific folder.
"""
import json
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional
import tiktoken
from langchain_text_splitters import MarkdownHeaderTextSplitter
from backend.config import CHUNK_HEADERS

# Initialize tiktoken encoder
enc = tiktoken.get_encoding("cl100k_base")

def count_tokens(text: str) -> int:
    """
    Count tokens in text using tiktoken.
    
    Args:
        text: Text to count tokens for
        
    Returns:
        Number of tokens
    """
    return len(enc.encode(text))


def convert_markdown_to_chunks(
    input_path: str | Path, 
    output_dir: Path,
    document_id: str,
    custom_metadata: Optional[Dict[str, Any]] = None
) -> tuple[Path, int]:
    """
    Convert Markdown to individual chunk JSON files with token counting.
    
    Output structure per chunk file:
    {
      "chunk": "text content",
      "metadata": {
        "chunk_id": "uuid",
        "self": {...},
        "parents": [...],
        "document_id": "...",
        "document_type": "...",
        "document_description": "...",
        "document_keywords": [...],
        "category_ids": [...],
        "tokens": "123"
      }
    }
    
    Storage structure:
    data/chunks/
    └── D01/
        ├── chunk_001.json
        ├── chunk_002.json
        └── chunk_003.json
    
    Args:
        input_path: Path to input Markdown file
        output_dir: Directory to save chunk files (e.g., data/chunks/D01/)
        document_id: Document ID (e.g., "D01")
        custom_metadata: Optional dict of custom fields from config sheet
        
    Returns:
        Tuple of (output directory path, number of chunks created)
        
    Raises:
        FileNotFoundError: If input file doesn't exist
    """
    input_path = Path(input_path)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Create output directory for this document
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Read markdown file
    with open(input_path, 'r', encoding='utf-8') as f:
        markdown_text = f.read()
    
    # Initialize splitter
    splitter = MarkdownHeaderTextSplitter(headers_to_split_on=CHUNK_HEADERS)
    docs = splitter.split_text(markdown_text)
    
    # Track header UUIDs
    header_registry = {}
    
    def get_header_uuid(level: str, title: str) -> str:
        """Get or create UUID for a header."""
        key = (level, title)
        if key not in header_registry:
            header_registry[key] = str(uuid.uuid4())
        return header_registry[key]
    
    # Process chunks
    chunk_count = 0
    
    for idx, doc in enumerate(docs, start=1):
        metadata_dict = doc.metadata
        
        # Detect chunk's header level
        if "header3" in metadata_dict:
            self_level = "h3"
            self_title = metadata_dict["header3"]
        elif "header2" in metadata_dict:
            self_level = "h2"
            self_title = metadata_dict["header2"]
        elif "header1" in metadata_dict:
            self_level = "h1"
            self_title = metadata_dict["header1"]
        else:
            self_level = None
            self_title = None
        
        # Assign chunk ID
        if self_level and self_title:
            chunk_id = get_header_uuid(self_level, self_title)
        else:
            chunk_id = str(uuid.uuid4())
        
        # Build parent hierarchy (excluding self)
        parents = []
        for header_key, level in [("header1", "h1"), ("header2", "h2"), ("header3", "h3")]:
            if header_key in metadata_dict:
                title = metadata_dict[header_key]
                header_id = get_header_uuid(level, title)
                
                # Skip if this is the chunk's own ID
                if header_id == chunk_id:
                    continue
                
                parents.append({
                    "id": header_id,
                    "header": level,
                    "title": title
                })
        
        # Get chunk text
        chunk_text = doc.page_content.strip()
        
        # Count tokens
        token_count = count_tokens(chunk_text)
        
        # Build metadata object
        chunk_metadata = {
            "chunk_id": chunk_id,
            "self": {
                "header": self_level,
                "title": self_title
            },
            "parents": parents,
            "tokens": str(token_count)  # Store as string
        }
        
        # Add custom metadata from config sheet if provided
        if custom_metadata:
            chunk_metadata.update(custom_metadata)
        
        # Create final chunk with new structure
        final_chunk = {
            "chunk": chunk_text,
            "metadata": chunk_metadata
        }
        
        # Save as individual file
        chunk_filename = f"chunk_{idx:03d}.json"
        chunk_filepath = output_dir / chunk_filename
        
        with open(chunk_filepath, 'w', encoding='utf-8') as f:
            json.dump(final_chunk, f, indent=2, ensure_ascii=False)
        
        chunk_count += 1
    
    return output_dir, chunk_count