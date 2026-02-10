"""
Process all files from data/input/ folder using config sheet metadata.

Usage:
    python process_all.py
"""
from pathlib import Path
import logging
from backend.input_folder_processor import InputFolderProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)

def main():
    """Process all files from data/input/ folder."""
    
    # Path to config file
    config_file = Path("DataSourceConfig.xlsx")  # or "config.csv"
    
    # Check if config exists
    if not config_file.exists():
        print(f"❌ Config file not found: {config_file}")
        print(f"\n   Please create a config file with columns:")
        print(f"   - Id: Document ID (e.g., D01, D02)")
        print(f"   - Format: Document type")
        print(f"   - Description: Document description")
        print(f"   - Keywords: Comma-separated keywords")
        print(f"   - Categories: Comma-separated category IDs")
        print(f"\n   Files without metadata will be skipped.")
        return
    
    print(f"\n📋 Using config: {config_file}")
    print(f"📂 Processing files from: data/input/")
    print()
    
    # Create processor
    processor = InputFolderProcessor(config_file=config_file)
    
    # Process all files
    results = processor.process_all(enable_ocr=False)
    
    # Done
    print("\n✅ PROCESSING COMPLETE")
    print(f"\n📁 Chunks saved in: data/chunks/")
    print(f"   Structure: data/chunks/D01/chunk_001.json, chunk_002.json, ...")
    
    # Show failures if any
    failed = [r for r in results['results'] if r.get('status') == 'failed']
    if failed:
        print("\n❌ Failed files:")
        for f in failed:
            print(f"   - {f['file']}: {f.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()