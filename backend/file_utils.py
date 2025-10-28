#!/usr/bin/env python3
"""
Shared helpers for loading large ParlTrack JSON blobs without duplicating code.

The loader automatically falls back to `.json.zst` compressed variants, which
allows the repository to keep only the compressed copy of multi-hundred-megabyte
files while existing code keeps referencing the original `.json` paths.
"""

from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any, Iterable, Iterator

import ijson
import zstandard as zstd


def _zst_variant(path: Path) -> Path:
    """Return the `.zst` companion path for the given JSON file."""
    return path if path.suffix == ".zst" else path.with_suffix(path.suffix + ".zst")


def _json_variant(path: Path) -> Path:
    """Return the plain `.json` companion path for a `.json.zst` file."""
    return path.with_suffix("") if path.suffix == ".zst" else path


def resolve_json_path(path: Path | str) -> Path:
    """
    Resolve the on-disk path for a ParlTrack JSON blob.

    The caller can reference either the raw `.json` file or its `.json.zst`
    compressed counterpart. This resolver prefers an existing compressed file
    so the uncompressed copy can be safely deleted to save space.
    """
    candidate = Path(path)
    if candidate.exists():
        return candidate

    compressed = _zst_variant(candidate)
    if compressed.exists():
        return compressed

    plain = _json_variant(candidate)
    if plain.exists():
        return plain

    return candidate


def load_json_auto(path: Path | str) -> Any:
    """
    Load JSON data from either an uncompressed file or a `.json.zst` archive.
    """
    resolved = resolve_json_path(path)
    if not resolved.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")

    if resolved.suffix == ".zst":
        with resolved.open("rb") as handle:
            reader = zstd.ZstdDecompressor().stream_reader(handle)
            return json.load(io.TextIOWrapper(reader, encoding="utf-8"))

    return json.loads(resolved.read_text(encoding="utf-8"))


def load_combined_dataset(primary: Path | str, fallbacks: Iterable[Path | str]) -> Any:
    """
    Load a dataset from a primary JSON path, falling back to a list of
    alternative term-specific files. When multiple fallback files exist,
    their contents (assumed to be lists) are concatenated.
    """
    try:
        return load_json_auto(primary)
    except FileNotFoundError:
        pass

    combined: list[Any] = []
    for fallback in fallbacks:
        resolved = resolve_json_path(fallback)
        if not resolved.exists():
            continue
        data = load_json_auto(resolved)
        if isinstance(data, list):
            combined.extend(data)
        elif data is not None:
            combined.append(data)

    if not combined:
        raise FileNotFoundError(f"No dataset found for {primary}")

    return combined


def stream_json_items(path: Path | str) -> Iterator[Any]:
    """Yield items from a JSON array without loading the entire file into memory."""
    resolved = resolve_json_path(path)
    if not resolved.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")

    if resolved.suffix == ".zst":
        with resolved.open("rb") as raw:
            reader = zstd.ZstdDecompressor().stream_reader(raw)
            text_stream = io.TextIOWrapper(reader, encoding="utf-8")
            try:
                yield from ijson.items(text_stream, "item")
            finally:
                text_stream.close()
                reader.close()
    else:
        with resolved.open("r", encoding="utf-8") as handle:
            yield from ijson.items(handle, "item")
