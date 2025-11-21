"""Chunk raw text into digestible pieces."""

from __future__ import annotations

import math
import re
from typing import List

from .config import settings


def split_into_chunks(text: str) -> List[str]:
    """Simple whitespace-based chunking with overlap."""
    tokens = re.split(r"\s+", text.strip())
    if not tokens:
        return []
    size = settings.chunking.target_tokens
    overlap = settings.chunking.overlap_tokens
    chunks: List[str] = []
    start = 0
    while start < len(tokens):
        end = min(len(tokens), start + size)
        chunk_tokens = tokens[start:end]
        chunks.append(" ".join(chunk_tokens))
        if end == len(tokens):
            break
        start = max(end - overlap, start + math.ceil(size / 2))
    return chunks

