from functools import lru_cache

from .data_extractor import DataExtractor
from django.conf import settings
from pathlib import Path


@lru_cache
def get_data_extractor() -> DataExtractor:
    """
    Lazily create and cache a single DataExtractor instance
    for the current Django process.

    - Первый вызов создаёт объект и грузит Excel'и.
    - Все последующие вызовы возвращают тот же объект.
    """
    MODULE_DIR = Path(__file__).resolve().parent
    DEFAULT_DATA_DIR = MODULE_DIR / "data"
    return DataExtractor(Path(DEFAULT_DATA_DIR))