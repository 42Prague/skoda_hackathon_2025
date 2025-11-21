"""Compat shim for Python 3.13+ where stdlib cgi module was removed."""

from __future__ import annotations

from email.message import Message
from typing import Dict, Tuple


def parse_header(line: str) -> Tuple[str, Dict[str, str]]:
    """Minimal subset of :mod:`cgi` API used by httpx."""
    msg = Message()
    msg["content-type"] = line
    params = msg.get_params()
    if not params:
        return line, {}
    main = params[0][0]
    extras = {key: value for key, value in params[1:]}
    return main, extras

