"""
Module: utils/hasher.py
Purpose: SHA-256 content hashing for deduplication of crawled pages.
         Provides a single deterministic hash for any text string so that
         duplicate pages (same content, different URLs) are never stored twice.
Author: KnowledgeSpider Engine
"""

import hashlib
from pathlib import Path


# ── Constants ────────────────────────────────────────────────────────────────
HASH_ALGORITHM: str = "sha256"
ENCODING: str = "utf-8"


def hash_content(text: str) -> str:
    """
    Compute the SHA-256 hex digest of a text string.

    Normalises whitespace before hashing so that minor formatting differences
    between two otherwise identical documents produce the same hash.

    Args:
        text: Raw or cleaned text content to hash.

    Returns:
        64-character lowercase hex string (SHA-256 digest).

    Example:
        >>> hash_content("Hello, world!")
        '315f5bdb76d078c43b8ac0064e4a0164612b1fce77c869345bfc94c75894edd3'
    """
    normalised: str = " ".join(text.split())
    digest: str = hashlib.new(HASH_ALGORITHM, normalised.encode(ENCODING)).hexdigest()
    return digest


def hash_file(path: Path) -> str:
    """
    Compute the SHA-256 hex digest of a file's contents.

    Reads the file in binary chunks so it can handle large files without
    loading everything into memory.

    Args:
        path: Absolute or relative path to the file.

    Returns:
        64-character lowercase hex string (SHA-256 digest).

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    hasher = hashlib.new(HASH_ALGORITHM)
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65_536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def hashes_match(text_a: str, text_b: str) -> bool:
    """
    Return True if two text strings produce the same SHA-256 hash.

    Useful for quick duplicate checks without storing both strings.

    Args:
        text_a: First text string.
        text_b: Second text string.

    Returns:
        True if both strings hash to the same digest.
    """
    return hash_content(text_a) == hash_content(text_b)
