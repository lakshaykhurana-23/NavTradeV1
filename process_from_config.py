"""
Simple script to process documents from a config sheet.

Expected config sheet columns:
- Link: URL to document (required)
- document_id: ID from "column in data sources"
- Format: Document type
- Description: Document description  
- Keywords: Comma-separated keywords
- Categories: Comma-separated category IDs (e.g., "C01_S02, C03_S01")
"""
from pathlib import Path
import logging
from backend.config_sheet_processor import ConfigSheetProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    """Process all documents from config sheet."""
    
    # Path to your config file
    # Change this to your Excel or CSV file path
    config_file = Path("DataSourceConfig.xlsx")  # or "config.csv"
    
    # Check if file exists
    if not config_file.exists():
        print(f"❌ Config file not found: {config_file}")
        print(f"\n   Please create a config file with columns:")
        print(f"   - Link: Document URL (required)")
        print(f"   - document_id: ID of the document")
        print(f"   - Format: Document type (PDF, DOCX, etc.)")
        print(f"   - Description: Document description")
        print(f"   - Keywords: Comma-separated keywords")
        print(f"   - Categories: Comma-separated category IDs")
        print(f"\n   Rows with empty 'Link' will be skipped automatically.")
        return
    
    print(f"📋 Processing documents from: {config_file}")
    print()
    
    # Create processor
    processor = ConfigSheetProcessor(
        config_file=config_file,
        link_column="Link"  # Column name with URLs
    )
    
    # Process all documents
    results = processor.process_all(enable_ocr=False)
    
    # Print results
    print("\n" + "=" * 60)
    print("✅ PROCESSING COMPLETE")
    print("=" * 60)
    print(f"Total rows in config: {results['total_rows']}")
    print(f"Skipped (no link): {results['skipped']}")
    print(f"Attempted to process: {results['processed']}")
    print(f"Successfully processed: {results['success']}")
    print(f"Failed: {results['failed']}")
    
    # Print where chunks are saved
    print(f"\n📁 Chunks saved in: data/chunks/")
    
    # Show any failures
    failed = [r for r in results['results'] if r.get('status') == 'failed']
    if failed:
        print("\n❌ Failed documents:")
        for f in failed:
            print(f"   - {f['link']}: {f.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()