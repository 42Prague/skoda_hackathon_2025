"""S³ — Skoda Smart Stream core package."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("s3")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.1.0"

__all__ = ["__version__"]

