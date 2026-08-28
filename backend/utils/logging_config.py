"""Centralised logging configuration for the EchoScape backend."""
from __future__ import annotations

import logging
import sys

_CONFIGURED = False


def configure_logging(level: str = "INFO") -> logging.Logger:
    """Configure root-level logging once and return the app logger."""
    global _CONFIGURED
    if not _CONFIGURED:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
                datefmt="%H:%M:%S",
            )
        )
        root = logging.getLogger()
        root.setLevel(getattr(logging, level.upper(), logging.INFO))
        root.addHandler(handler)
        _CONFIGURED = True
    return logging.getLogger("echoscape")
