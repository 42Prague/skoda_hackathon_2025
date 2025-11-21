"""
Translation cache background task is disabled for the MVP scope to prevent
startup failures caused by missing localization services.
"""

from swx_api.core.middleware.logging_middleware import logger


async def refresh_translation_cache():
    """Placeholder coroutine for compatibility."""
    logger.info("Translation cache refresh is disabled for MVP scope.")


def start_cache_refresh():
    """Do not start any background work for MVP."""
    logger.info("Translation cache background task is disabled.")
