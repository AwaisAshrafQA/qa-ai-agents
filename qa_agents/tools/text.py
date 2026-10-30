"""Small text helpers shared by agents."""

from __future__ import annotations

import re


def error_signature(error: str) -> str:
    """Normalise ids, numbers, hashes, emails and quoted values so the same error groups together."""
    sig = error.strip().splitlines()[0] if error.strip() else ""
    sig = re.sub(r"[\w.+-]+@[\w-]+\.[\w.]+", "<email>", sig)
    sig = re.sub(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", "<uuid>", sig, flags=re.IGNORECASE)
    sig = re.sub(r"0x[0-9a-f]+|\b[0-9a-f]*\d[0-9a-f]{7,}\b|\d+(?:\.\d+)?", "<n>", sig, flags=re.IGNORECASE)
    return sig[:160]
