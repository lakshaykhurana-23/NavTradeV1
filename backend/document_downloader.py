"""
Document downloader for URLs and direct PDF links.

Supports:
- Direct PDF links (https://example.com/file.pdf)
- Webpage URLs (converts to PDF using Playwright)
- DOCX links
"""
import requests
from pathlib import Path
from urllib.parse import urlparse, unquote
import logging
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)


class DocumentDownloader:
    """Download documents from URLs."""
    
    def __init__(self, download_dir: Path):
        """
        Initialize downloader.
        
        Args:
            download_dir: Directory to save downloaded files
        """
        self.download_dir = download_dir
        self.download_dir.mkdir(parents=True, exist_ok=True)
    
    def download(self, url: str, filename: str = None) -> Path:
        """
        Download a document from URL.
        
        Automatically detects type:
        - .pdf, .docx links → direct download
        - Other URLs → convert webpage to PDF
        
        Args:
            url: URL to download from
            filename: Optional custom filename (auto-generated if not provided)
            
        Returns:
            Path to downloaded file
            
        Raises:
            Exception: If download fails
        """
        logger.info(f"Downloading from: {url}")
        
        # Determine file type from URL
        parsed_url = urlparse(url)
        url_path = unquote(parsed_url.path)
        
        # Check if it's a direct file link
        if url_path.endswith('.pdf'):
            return self._download_pdf(url, filename)
        elif url_path.endswith(('.docx', '.doc')):
            return self._download_docx(url, filename)
        else:
            # It's a webpage - convert to PDF
            return self._webpage_to_pdf(url, filename)
    
    def _download_pdf(self, url: str, filename: str = None) -> Path:
        """Download PDF directly."""
        if not filename:
            # Extract filename from URL
            filename = self._get_filename_from_url(url, '.pdf')
        
        output_path = self.download_dir / filename
        
        logger.info(f"Downloading PDF: {filename}")
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"✓ Downloaded: {output_path}")
            return output_path
        
        except Exception as e:
            logger.error(f"Failed to download PDF: {e}")
            raise
    
    def _download_docx(self, url: str, filename: str = None) -> Path:
        """Download DOCX directly."""
        if not filename:
            filename = self._get_filename_from_url(url, '.docx')
        
        output_path = self.download_dir / filename
        
        logger.info(f"Downloading DOCX: {filename}")
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"✓ Downloaded: {output_path}")
            return output_path
        
        except Exception as e:
            logger.error(f"Failed to download DOCX: {e}")
            raise
    
    def _webpage_to_pdf(self, url: str, filename: str = None) -> Path:
        """Convert webpage to PDF using Playwright."""
        if not filename:
            # Create filename from URL domain and path
            parsed = urlparse(url)
            safe_name = f"{parsed.netloc}_{parsed.path}".replace('/', '_').replace('.', '_')
            filename = f"{safe_name}.pdf"
        
        if not filename.endswith('.pdf'):
            filename += '.pdf'
        
        output_path = self.download_dir / filename
        
        logger.info(f"Converting webpage to PDF: {filename}")
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page()
                
                # Load page
                page.goto(url, wait_until="networkidle", timeout=60000)
                
                # Generate PDF
                page.pdf(
                    path=str(output_path),
                    format="A4",
                    print_background=True
                )
                
                browser.close()
            
            logger.info(f"✓ Converted: {output_path}")
            return output_path
        
        except Exception as e:
            logger.error(f"Failed to convert webpage: {e}")
            raise
    
    def _get_filename_from_url(self, url: str, default_ext: str) -> str:
        """Extract filename from URL or generate one."""
        parsed_url = urlparse(url)
        url_path = unquote(parsed_url.path)
        
        # Try to get filename from URL
        if url_path and '/' in url_path:
            filename = url_path.split('/')[-1]
            if filename and len(filename) > 0:
                return filename
        
        # Generate filename from domain
        domain = parsed_url.netloc.replace('www.', '')
        filename = f"{domain}_document{default_ext}"
        return filename
    
    def download_batch(self, urls: list) -> dict:
        """
        Download multiple URLs.
        
        Args:
            urls: List of URLs to download
            
        Returns:
            Dictionary mapping URLs to downloaded file paths
        """
        results = {}
        
        for url in urls:
            try:
                file_path = self.download(url)
                results[url] = {
                    'status': 'success',
                    'file_path': str(file_path)
                }
            except Exception as e:
                results[url] = {
                    'status': 'failed',
                    'error': str(e)
                }
        
        return results