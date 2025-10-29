#!/usr/bin/env python3
"""
Build a lightweight SQLite index for amendment details per MEP/term.

The Render backend struggles to stream the 1.5M+ amendment entries fast enough
for on-demand queries. This utility precomputes a small relational index that
allows the API to answer `amendments` category requests in milliseconds without
loading the giant ParlTrack blobs each time.
"""

from __future__ import annotations

import json
import sqlite3
import sys
import time
from pathlib import Path
from typing import Iterator

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.file_utils import resolve_json_path, stream_json_items

DATA_DIR = PROJECT_ROOT / "data"
PARLTRACK_DIR = DATA_DIR / "parltrack"
DB_PATH = DATA_DIR / "amendments_index.db"

TERMS = (8, 9, 10)


def _normalize_mep(entry: object) -> int | None:
    """Normalize a ParlTrack MEP identifier into an integer ID."""
    if entry is None:
        return None

    if isinstance(entry, dict):
        for key in ("mepid", "mepId", "UserID", "id"):
            value = entry.get(key)
            if value is not None:
                try:
                    return int(value)
                except (TypeError, ValueError):
                    return None
        return None

    try:
        return int(entry)
    except (TypeError, ValueError):
        return None


def _json_or_none(value: object) -> str | None:
    """Serialize lists/dicts to JSON, leave strings untouched."""
    if value is None:
        return None
    if isinstance(value, (list, dict)):
        if not value:
            return None
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)


def _ensure_schema(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute("PRAGMA journal_mode=WAL;")
    cur.execute("PRAGMA synchronous=OFF;")
    cur.execute("PRAGMA temp_store=MEMORY;")

    cur.executescript(
        """
        DROP TABLE IF EXISTS amendment_mep;
        DROP TABLE IF EXISTS amendments;

        CREATE TABLE amendments (
            id            INTEGER PRIMARY KEY,
            term          INTEGER NOT NULL,
            date          TEXT,
            seq           INTEGER,
            reference     TEXT,
            title         TEXT,
            committee     TEXT,
            location      TEXT,
            authors       TEXT,
            new_json      BLOB,
            old_json      BLOB,
            src           TEXT,
            dossiers      TEXT
        );

        CREATE TABLE amendment_mep (
            amendment_id  INTEGER NOT NULL,
            mep_id        INTEGER NOT NULL,
            PRIMARY KEY (amendment_id, mep_id),
            FOREIGN KEY (amendment_id) REFERENCES amendments(id)
        );

        CREATE INDEX idx_amendment_term_date ON amendments (term, date DESC, id DESC);
        CREATE INDEX idx_amendment_mep ON amendment_mep (mep_id, amendment_id);
        """
    )
    conn.commit()


def _iter_term_amendments(term: int) -> Iterator[dict]:
    """Stream amendments for a specific term."""
    preferred = PARLTRACK_DIR / f"ep_amendments_term{term}.json"
    file_path = resolve_json_path(preferred)
    if not file_path.exists():
        raise FileNotFoundError(f"Missing amendments dataset for term {term}: {preferred}")
    yield from stream_json_items(file_path)


def _shrink_text_payload(value: object, term: int) -> object:
    """Trim very large amendment texts for archived terms to keep the index compact."""
    if value is None or term >= 10:
        return value
    if isinstance(value, list):
        trimmed: list[str] = []
        remaining = 2000
        for segment in value:
            segment_text = str(segment)
            if len(segment_text) > 400:
                segment_text = segment_text[:400] + "…"
            trimmed.append(segment_text[:remaining])
            remaining -= len(trimmed[-1])
            if remaining <= 0:
                break
        return trimmed
    if isinstance(value, str) and len(value) > 800:
        return value[:800] + "…"
    return value


def build_index() -> None:
    start = time.time()
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    try:
        _ensure_schema(conn)
        cur = conn.cursor()

        amendment_id = 1
        batch_amendments: list[tuple] = []
        batch_links: list[tuple[int, int]] = []

        for term in TERMS:
            term_start = time.time()
            processed = 0
            linked = 0
            print(f"Indexing term {term} amendments...", flush=True)

            for amendment in _iter_term_amendments(term):
                mep_ids = []
                for entry in amendment.get("meps", []):
                    mep_id = _normalize_mep(entry)
                    if mep_id is not None:
                        mep_ids.append(mep_id)

                if not mep_ids:
                    amendment_id += 1
                    continue

                batch_amendments.append(
                    (
                        amendment_id,
                        term,
                        amendment.get("date"),
                        amendment.get("seq"),
                        amendment.get("reference"),
                        amendment.get("title"),
                        _json_or_none(amendment.get("committee")),
                        _json_or_none(amendment.get("location")),
                        _json_or_none(amendment.get("authors")),
                        None,
                        None,
                        amendment.get("src") or amendment.get("url"),
                        _json_or_none(amendment.get("dossiers")),
                    )
                )

                for mep_id in mep_ids:
                    batch_links.append((amendment_id, mep_id))

                amendment_id += 1
                processed += 1
                linked += len(mep_ids)

                if len(batch_amendments) >= 2000:
                    cur.executemany(
                        """
                        INSERT INTO amendments (
                            id, term, date, seq, reference, title, committee,
                            location, authors, new_json, old_json, src, dossiers
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        batch_amendments,
                    )
                    batch_amendments.clear()

                if len(batch_links) >= 5000:
                    cur.executemany(
                        "INSERT OR IGNORE INTO amendment_mep (amendment_id, mep_id) VALUES (?, ?)",
                        batch_links,
                    )
                    batch_links.clear()

                if processed % 50000 == 0:
                    conn.commit()
                    elapsed = time.time() - term_start
                    print(f"  processed {processed:,} records ({linked:,} associations) in {elapsed:.1f}s", flush=True)

            if batch_amendments:
                cur.executemany(
                    """
                    INSERT INTO amendments (
                        id, term, date, seq, reference, title, committee,
                        location, authors, new_json, old_json, src, dossiers
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    batch_amendments,
                )
                batch_amendments.clear()

            if batch_links:
                cur.executemany(
                    "INSERT OR IGNORE INTO amendment_mep (amendment_id, mep_id) VALUES (?, ?)",
                    batch_links,
                )
                batch_links.clear()

            conn.commit()
            print(f"Term {term} complete: {processed:,} amendments in {time.time() - term_start:.1f}s", flush=True)

        total_time = time.time() - start
        size_mb = DB_PATH.stat().st_size / (1024 * 1024)
        print(f"Completed index build in {total_time:.1f}s ({size_mb:.1f} MB at {DB_PATH})")
    finally:
        conn.close()


if __name__ == "__main__":
    build_index()
