"""Data loading utilities."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterator, Tuple

import pandas as pd

logger = logging.getLogger(__name__)


def iter_text_sources(data_dir: Path) -> Iterator[Tuple[str, str]]:
    """Yield (path, text) tuples from supported files."""
    for path in sorted(data_dir.rglob("*")):
        if path.is_dir():
            continue
        suffix = path.suffix.lower()
        try:
            if suffix in {".txt"}:
                yield str(path), path.read_text(encoding="utf-8", errors="ignore")
            elif suffix in {".xlsx", ".xls"}:
                text = _flatten_excel(path)
                if text:
                    yield str(path), text
            else:
                logger.debug("Skipping unsupported file %s", path)
        except Exception as exc:  # pragma: no cover - best-effort ingestion
            logger.warning("Failed to read %s: %s", path, exc)


def _flatten_excel(path: Path) -> str:
    frames = pd.read_excel(path, sheet_name=None, dtype=str)
    parts = []
    for sheet, df in frames.items():
        df = df.fillna("")
        parts.append(f"# Sheet: {sheet}")
        parts.extend(df.apply(lambda row: " | ".join(row.astype(str)), axis=1))
    return "\n".join(parts)

