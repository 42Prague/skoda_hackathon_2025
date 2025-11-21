"""
PDF text extraction module for document processing.
Architecture requirement: Extract text before chunking.
"""
import os
from typing import Optional, List
import io

try:
    import PyPDF2
    PDF2_AVAILABLE = True
except ImportError:
    PDF2_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False


def extract_text_from_pdf(file_content: bytes) -> str:
    """
    Extract text from PDF file content (bytes).
    Tries pdfplumber first (better), falls back to PyPDF2.
    
    Args:
        file_content: PDF file content as bytes
    
    Returns:
        Extracted text as string
    """
    if not file_content:
        raise ValueError("PDF file content is empty")
    
    text = ""
    
    # Try pdfplumber first (better text extraction)
    if PDFPLUMBER_AVAILABLE:
        try:
            with pdfplumber.open(io.BytesIO(file_content)) as pdf:
                pages_text = []
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        pages_text.append(page_text)
                text = "\n\n".join(pages_text)
                if text.strip():
                    return text
        except Exception as e:
            print(f"pdfplumber extraction failed: {e}, trying PyPDF2...")
    
    # Fallback to PyPDF2
    if PDF2_AVAILABLE:
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            pages_text = []
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    pages_text.append(page_text)
            text = "\n\n".join(pages_text)
            if text.strip():
                return text
        except Exception as e:
            print(f"PyPDF2 extraction failed: {e}")
    
    if not text.strip():
        raise ValueError("Could not extract text from PDF. Install pdfplumber or PyPDF2.")
    
    return text


def extract_text_by_pages(file_content: bytes) -> List[str]:
    """
    Extract text from PDF, returning a list of page texts.
    Useful for page-aware chunking.
    
    Args:
        file_content: PDF file content as bytes
    
    Returns:
        List of page texts
    """
    if not file_content:
        raise ValueError("PDF file content is empty")
    
    pages = []
    
    # Try pdfplumber first
    if PDFPLUMBER_AVAILABLE:
        try:
            with pdfplumber.open(io.BytesIO(file_content)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    pages.append(page_text if page_text else "")
                if any(pages):
                    return pages
        except Exception as e:
            print(f"pdfplumber extraction failed: {e}, trying PyPDF2...")
    
    # Fallback to PyPDF2
    if PDF2_AVAILABLE:
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                pages.append(page_text if page_text else "")
            if any(pages):
                return pages
        except Exception as e:
            print(f"PyPDF2 extraction failed: {e}")
    
    if not any(pages):
        raise ValueError("Could not extract text from PDF. Install pdfplumber or PyPDF2.")
    
    return pages

