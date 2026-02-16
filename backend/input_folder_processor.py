"""
Process documents from data/input folder using config sheet metadata.

Files in data/input/ are named like: D01.pdf, D02.html, D03.docx
Config sheet has Id column matching the filename prefix (D01, D02, etc.)
"""
import pandas as pd
import json
from pathlib import Path
import logging
from typing import Dict, List, Any, Optional
from backend.config import INPUT_DIR, CHUNKS_DIR, PDF_DIR, MARKDOWN_DIR
from backend.utils import detect_file_type, generate_output_path
from backend.converters import (
    convert_docx_to_pdf,
    convert_html_to_pdf,
    convert_pdf_to_markdown
)
from backend.converters.markdown_to_chunks import convert_markdown_to_chunks

logger = logging.getLogger(__name__)


class InputFolderProcessor:
    """
    Process all documents from data/input/ folder using config sheet for metadata.
    
    Workflow:
    1. Scan data/input/ for files (D01.pdf, D02.html, etc.)
    2. Extract document ID from filename (D01, D02, etc.)
    3. Look up metadata in config sheet by Id column
    4. Skip if all of Keywords, Categories, Description are empty
    5. Process file and add metadata to chunks
    6. Save chunks as individual files in data/chunks/D01/, data/chunks/D02/, etc.
    """
    
    # Column mapping from config sheet to metadata keys
    COLUMN_MAPPING = {
        'Document ID': None,  # Used for matching, not in metadata
        'document_id': 'document_id',
        'Document Type': 'document_type',
        'Document Link': 'document_link',     
        'Document Title': 'document_title' ,
        'Document Description': 'document_description',
        'Document Keywords': 'document_keywords',
        'Document Categories': 'category_ids',
    }
    
    def __init__(self, config_file: Path):
        """
        Initialize processor.
        
        Args:
            config_file: Path to Excel (.xlsx) or CSV file with metadata
        """
        self.config_file = Path(config_file)
        
        # Load config
        self.df = self._load_config()
        
        # Create lookup dictionary: Id -> metadata
        self.metadata_lookup = self._create_metadata_lookup()
        
        logger.info(f"Loaded config with {len(self.df)} entries")
        logger.info(f"Metadata available for {len(self.metadata_lookup)} document IDs")
    
    def _load_config(self) -> pd.DataFrame:
        """Load config file (Excel or CSV)."""
        if self.config_file.suffix == '.csv':
            return pd.read_csv(self.config_file)
        elif self.config_file.suffix in ['.xlsx', '.xls']:
            return pd.read_excel(self.config_file)
        else:
            raise ValueError(f"Unsupported file type: {self.config_file.suffix}")
    
    def _parse_json_array(self, value: str) -> List[str]:
        """Parse JSON array string into list."""
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if item]
            return []
        except (json.JSONDecodeError, TypeError):
            return []

    def _parse_list_field(self, value: Any) -> List[str]:
        """
        Parse comma-separated string into list.
        
        Args:
            value: String with comma-separated values or NaN
            
        Returns:
            List of cleaned strings
        """
        # Handle NaN/None
        if pd.isna(value) or value is None or value == '':
            return []
        
        # Convert to string and split by comma
        value_str = str(value)
        items = value_str.split(',')
        
        # Trim spaces and remove empty strings
        cleaned_items = [item.strip() for item in items if item.strip()]
        
        return cleaned_items
    
    def _has_metadata(self, row: pd.Series) -> bool:
        """
        Check if row has at least one of: Keywords, Categories, or Description.
        
        Args:
            row: DataFrame row
            
        Returns:
            True if at least one metadata field has content
        """
        # Check Keywords
        if 'Document Keywords' in row.index and pd.notna(row['Document Keywords']):       
            return True
        
        # Check Document Categories
        if 'Document Categories' in row.index and pd.notna(row['Document Categories']):   
            return True
        
        # Check Document Description
        if 'Document Description' in row.index and pd.notna(row['Document Description']): 
            return True
        
        return False    
    
    def _extract_metadata(self, row: pd.Series) -> Dict[str, Any]:
        """
        Extract metadata from a config sheet row.
        
        Args:
            row: DataFrame row
            
        Returns:
            Dictionary with metadata
        """
        metadata = {}
        
        # Add document_id from Document ID column
        if 'Document ID' in row.index and pd.notna(row['Document ID']):
            metadata['document_id'] = str(row['Document ID']).strip()
        else:
            metadata['document_id'] = ""
        
        # Map other columns
        for col_name, meta_key in self.COLUMN_MAPPING.items():
            if meta_key is None or col_name == 'Document ID':
                continue
            
            if col_name not in row.index:
                continue
            
            value = row[col_name]
            
            # Skip NaN values
            if pd.isna(value):
                metadata[meta_key] = "" if meta_key in ['document_type', 'document_description', 'document_link', 'document_title'] else []
                continue
            
            if col_name == 'Document Keywords':
                # If it's already a list (from Excel with proper array), use it directly
                if isinstance(value, list):
                    metadata[meta_key] = value
                # If it's a string, check if it's JSON formatted
                elif isinstance(value, str):
                    value_stripped = value.strip()
                    # Check if it looks like a JSON array
                    if value_stripped.startswith('[') and value_stripped.endswith(']'):
                        # Try to parse as JSON
                        parsed = self._parse_json_array(value_stripped)
                        if parsed:
                            metadata[meta_key] = parsed
                        else:
                            # If JSON parsing fails, fall back to comma-separated
                            metadata[meta_key] = self._parse_list_field(value)
                    else:
                        # Normal comma-separated string
                        metadata[meta_key] = self._parse_list_field(value)
                else:
                    metadata[meta_key] = []
            # Handle Document Categories normally (needs parsing)
            elif col_name == 'Document Categories':
                metadata[meta_key] = self._parse_list_field(value)
            else:
                # Regular string fields (document_type, document_description, etc.)
                metadata[meta_key] = str(value).strip()
        
        return metadata
    
    def _create_metadata_lookup(self) -> Dict[str, Dict]:
        """
        Create lookup dictionary: document ID -> metadata.
        
        Returns:
            Dictionary mapping document IDs to their metadata
        """
        lookup = {}
        
        if 'Document ID' not in self.df.columns:
            logger.warning("No 'Document ID' column found in config sheet")
            return lookup
        
        for idx, row in self.df.iterrows():
            # Skip rows without Document ID
            if pd.isna(row['Document ID']) or str(row['Document ID']).strip() == '':
                continue
            
            doc_id = str(row['Document ID']).strip()
            
            # Only include if has metadata
            if self._has_metadata(row):
                metadata = self._extract_metadata(row)
                lookup[doc_id] = metadata
                logger.debug(f"Loaded metadata for {doc_id}")
            else:
                logger.debug(f"Skipping {doc_id} - no metadata content")
        
        return lookup
    
    def _get_input_files(self) -> List[Path]:
        """
        Get all supported files from input directory.
        
        Returns:
            List of input file paths
        """
        input_files = []
        
        # Supported extensions
        supported_extensions = ['.pdf', '.docx', '.doc', '.html', '.htm']
        
        # Get all files
        for file_path in INPUT_DIR.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                input_files.append(file_path)
        
        # Sort for consistent ordering
        return sorted(input_files)
    
    def _extract_doc_id_from_filename(self, filename: str) -> Optional[str]:
        """
        Extract document ID from filename.
        
        Examples:
            "D01.pdf" -> "D01"
            "D02.html" -> "D02"
            "D123.docx" -> "D123"
        
        Args:
            filename: Filename (with or without extension)
            
        Returns:
            Document ID or None if not found
        """
        # Remove extension
        name_without_ext = Path(filename).stem
        
        # Return the stem as document ID
        return name_without_ext
    
    def process_all(self, enable_ocr: bool = False) -> Dict:
        """
        Process all documents in data/input/ folder.
        
        Args:
            enable_ocr: Whether to enable OCR for PDFs
            
        Returns:
            Dictionary with processing statistics
        """
        logger.info("=" * 70)
        logger.info("PROCESSING ALL FILES FROM data/input/")
        logger.info("=" * 70)
        
        # Get all input files
        input_files = self._get_input_files()
        
        if not input_files:
            logger.warning("No files found in data/input/")
            return {
                'total_files': 0,
                'processed': 0,
                'skipped_no_metadata': 0,
                'skipped_no_id': 0,
                'failed': 0,
                'total_chunks': 0,
                'results': []
            }
        
        logger.info(f"Found {len(input_files)} file(s) in data/input/")
        logger.info("")
        
        results = []
        processed_count = 0
        skipped_no_metadata_count = 0
        skipped_no_id_count = 0
        failed_count = 0
        total_chunks = 0
        
        for idx, input_file in enumerate(input_files, 1):
            logger.info(f"[{idx}/{len(input_files)}] File: {input_file.name}")
            
            try:
                # Extract document ID from filename
                doc_id = self._extract_doc_id_from_filename(input_file.name)
                
                if not doc_id:
                    logger.warning(f"  ⊘ Skipped - Could not extract document ID from filename")
                    skipped_no_id_count += 1
                    results.append({
                        'file': input_file.name,
                        'status': 'skipped_no_id',
                        'reason': 'Could not extract document ID'
                    })
                    logger.info("")
                    continue
                
                logger.info(f"  Document ID: {doc_id}")
                
                # Check if metadata exists for this ID
                if doc_id not in self.metadata_lookup:
                    logger.warning(f"  ⊘ Skipped - No metadata in config (or all metadata empty)")
                    skipped_no_metadata_count += 1
                    results.append({
                        'file': input_file.name,
                        'document_id': doc_id,
                        'status': 'skipped_no_metadata',
                        'reason': 'No metadata found or all metadata fields empty'
                    })
                    logger.info("")
                    continue
                
                # Get metadata
                metadata = self.metadata_lookup[doc_id]
                
                logger.info(f"  Type: {metadata.get('document_type', 'N/A')}")
                logger.info(f"  Keywords: {metadata.get('document_keywords', [])}")
                logger.info(f"  Categories: {metadata.get('category_ids', [])}")
                
                # Process the file
                result = self._process_single_file(input_file, doc_id, metadata, enable_ocr)
                
                results.append(result)
                processed_count += 1
                total_chunks += result.get('chunk_count', 0)
                
                logger.info(f"  ✓ Success: {result['chunks_dir']}")
                logger.info(f"  ✓ Created {result['chunk_count']} chunks")
            
            except Exception as e:
                logger.error(f"  ✗ Failed: {e}")
                failed_count += 1
                results.append({
                    'file': input_file.name,
                    'document_id': doc_id if 'doc_id' in locals() else 'unknown',
                    'status': 'failed',
                    'error': str(e)
                })
            
            logger.info("")
        
        # Summary
        logger.info("=" * 70)
        logger.info("PROCESSING SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Total files found:              {len(input_files)}")
        logger.info(f"Successfully processed:         {processed_count}")
        logger.info(f"Skipped (no metadata):          {skipped_no_metadata_count}")
        logger.info(f"Skipped (no ID):                {skipped_no_id_count}")
        logger.info(f"Failed:                         {failed_count}")
        logger.info(f"Total chunks created:           {total_chunks}")
        logger.info("=" * 70)
        
        return {
            'total_files': len(input_files),
            'processed': processed_count,
            'skipped_no_metadata': skipped_no_metadata_count,
            'skipped_no_id': skipped_no_id_count,
            'failed': failed_count,
            'total_chunks': total_chunks,
            'results': results
        }
    
    def _process_single_file(
        self,
        input_file: Path,
        doc_id: str,
        metadata: Dict,
        enable_ocr: bool
    ) -> Dict:
        """
        Process a single file.
        
        Steps:
        1. Detect file type
        2. Convert to PDF (if needed)
        3. Extract to Markdown
        4. Generate chunks with metadata
        5. Save as individual files in data/chunks/DOC_ID/
        
        Args:
            input_file: Path to input file
            doc_id: Document ID
            metadata: Metadata dictionary
            enable_ocr: Whether to enable OCR
            
        Returns:
            Dictionary with processing result
        """
        # Detect file type
        file_type = detect_file_type(input_file)
        if not file_type:
            raise ValueError(f"Unsupported file type: {input_file.suffix}")
        
        # Convert to PDF if needed
        if file_type == "pdf":
            pdf_path = PDF_DIR / input_file.name
            if input_file != pdf_path:
                import shutil
                shutil.copy2(input_file, pdf_path)
        elif file_type == "docx":
            logger.info(f"  Converting DOCX to PDF...")
            pdf_path = generate_output_path(input_file, PDF_DIR, ".pdf")
            convert_docx_to_pdf(input_file, pdf_path)
        elif file_type == "html":
            logger.info(f"  Converting HTML to PDF...")
            pdf_path = generate_output_path(input_file, PDF_DIR, ".pdf")
            convert_html_to_pdf(input_file, pdf_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        # Convert PDF to Markdown
        logger.info(f"  Extracting text to Markdown...")
        markdown_path = generate_output_path(pdf_path, MARKDOWN_DIR, ".md")
        convert_pdf_to_markdown(pdf_path, markdown_path, enable_ocr=enable_ocr)
        
        # Generate chunks with metadata
        logger.info(f"  Generating chunks with metadata and token counts...")
        
        # Create output directory for this document
        chunks_output_dir = CHUNKS_DIR / doc_id
        
        chunks_dir, chunk_count = convert_markdown_to_chunks(
            markdown_path,
            chunks_output_dir,
            doc_id,
            custom_metadata=metadata
        )
        
        return {
            'file': input_file.name,
            'document_id': doc_id,
            'status': 'success',
            'chunks_dir': str(chunks_dir),
            'chunk_count': chunk_count,
            'file_type': file_type
        }