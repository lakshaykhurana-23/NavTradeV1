# """
# Config sheet processor with proper metadata structure.

# Handles:
# - Reading config sheet with 'Link' column
# - Parsing document_keywords (comma-separated, trimmed)
# - Parsing category_ids (comma-separated, trimmed)
# - Adding all metadata to chunks
# """
# import pandas as pd
# from pathlib import Path
# import logging
# from typing import Dict, List, Any
# from backend.config import INPUT_DIR, CHUNKS_DIR, PDF_DIR, MARKDOWN_DIR
# from backend.utils import detect_file_type, generate_output_path
# from backend.converters import (
#     convert_docx_to_pdf,
#     convert_html_to_pdf,
#     convert_pdf_to_markdown
# )
# from backend.converters.markdown_to_chunks import convert_markdown_to_chunks
# from backend.document_downloader import DocumentDownloader

# logger = logging.getLogger(__name__)


# class ConfigSheetProcessor:
#     """
#     Process documents from a config sheet with Link and metadata columns.
    
#     Expected columns:
#     - Link: URL to document (required, skip if empty)
#     - document_id: ID of the document
#     - Format: Document type/format
#     - Description: Document description
#     - Keywords: Comma-separated keywords
#     - Categories: Comma-separated category IDs (e.g., "C01_S02, C03_S01")
#     """
    
#     # Column mapping from config sheet to metadata keys
#     COLUMN_MAPPING = {
#         'Link': None,  # Special handling, not in metadata
#         'Id': 'document_id',
#         'Format': 'document_type',
#         'Description': 'document_description',
#         'Keywords': 'document_keywords',
#         'Categories': 'category_ids'
#     }
    
#     def __init__(self, config_file: Path, link_column: str = "Link"):
#         """
#         Initialize processor.
        
#         Args:
#             config_file: Path to Excel (.xlsx) or CSV file
#             link_column: Name of the column containing URLs (default: "Link")
#         """
#         self.config_file = Path(config_file)
#         self.link_column = link_column
#         self.downloader = DocumentDownloader(INPUT_DIR)
        
#         # Load config
#         self.df = self._load_config()
#         logger.info(f"Loaded config with {len(self.df)} entries")
    
#     def _load_config(self) -> pd.DataFrame:
#         """Load config file (Excel or CSV)."""
#         if self.config_file.suffix == '.csv':
#             return pd.read_csv(self.config_file)
#         elif self.config_file.suffix in ['.xlsx', '.xls']:
#             return pd.read_excel(self.config_file)
#         else:
#             raise ValueError(f"Unsupported file type: {self.config_file.suffix}")
    
#     def _parse_list_field(self, value: Any) -> List[str]:
#         """
#         Parse comma-separated string into list.
        
#         Handles:
#         - Trimming spaces before and after commas
#         - Removing empty strings
#         - Handling NaN/None values
        
#         Args:
#             value: String with comma-separated values or NaN
            
#         Returns:
#             List of cleaned strings
            
#         Examples:
#             "tax, form, 2024" -> ["tax", "form", "2024"]
#             "C01_S02 , C03_S01" -> ["C01_S02", "C03_S01"]
#             "single value" -> ["single value"]
#             NaN -> []
#         """
#         # Handle NaN/None
#         if pd.isna(value) or value is None or value == '':
#             return []
        
#         # Convert to string and split by comma
#         value_str = str(value)
#         items = value_str.split(',')
        
#         # Trim spaces and remove empty strings
#         cleaned_items = [item.strip() for item in items if item.strip()]
        
#         return cleaned_items
    
#     def _extract_metadata(self, row: pd.Series) -> Dict[str, Any]:
#         """
#         Extract metadata from a config sheet row.
        
#         Maps column names to metadata keys and handles special parsing.
        
#         Args:
#             row: DataFrame row
            
#         Returns:
#             Dictionary with metadata
#         """
#         metadata = {}
        
#         for col_name, meta_key in self.COLUMN_MAPPING.items():
#             # Skip Link column (handled separately)
#             if meta_key is None:
#                 continue
            
#             # Check if column exists in dataframe
#             if col_name not in row.index:
#                 continue
            
#             value = row[col_name]
            
#             # Skip NaN values
#             if pd.isna(value):
#                 metadata[meta_key] = "" if meta_key in ['document_id', 'document_type', 'document_description'] else []
#                 continue
            
#             # Special handling for list fields
#             if col_name in ['Keywords', 'Categories']:
#                 metadata[meta_key] = self._parse_list_field(value)
#             else:
#                 # Regular string fields
#                 metadata[meta_key] = str(value).strip()
        
#         return metadata
    
#     def process_all(self, enable_ocr: bool = False) -> Dict:
#         """
#         Process all documents in the config sheet.
        
#         Args:
#             enable_ocr: Whether to enable OCR for PDFs
            
#         Returns:
#             Dictionary with processing results
#         """
#         logger.info("=" * 60)
#         logger.info("Processing documents from config sheet")
#         logger.info("=" * 60)
        
#         if self.link_column not in self.df.columns:
#             raise ValueError(f"Column '{self.link_column}' not found in config file")
        
#         results = []
#         processed_count = 0
#         skipped_count = 0
        
#         for idx, row in self.df.iterrows():
#             link = row[self.link_column]
            
#             # Skip if Link column is empty
#             if pd.isna(link) or link == '' or str(link).strip() == '':
#                 skipped_count += 1
#                 logger.info(f"\n[Row {idx + 1}] Skipping - No link provided")
#                 continue
            
#             # Extract metadata from row
#             custom_metadata = self._extract_metadata(row)
            
#             logger.info(f"\n[{processed_count + 1}] Processing: {link}")
#             logger.info(f"  Document ID: {custom_metadata.get('document_id', 'N/A')}")
#             logger.info(f"  Type: {custom_metadata.get('document_type', 'N/A')}")
#             logger.info(f"  Keywords: {custom_metadata.get('document_keywords', [])}")
#             logger.info(f"  Categories: {custom_metadata.get('category_ids', [])}")
            
#             try:
#                 result = self._process_single_entry(link, custom_metadata, enable_ocr)
#                 results.append(result)
#                 processed_count += 1
#                 logger.info(f"  ✓ Success: {result['chunks_path']}")
            
#             except Exception as e:
#                 logger.error(f"  ✗ Failed: {e}")
#                 results.append({
#                     'link': link,
#                     'metadata': custom_metadata,
#                     'status': 'failed',
#                     'error': str(e)
#                 })
        
#         # Summary
#         success_count = sum(1 for r in results if r.get('status') == 'success')
#         failed_count = len(results) - success_count
        
#         logger.info("\n" + "=" * 60)
#         logger.info("PROCESSING SUMMARY")
#         logger.info("=" * 60)
#         logger.info(f"Total rows: {len(self.df)}")
#         logger.info(f"Skipped (no link): {skipped_count}")
#         logger.info(f"Processed: {processed_count}")
#         logger.info(f"Success: {success_count}")
#         logger.info(f"Failed: {failed_count}")
#         logger.info("=" * 60)
        
#         return {
#             'total_rows': len(self.df),
#             'skipped': skipped_count,
#             'processed': processed_count,
#             'success': success_count,
#             'failed': failed_count,
#             'results': results
#         }
    
#     def _process_single_entry(
#         self, 
#         link: str, 
#         custom_metadata: Dict, 
#         enable_ocr: bool
#     ) -> Dict:
#         """
#         Process a single entry from config sheet.
        
#         Steps:
#         1. Download document from link
#         2. Convert to PDF (if needed)
#         3. Extract to Markdown
#         4. Generate chunks with custom metadata
        
#         Args:
#             link: Document URL
#             custom_metadata: Custom metadata to add to chunks
#             enable_ocr: Whether to enable OCR
            
#         Returns:
#             Dictionary with processing result
#         """
#         # Step 1: Download document
#         logger.info(f"  Downloading from URL...")
#         downloaded_file = self.downloader.download(link)
        
#         # Step 2: Detect file type
#         file_type = detect_file_type(downloaded_file)
#         if not file_type:
#             raise ValueError(f"Unsupported file type: {downloaded_file.suffix}")
        
#         # Step 3: Convert to PDF if needed
#         if file_type == "pdf":
#             pdf_path = PDF_DIR / downloaded_file.name
#             if downloaded_file != pdf_path:
#                 import shutil
#                 shutil.copy2(downloaded_file, pdf_path)
#         elif file_type == "docx":
#             logger.info(f"  Converting DOCX to PDF...")
#             pdf_path = generate_output_path(downloaded_file, PDF_DIR, ".pdf")
#             convert_docx_to_pdf(downloaded_file, pdf_path)
#         elif file_type == "html":
#             logger.info(f"  Converting HTML to PDF...")
#             pdf_path = generate_output_path(downloaded_file, PDF_DIR, ".pdf")
#             convert_html_to_pdf(downloaded_file, pdf_path)
#         else:
#             raise ValueError(f"Unsupported file type: {file_type}")
        
#         # Step 4: Convert PDF to Markdown
#         logger.info(f"  Extracting text to Markdown...")
#         markdown_path = generate_output_path(pdf_path, MARKDOWN_DIR, ".md")
#         convert_pdf_to_markdown(pdf_path, markdown_path, enable_ocr=enable_ocr)
        
#         # Step 5: Generate chunks with custom metadata
#         logger.info(f"  Generating JSON chunks with metadata...")
#         chunks_path = generate_output_path(markdown_path, CHUNKS_DIR, ".json")
#         convert_markdown_to_chunks(
#             markdown_path, 
#             chunks_path,
#             custom_metadata=custom_metadata
#         )
        
#         return {
#             'link': link,
#             'metadata': custom_metadata,
#             'status': 'success',
#             'chunks_path': str(chunks_path),
#             'file_type': file_type
#         }