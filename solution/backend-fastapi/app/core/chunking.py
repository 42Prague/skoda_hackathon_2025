"""
Document chunking module for RAG pipeline.
Architecture requirement: ALWAYS chunk documents before embedding.
"""
import uuid
from typing import List, Dict, Optional
import tiktoken


def count_tokens(text: str, model: str = "gpt-4") -> int:
    """
    Count tokens in text using tiktoken.
    Default model: gpt-4 (approximates OpenAI token counting)
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except Exception:
        # Fallback: approximate 1 token = 4 characters
        return len(text) // 4


def chunk_text(
    text: str,
    max_tokens: int = 512,
    overlap_tokens: int = 50,
    chunk_by: str = "tokens"
) -> List[Dict[str, any]]:
    """
    Split text into chunks following architecture requirements:
    - max tokens per chunk: 512-1024 (default 512)
    - overlap: 10-20% (default ~10%)
    - split by tokens or semantic units
    
    Args:
        text: Text to chunk
        max_tokens: Maximum tokens per chunk (512-1024 range)
        overlap_tokens: Number of tokens to overlap between chunks
        chunk_by: "tokens" or "semantic" (semantic not yet implemented)
    
    Returns:
        List of chunk dictionaries with:
        - chunk_id
        - text
        - token_count
        - start_char
        - end_char
        - index
    """
    if chunk_by == "tokens":
        return _chunk_by_tokens(text, max_tokens, overlap_tokens)
    else:
        # Fallback to token-based chunking
        return _chunk_by_tokens(text, max_tokens, overlap_tokens)


def _chunk_by_tokens(text: str, max_tokens: int, overlap_tokens: int) -> List[Dict[str, any]]:
    """Chunk text by token count with overlap"""
    encoding = tiktoken.encoding_for_model("gpt-4")
    tokens = encoding.encode(text)
    
    chunks = []
    start_idx = 0
    
    while start_idx < len(tokens):
        # Calculate end index
        end_idx = min(start_idx + max_tokens, len(tokens))
        
        # Extract chunk tokens
        chunk_tokens = tokens[start_idx:end_idx]
        chunk_text = encoding.decode(chunk_tokens)
        
        # Create chunk metadata
        chunk = {
            "chunk_id": str(uuid.uuid4()),
            "text": chunk_text,
            "token_count": len(chunk_tokens),
            "text_length": len(chunk_text),
            "start_char": start_idx,  # Approximate character position
            "end_char": end_idx,
            "index": len(chunks)
        }
        
        chunks.append(chunk)
        
        # Move start index with overlap
        if end_idx >= len(tokens):
            break
        start_idx = end_idx - overlap_tokens
    
    return chunks


def chunk_by_pages(
    pages: List[str],
    max_tokens_per_chunk: int = 512,
    overlap_tokens: int = 50
) -> List[Dict[str, any]]:
    """
    Chunk text that is already split by pages.
    Useful for PDF documents where page boundaries are known.
    
    Args:
        pages: List of page texts
        max_tokens_per_chunk: Maximum tokens per chunk
        overlap_tokens: Overlap between chunks
    
    Returns:
        List of chunks with page information
    """
    chunks = []
    current_chunk_text = ""
    current_chunk_pages = []
    current_token_count = 0
    chunk_index = 0
    
    for page_num, page_text in enumerate(pages, start=1):
        page_tokens = count_tokens(page_text)
        
        # If adding this page would exceed max_tokens, finalize current chunk
        if current_token_count + page_tokens > max_tokens_per_chunk and current_chunk_text:
            # Finalize current chunk
            chunk = {
                "chunk_id": str(uuid.uuid4()),
                "text": current_chunk_text,
                "token_count": current_token_count,
                "text_length": len(current_chunk_text),
                "start_page": current_chunk_pages[0] if current_chunk_pages else page_num,
                "end_page": current_chunk_pages[-1] if current_chunk_pages else page_num,
                "index": chunk_index
            }
            chunks.append(chunk)
            chunk_index += 1
            
            # Start new chunk with overlap (keep last part of previous chunk)
            if overlap_tokens > 0 and current_chunk_text:
                # Simple overlap: keep last 20% of text
                overlap_text = current_chunk_text[-len(current_chunk_text)//5:]
                current_chunk_text = overlap_text
                current_token_count = count_tokens(overlap_text)
                current_chunk_pages = [current_chunk_pages[-1]] if current_chunk_pages else []
            else:
                current_chunk_text = ""
                current_token_count = 0
                current_chunk_pages = []
        
        # Add page to current chunk
        if current_chunk_text:
            current_chunk_text += "\n\n"
        current_chunk_text += page_text
        current_token_count += page_tokens
        current_chunk_pages.append(page_num)
    
    # Finalize last chunk
    if current_chunk_text:
        chunk = {
            "chunk_id": str(uuid.uuid4()),
            "text": current_chunk_text,
            "token_count": current_token_count,
            "text_length": len(current_chunk_text),
            "start_page": current_chunk_pages[0] if current_chunk_pages else 1,
            "end_page": current_chunk_pages[-1] if current_chunk_pages else len(pages),
            "index": chunk_index
        }
        chunks.append(chunk)
    
    return chunks

