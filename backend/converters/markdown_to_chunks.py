"""
Convert Markdown files to JSON chunks with UUID tracking.
"""
import json
import uuid
from pathlib import Path
from typing import List, Dict, Any
from langchain_text_splitters import MarkdownHeaderTextSplitter
from backend.config import CHUNK_HEADERS


def convert_markdown_to_chunks(input_path: str | Path, output_path: str | Path) -> Path:
    """
    Convert Markdown to hierarchical chunks with UUID tracking.
    
    This function:
    1. Splits markdown by headers
    2. Assigns unique IDs to each chunk
    3. Tracks parent-child relationships
    4. Saves as JSON
    
    Args:
        input_path: Path to input Markdown file
        output_path: Path for output JSON file
        
    Returns:
        Path to the generated JSON file
        
    Raises:
        FileNotFoundError: If input file doesn't exist
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
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
    final_chunks = []
    
    for doc in docs:
        metadata = doc.metadata
        
        # Detect chunk's header level
        if "header3" in metadata:
            self_level = "h3"
            self_title = metadata["header3"]
        elif "header2" in metadata:
            self_level = "h2"
            self_title = metadata["header2"]
        elif "header1" in metadata:
            self_level = "h1"
            self_title = metadata["header1"]
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
            if header_key in metadata:
                title = metadata[header_key]
                header_id = get_header_uuid(level, title)
                
                # Skip if this is the chunk's own ID
                if header_id == chunk_id:
                    continue
                
                parents.append({
                    "id": header_id,
                    "header": level,
                    "title": title
                })
        
        # Create chunk object
        final_chunks.append({
            "chunk_id": chunk_id,
            "self": {
                "header": self_level,
                "title": self_title
            },
            "parents": parents,
            "text": doc.page_content.strip()
        })
    
    # Save to JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_chunks, f, indent=2, ensure_ascii=False)
    
    return output_path
