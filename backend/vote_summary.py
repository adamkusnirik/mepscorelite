#!/usr/bin/env python3
"""
Utility helpers for reducing the size of the votes attendance data.

The original dataset stored one row per vote per MEP (~27M rows) in the
`votes_attended` table, which inflated the SQLite file close to 2 GB.
This module aggregates the raw ParlTrack votes dump into a compact
summary table and (optionally) drops the heavyweight table.
"""

from __future__ import annotations

import io
import json
import sqlite3
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import DefaultDict, Dict, Iterable, Iterator, MutableMapping, Set, Tuple

import zstandard as zstd

# Keep only the terms that are used by the public site (8th onwards).
# Older terms can easily be re-generated from the ParlTrack dump if needed.
TERM_WINDOWS: Tuple[Tuple[int, datetime, datetime], ...] = (
    (8, datetime(2014, 7, 1), datetime(2019, 7, 2)),
    (9, datetime(2019, 7, 2), datetime(2024, 7, 16)),
    (10, datetime(2024, 7, 16), datetime(2029, 7, 15)),
)


@dataclass(frozen=True)
class Config:
    db_path: Path = Path("data/meps.db")
    votes_file: Path = Path("data/parltrack/ep_votes.json.zst")
    min_term: int = 8
    drop_raw_table: bool = True


class VoteSummaryError(RuntimeError):
    """Raised when the summary cannot be generated."""


def _detect_term(timestamp: str, min_term: int) -> int | None:
    """
    Convert the ParlTrack timestamp (UTC ISO string) into an EP term number.

    Returns None when the timestamp is outside of the configured term windows.
    """
    if not timestamp:
        return None

    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None

    for term, start, end in TERM_WINDOWS:
        if term < min_term:
            continue
        if start <= dt < end:
            return term
    return None


def _iter_votes(votes_file: Path) -> Iterator[dict]:
    """
    Lazily stream the votes array from the compressed ParlTrack dump.

    The file holds ~43k votes which expands to ~200 MB – loading everything
    at once is acceptable, but the stream keeps memory usage predictable.
    """
    if not votes_file.exists():
        raise VoteSummaryError(f"Votes dump not found: {votes_file}")

    with votes_file.open("rb") as fh:
        reader = zstd.ZstdDecompressor().stream_reader(fh)
        text_stream = io.TextIOWrapper(reader, encoding="utf-8")
        yield from json.load(text_stream)


def aggregate_vote_attendance(
    votes: Iterable[dict], min_term: int
) -> Tuple[Dict[int, Dict[int, int]], Dict[int, int]]:
    """
    Reduce the verbose votes array into:
      * per-term, per-MEP attendance counts
      * total number of votes cast in a term (for attendance rates)
    """
    attendance: DefaultDict[int, DefaultDict[int, int]] = defaultdict(lambda: defaultdict(int))
    total_vote_ids: DefaultDict[int, Set[str]] = defaultdict(set)

    for vote in votes:
        ts = vote.get("ts")
        term = _detect_term(ts, min_term)
        if term is None:
            continue

        vote_id = str(vote.get("voteid") or "")
        if vote_id:
            total_vote_ids[term].add(vote_id)

        vote_groups = vote.get("votes") or {}
        # Guard against double counting: the same MEP must not be counted twice for a single vote.
        seen_in_vote: Set[int] = set()

        for outcome_key in ("+", "-", "0"):
            outcome = vote_groups.get(outcome_key)
            if not isinstance(outcome, dict):
                continue

            groups = outcome.get("groups") or {}
            for members in groups.values():
                if not isinstance(members, list):
                    continue
                for member in members:
                    mep_id = member.get("mepid")
                    if mep_id is None:
                        continue
                    try:
                        mep_id_int = int(mep_id)
                    except (TypeError, ValueError):
                        continue
                    if mep_id_int in seen_in_vote:
                        continue

                    attendance[term][mep_id_int] += 1
                    seen_in_vote.add(mep_id_int)

    # Convert vote id sets into counts
    total_counts = {term: len(vote_ids) for term, vote_ids in total_vote_ids.items()}
    attendance_dict = {term: dict(meps) for term, meps in attendance.items()}
    return attendance_dict, total_counts


def update_vote_summary(config: Config = Config()) -> Tuple[int, int]:
    """
    Aggregate the vote attendance data into compact summary tables.

    Returns:
        Tuple of (number of summary rows inserted, number of term totals inserted).
    """
    votes_iter = _iter_votes(config.votes_file)
    attendance_by_term, totals_by_term = aggregate_vote_attendance(votes_iter, config.min_term)

    if not attendance_by_term:
        raise VoteSummaryError("No attendance data extracted – aborting to avoid wiping tables.")

    conn = sqlite3.connect(config.db_path)
    try:
        cur = conn.cursor()

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS mep_vote_summary (
                mep_id INTEGER NOT NULL,
                term INTEGER NOT NULL,
                votes_attended INTEGER NOT NULL,
                PRIMARY KEY (mep_id, term)
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS term_vote_totals (
                term INTEGER PRIMARY KEY,
                votes_total INTEGER NOT NULL
            )
            """
        )

        # Clear existing rows for the tracked terms to keep the table minimal.
        tracked_terms = tuple(sorted(attendance_by_term.keys()))
        placeholders = ",".join("?" for _ in tracked_terms)
        if tracked_terms:
            cur.execute(
                f"DELETE FROM mep_vote_summary WHERE term IN ({placeholders})",
                tracked_terms,
            )
            cur.execute(
                f"DELETE FROM term_vote_totals WHERE term IN ({placeholders})",
                tracked_terms,
            )

        summary_rows = [
            (mep_id, term, votes)
            for term, term_data in attendance_by_term.items()
            for mep_id, votes in term_data.items()
        ]
        cur.executemany(
            "INSERT OR REPLACE INTO mep_vote_summary (mep_id, term, votes_attended) VALUES (?, ?, ?)",
            summary_rows,
        )

        total_rows = [(term, totals_by_term.get(term, 0)) for term in tracked_terms]
        cur.executemany(
            "INSERT OR REPLACE INTO term_vote_totals (term, votes_total) VALUES (?, ?)",
            total_rows,
        )

        if config.drop_raw_table:
            cur.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='votes_attended'"
            )
            if cur.fetchone():
                cur.execute("DROP TABLE votes_attended")

        conn.commit()
        conn.execute("VACUUM")
        return len(summary_rows), len(total_rows)
    finally:
        conn.close()


def main(argv: Iterable[str] | None = None) -> None:
    try:
        summary_count, term_count = update_vote_summary()
    except VoteSummaryError as exc:
        print(f"[vote-summary] ERROR: {exc}")
        raise SystemExit(1)

    print(
        f"[vote-summary] Compacted vote attendance into {summary_count:,} rows "
        f"across {term_count} term totals."
    )


if __name__ == "__main__":
    main()

