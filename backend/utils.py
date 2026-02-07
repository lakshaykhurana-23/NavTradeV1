"""
Utility functions for file handling and type detection.
"""
from pathlib import Path
from typing import Literal
from backend.config import SUPPORTED_FORMATS


def detect_file_type(file_path: str | Path) -> Literal["pdf", "docx", "html"] | None:
    """
    Detect file type based on extension.
    
    Args:
        file_path: Path to the file
        
    Returns:
        File type ('pdf', 'docx', or 'html') or None if unsupported
    """
    file_path = Path(file_path)
    extension = file_path.suffix.lower()
    
    for file_type, extensions in SUPPORTED_FORMATS.items():
        if extension in extensions:
            return file_type
    
    return None


def generate_output_path(input_path: str | Path, output_dir: Path, new_extension: str) -> Path:
    """
    Generate output file path with new extension.
    
    Args:
        input_path: Original file path
        output_dir: Directory for output file
        new_extension: New file extension (e.g., '.pdf', '.md')
        
    Returns:
        Path object for output file
    """
    input_path = Path(input_path)
    return output_dir / f"{input_path.stem}{new_extension}"


def ensure_path_exists(file_path: str | Path) -> Path:
    """
    Ensure a file exists, raise FileNotFoundError if not.
    
    Args:
        file_path: Path to check
        
    Returns:
        Path object if file exists
        
    Raises:
        FileNotFoundError: If file doesn't exist
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    return file_path
