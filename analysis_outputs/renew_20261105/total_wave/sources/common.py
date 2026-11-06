# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "lightgbm"]
# ///
"""Shared paths and content-addressed experiment records."""
import hashlib
import json
from pathlib import Path
from typing import Final

ROOT: Final = Path(__file__).resolve().parents[2]
OUT: Final = ROOT / "analysis_outputs/autoresearch_20261103"
CACHE: Final = OUT / "cache"
SOURCE: Final = Path(__file__).resolve().parent


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def save_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, allow_nan=False), encoding="utf-8")
