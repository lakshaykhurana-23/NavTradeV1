"""
Enhanced simple tracker with LIVE progress updates during processing.

Shows real-time status so you know it's working (not frozen).

Usage:
    python simple_tracker.py
"""
import time
import json
import argparse
import threading
import sys
from pathlib import Path
from datetime import datetime, timedelta
import logging

# Import your existing processor
from backend.input_folder_processor import InputFolderProcessor
from backend.config import INPUT_DIR

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


def format_time(seconds):
    """Format seconds to readable time."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m ({seconds:.0f}s)"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h ({seconds/60:.0f}m)"


class LiveProgressIndicator:
    """Shows live progress during long-running operations."""
    
    def __init__(self, message="Processing"):
        self.message = message
        self.running = False
        self.thread = None
        self.start_time = None
    
    def start(self):
        """Start showing live progress."""
        self.running = True
        self.start_time = time.time()
        self.thread = threading.Thread(target=self._show_progress, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop showing progress."""
        self.running = False
        if self.thread:
            self.thread.join()
        # Clear the line
        sys.stdout.write('\r' + ' ' * 100 + '\r')
        sys.stdout.flush()
    
    def _show_progress(self):
        """Show animated progress indicator."""
        spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        idx = 0
        
        while self.running:
            elapsed = time.time() - self.start_time
            elapsed_str = format_time(elapsed)
            
            # Show spinner + message + elapsed time
            sys.stdout.write(f'\r   {spinner[idx]} {self.message}... {elapsed_str} elapsed')
            sys.stdout.flush()
            
            idx = (idx + 1) % len(spinner)
            time.sleep(0.1)


def process_with_timing(config_file, enable_ocr=False):
    """
    Process documents with timing and LIVE progress updates.
    """
    print("\n" + "="*70)
    print("DOCUMENT PROCESSING WITH LIVE TRACKING")
    print("="*70)
    print(f"Config: {config_file}")
    print(f"OCR: {'ENABLED (slower)' if enable_ocr else 'DISABLED (faster)'}")
    print("="*70 + "\n")
    
    # Initialize processor
    processor = InputFolderProcessor(config_file)
    
    # Get files to process
    input_files = processor._get_input_files()
    
    if not input_files:
        print("❌ No files found in data/input/")
        return
    
    print(f"📁 Found {len(input_files)} file(s) to process\n")
    
    # Track all results
    all_results = []
    overall_start = time.time()
    
    # Process each file
    for idx, input_file in enumerate(input_files, 1):
        print("="*70)
        print(f"[{idx}/{len(input_files)}] FILE: {input_file.name}")
        print("="*70)
        
        file_start = time.time()
        
        try:
            # Get document ID
            doc_id = processor._extract_doc_id_from_filename(input_file.name)
            
            if not doc_id:
                print("⊘ Skipped - No document ID")
                print()
                continue
            
            # Check metadata
            if doc_id not in processor.metadata_lookup:
                print("⊘ Skipped - No metadata")
                print()
                continue
            
            metadata = processor.metadata_lookup[doc_id]
            
            # Show file info
            file_size_mb = input_file.stat().st_size / (1024 * 1024)
            print(f"📄 Document ID: {doc_id}")
            print(f"📊 File size: {file_size_mb:.2f} MB")
            print(f"🕐 Started: {datetime.now().strftime('%H:%M:%S')}")
            print()
            
            # Import needed modules
            from backend.utils import detect_file_type, generate_output_path
            from backend.config import PDF_DIR, MARKDOWN_DIR, CHUNKS_DIR
            from backend.converters import convert_docx_to_pdf, convert_html_to_pdf, convert_pdf_to_markdown
            from backend.converters.markdown_to_chunks import convert_markdown_to_chunks
            
            # STEP 1: Conversion
            step1_start = time.time()
            print("⏱️  Step 1/3: Converting to PDF...")
            
            file_type = detect_file_type(input_file)
            
            progress = LiveProgressIndicator("Converting")
            progress.start()
            
            if file_type == "pdf":
                pdf_path = PDF_DIR / input_file.name
                if input_file != pdf_path:
                    import shutil
                    shutil.copy2(input_file, pdf_path)
            elif file_type == "docx":
                pdf_path = generate_output_path(input_file, PDF_DIR, ".pdf")
                convert_docx_to_pdf(input_file, pdf_path)
            elif file_type == "html":
                pdf_path = generate_output_path(input_file, PDF_DIR, ".pdf")
                convert_html_to_pdf(input_file, pdf_path)
            else:
                progress.stop()
                raise ValueError(f"Unsupported file type: {file_type}")
            
            progress.stop()
            step1_time = time.time() - step1_start
            print(f"   ✓ Done in {format_time(step1_time)}")
            
            # Get page count
            try:
                import PyPDF2
                reader = PyPDF2.PdfReader(str(pdf_path))
                total_pages = len(reader.pages)
                print(f"   📖 Total pages: {total_pages}")
            except:
                total_pages = None
            
            print()
            
            # STEP 2: PDF to Markdown (SLOWEST STEP - SHOW LIVE PROGRESS)
            step2_start = time.time()
            print("⏱️  Step 2/3: Extracting text (PDF → Markdown)...")
            print("   💡 This is the slowest step - watch the live timer below:")
            print()
            
            # Start live progress indicator
            progress = LiveProgressIndicator("🔄 Extracting text from PDF")
            progress.start()
            
            markdown_path = generate_output_path(pdf_path, MARKDOWN_DIR, ".md")
            convert_pdf_to_markdown(pdf_path, markdown_path, enable_ocr=enable_ocr)
            
            # Stop progress indicator
            progress.stop()
            
            step2_time = time.time() - step2_start
            print(f"   ✓ Done in {format_time(step2_time)}")
            
            if total_pages:
                time_per_page = step2_time / total_pages
                print(f"   ⚡ {time_per_page:.2f}s per page")
            
            print()
            
            # STEP 3: Create chunks
            step3_start = time.time()
            print("⏱️  Step 3/3: Creating chunks...")
            
            progress = LiveProgressIndicator("Creating chunks")
            progress.start()
            
            chunks_output_dir = CHUNKS_DIR / doc_id
            chunks_dir, chunk_count = convert_markdown_to_chunks(
                markdown_path,
                chunks_output_dir,
                doc_id,
                custom_metadata=metadata
            )
            
            progress.stop()
            step3_time = time.time() - step3_start
            print(f"   ✓ Done in {format_time(step3_time)}")
            print(f"   📦 Created {chunk_count} chunks")
            print()
            
            # File summary
            file_time = time.time() - file_start
            
            print("-"*70)
            print("📊 FILE SUMMARY")
            print("-"*70)
            print(f"Status: ✓ SUCCESS")
            print(f"Total time: {format_time(file_time)}")
            print()
            print("Time breakdown:")
            print(f"  Step 1 (Conversion):      {format_time(step1_time):>12s}  ({step1_time/file_time*100:>5.1f}%)")
            print(f"  Step 2 (PDF→Markdown):    {format_time(step2_time):>12s}  ({step2_time/file_time*100:>5.1f}%)")
            print(f"  Step 3 (Create chunks):   {format_time(step3_time):>12s}  ({step3_time/file_time*100:>5.1f}%)")
            print(f"  {'TOTAL':>26s}: {format_time(file_time):>12s}")
            
            # Save result
            result = {
                'file_name': input_file.name,
                'doc_id': doc_id,
                'file_size_mb': file_size_mb,
                'total_pages': total_pages,
                'total_time_seconds': file_time,
                'step1_conversion_seconds': step1_time,
                'step2_pdf_to_markdown_seconds': step2_time,
                'step3_chunks_seconds': step3_time,
                'chunks_created': chunk_count,
                'time_per_page': step2_time / total_pages if total_pages else None,
                'status': 'success'
            }
            all_results.append(result)
            
            # Show ETA
            if idx < len(input_files):
                avg_time = sum(r['total_time_seconds'] for r in all_results) / len(all_results)
                remaining = len(input_files) - idx
                eta_seconds = avg_time * remaining
                eta = timedelta(seconds=int(eta_seconds))
                print(f"\n⏰ Estimated time remaining: {eta} ({remaining} files left)")
            
            print("="*70 + "\n")
        
        except Exception as e:
            file_time = time.time() - file_start
            print(f"\n❌ ERROR: {e}")
            print(f"Time before failure: {format_time(file_time)}")
            print("="*70 + "\n")
            
            all_results.append({
                'file_name': input_file.name,
                'doc_id': doc_id if 'doc_id' in locals() else 'unknown',
                'total_time_seconds': file_time,
                'status': 'failed',
                'error': str(e)
            })
    
    # Overall summary
    total_time = time.time() - overall_start
    successful = [r for r in all_results if r.get('status') == 'success']
    
    print("\n" + "="*70)
    print("🏁 OVERALL SUMMARY")
    print("="*70)
    print(f"Total files: {len(input_files)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(all_results) - len(successful)}")
    print(f"Total time: {format_time(total_time)}")
    
    if successful:
        avg_time = sum(r['total_time_seconds'] for r in successful) / len(successful)
        print(f"Average per file: {format_time(avg_time)}")
        
        total_pages = sum(r.get('total_pages', 0) for r in successful if r.get('total_pages'))
        if total_pages > 0:
            total_pdf_time = sum(r.get('step2_pdf_to_markdown_seconds', 0) for r in successful)
            print(f"Average per page: {total_pdf_time/total_pages:.2f}s")
    
    print("="*70)
    
    # Save to CSV
    csv_file = Path('processing_times.csv')
    
    import csv
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        if successful:
            writer = csv.DictWriter(f, fieldnames=[
                'file_name', 'doc_id', 'file_size_mb', 'total_pages',
                'total_time_seconds', 'total_time_minutes',
                'step1_conversion_seconds', 'step2_pdf_to_markdown_seconds',
                'step3_chunks_seconds', 'chunks_created', 'time_per_page',
                'status', 'error'
            ])
            writer.writeheader()
            
            for r in all_results:
                row = r.copy()
                row['total_time_minutes'] = f"{r.get('total_time_seconds', 0)/60:.2f}"
                writer.writerow(row)
    
    print(f"\n📊 Results saved to: {csv_file}")
    print(f"   Open in Excel to analyze timing data")
    print()


def main():
    parser = argparse.ArgumentParser(description='Process documents with live progress tracking')
    parser.add_argument('--config', type=Path, default=Path('UpdatedConfig.xlsx'), 
                       help='Config file path (default: UpdatedConfig.xlsx)')
    parser.add_argument('--ocr', action='store_true', help='Enable OCR (slower)')
    
    args = parser.parse_args()
    
    if not args.config.exists():
        print(f"❌ Config file not found: {args.config}")
        print(f"\n💡 Make sure your config file exists:")
        print(f"   - UpdatedConfig.xlsx  (default)")
        print(f"   - Or use: --config yourfile.xlsx")
        return
    
    process_with_timing(args.config, args.ocr)


if __name__ == "__main__":
    main()