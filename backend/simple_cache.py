"""
Simple cache for document processing - stores processed file paths
"""
import json
from pathlib import Path
from datetime import datetime


class SimpleCache:
    """
    Simple JSON-based cache to track processed files.
    Stores: filename -> {chunks_path, processed_at}
    """
    
    def __init__(self, cache_file: str = "data/cache/processed.json"):
        self.cache_file = Path(cache_file)
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        self.cache = self._load()
    
    def _load(self) -> dict:
        """Load cache from file"""
        if self.cache_file.exists():
            return json.loads(self.cache_file.read_text())
        return {}
    
    def _save(self):
        """Save cache to file"""
        self.cache_file.write_text(json.dumps(self.cache, indent=2))
    
    def get(self, filename: str) -> str | None:
        """Get cached chunks path for a file, returns None if not cached"""
        entry = self.cache.get(filename)
        if entry and Path(entry['chunks_path']).exists():
            return entry['chunks_path']
        return None
    
    def set(self, filename: str, chunks_path: str):
        """Cache a processed file"""
        self.cache[filename] = {
            'chunks_path': chunks_path,
            'processed_at': datetime.now().isoformat()
        }
        self._save()
    
    def clear(self):
        """Clear all cache"""
        self.cache = {}
        self._save()