"""
Convert HTML files to PDF using Playwright.
"""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright


async def _html_to_pdf_async(input_path: Path, output_path: Path) -> Path:
    """
    Async function to convert HTML to PDF.
    
    Args:
        input_path: Path to input HTML file
        output_path: Path for output PDF file
        
    Returns:
        Path to the generated PDF file
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        # Load HTML file
        await page.goto(
            f"file://{input_path.absolute()}",
            wait_until="networkidle"
        )
        
        # Generate PDF
        await page.pdf(
            path=str(output_path),
            format="A4",
            print_background=True
        )
        
        await browser.close()
    
    return output_path


def convert_html_to_pdf(input_path: str | Path, output_path: str | Path) -> Path:
    """
    Convert HTML file to PDF using Playwright/Chromium.
    
    This is a synchronous wrapper that should NOT be called from async code.
    Use convert_html_to_pdf_async() instead when in async context.
    
    Args:
        input_path: Path to input HTML file
        output_path: Path for output PDF file
        
    Returns:
        Path to the generated PDF file
        
    Raises:
        FileNotFoundError: If input file doesn't exist
        RuntimeError: If called from within an async event loop
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Check if an event loop is already running
    try:
        asyncio.get_running_loop()
        raise RuntimeError(
            "convert_html_to_pdf() cannot be called from async context. "
            "Use 'await convert_html_to_pdf_async()' instead."
        )
    except RuntimeError as e:
        if "cannot be called from async context" in str(e):
            raise
        # No event loop running, proceed with asyncio.run()
        pass
    
    asyncio.run(_html_to_pdf_async(input_path, output_path))
    
    return output_path


async def convert_html_to_pdf_async(input_path: str | Path, output_path: str | Path) -> Path:
    """
    Async version of convert_html_to_pdf for use in async contexts.
    
    Args:
        input_path: Path to input HTML file
        output_path: Path for output PDF file
        
    Returns:
        Path to the generated PDF file
        
    Raises:
        FileNotFoundError: If input file doesn't exist
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Run async conversion
    return await _html_to_pdf_async(input_path, output_path)