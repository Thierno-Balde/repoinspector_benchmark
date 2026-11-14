"""A clean example module."""

from pathlib import Path


def read_name(path: str) -> str:
    return Path(path).name
