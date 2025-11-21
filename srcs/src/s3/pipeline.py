"""End-to-end ingestion pipeline."""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import List

from .chunker import split_into_chunks
from .loader import iter_text_sources
from .models import ContentChunk
from .tagger import tag_text
from .vector_store import VectorStore
from .config import settings

logger = logging.getLogger(__name__)


def build_chunks() -> List[ContentChunk]:
    chunks: List[ContentChunk] = []
    for path, text in iter_text_sources(settings.data_dir):
        raw_chunks = split_into_chunks(text)
        for idx, chunk_text in enumerate(raw_chunks):
            chunk_id = _chunk_id(path, idx, chunk_text)
            tags = tag_text(chunk_text)
            chunks.append(
                ContentChunk(
                    id=chunk_id,
                    source_path=path,
                    text=chunk_text,
                    tags=tags,
                )
            )
    logger.info("Built %d chunks", len(chunks))
    return chunks


def ingest() -> List[ContentChunk]:
    logger.info("Running ingestion pipeline...")
    chunks = build_chunks()
    store = VectorStore()
    store.fit(chunks)
    store.save()
    logger.info("Stored %d chunks in vector store", len(chunks))
    return chunks


def _chunk_id(path: str, idx: int, text: str) -> str:
    digest = hashlib.md5(text.encode("utf-8")).hexdigest()  # noqa: S324
    return f"{Path(path).stem}-{idx}-{digest[:8]}"

