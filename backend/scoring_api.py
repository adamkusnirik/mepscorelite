#!/usr/bin/env python3
"""Minimal-memory API endpoints for detailed MEP activities."""

from __future__ import annotations

import json
import sqlite3
import threading
import zlib
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional

from flask import Flask, jsonify, request
from flask_cors import CORS

try:
    from .mep_score_scorer import MEPScoreScorer
    from .file_utils import stream_json_items
except ImportError:  # pragma: no cover
    from mep_score_scorer import MEPScoreScorer  # type: ignore
    from file_utils import stream_json_items  # type: ignore


app = Flask(__name__)
CORS(app)

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
PARLTRACK_DIR = DATA_DIR / "parltrack"

# Ensure directories exist even in read-only deployments (no-op if already present)
DATA_DIR.mkdir(parents=True, exist_ok=True)
PARLTRACK_DIR.mkdir(parents=True, exist_ok=True)

scorer = MEPScoreScorer(db_path=str(DATA_DIR / "meps.db"))

TERM_YEAR_RANGES = {
    8: (2014, 2019),
    9: (2019, 2024),
    10: (2024, 2030),
}

AMENDMENTS_DB_PATH = DATA_DIR / "amendments_index.db"
_amendments_conn: Optional[sqlite3.Connection] = None
_amendments_lock = threading.Lock()


def _ensure_amendments_connection() -> Optional[sqlite3.Connection]:
    """Return a shared connection to the optional amendments index if available."""
    global _amendments_conn
    if not AMENDMENTS_DB_PATH.exists():
        return None
    if _amendments_conn is not None:
        return _amendments_conn
    with _amendments_lock:
        if _amendments_conn is None:
            conn = sqlite3.connect(str(AMENDMENTS_DB_PATH), check_same_thread=False)
            conn.row_factory = sqlite3.Row
            _amendments_conn = conn
    return _amendments_conn


def _parse_json_field(value: Optional[object]) -> Optional[List]:
    if value is None:
        return None
    if isinstance(value, (bytes, bytearray)):
        try:
            decoded = zlib.decompress(value).decode("utf-8")
        except Exception:
            decoded = value.decode("utf-8", errors="replace")
    else:
        text = str(value).strip()
        if not text:
            return None
        decoded = text
    try:
        parsed = json.loads(decoded)
        if isinstance(parsed, list):
            return parsed
        return [parsed]
    except json.JSONDecodeError:
        return [decoded]


def _parse_authors(value: Optional[str]) -> Optional[object]:
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    if text.startswith("[") or text.startswith("{"):
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return ", ".join(str(item) for item in parsed)
            return parsed
        except json.JSONDecodeError:
            return text
    return text


def _get_term_file(prefix: str, term: int) -> Path:
    return PARLTRACK_DIR / f"{prefix}_term{term}.json"


def _stream_first_available(paths: Iterable[Path]) -> None:
    for candidate in paths:
        try:
            iterator = stream_json_items(candidate)
            try:
                next(iterator)
            except StopIteration:
                pass
            return
        except FileNotFoundError:
            continue
    raise FileNotFoundError(
        "No dataset found for any of: " + ", ".join(str(path) for path in paths)
    )


def _normalize_mep_id(entry: object) -> Optional[str]:
    if entry is None:
        return None
    if isinstance(entry, dict):
        for key in ("mepid", "mepId", "UserID", "id"):
            if key in entry and entry[key] is not None:
                return str(entry[key])
        return None
    return str(entry)


def _matches_mep(meps: List[object], mep_id_str: str) -> bool:
    return any(_normalize_mep_id(entry) == mep_id_str for entry in meps)


def _extract_year(date_str: Optional[str]) -> Optional[int]:
    if not date_str:
        return None
    try:
        return int(date_str[:4])
    except (TypeError, ValueError):
        return None


def _find_mep_activities(mep_id: int, term: int) -> Optional[Dict]:
    mep_id_str = str(mep_id)
    candidates = (
        _get_term_file("ep_mep_activities", term),
        PARLTRACK_DIR / "ep_mep_activities.json",
    )
    for candidate in candidates:
        try:
            for record in stream_json_items(candidate):
                if str(record.get("mep_id")) == mep_id_str:
                    return record
        except FileNotFoundError:
            continue
    return None


def _iter_amendments_for_mep(mep_id: int, term: int) -> Iterator[Dict]:
    mep_id_str = str(mep_id)
    year_range = TERM_YEAR_RANGES.get(term, (0, 9999))
    candidates = (
        _get_term_file("ep_amendments", term),
        PARLTRACK_DIR / "ep_amendments.json",
    )
    for candidate in candidates:
        try:
            for amendment in stream_json_items(candidate):
                mep_list = amendment.get("meps") or []
                if _matches_mep(mep_list, mep_id_str):
                    if "_term" in candidate.name:
                        yield amendment
                    else:
                        year = _extract_year(amendment.get("date"))
                        if year and year_range[0] <= year <= year_range[1]:
                            yield amendment
            if "_term" in candidate.name:
                break
        except FileNotFoundError:
            continue


def _motion_sort_key(item: Dict) -> str:
    return item.get('Date opened') or item.get('date', '')


@app.route('/api/score', methods=['GET', 'POST'])
def get_scores():
    """Return term-wide scores computed from the SQLite database."""
    try:
        term = int(request.args.get('term', 10))
        results = scorer.score_all_meps(term)
        return jsonify({
            'success': True,
            'count': len(results),
            'data': results,
            'methodology': 'MEP Ranking (October 2017) with term-specific ranges'
        })
    except Exception as exc:  # pragma: no cover
        return jsonify({'success': False, 'error': str(exc)}), 500


@app.route('/api/mep/<int:mep_id>/category/<category>', methods=['GET'])
def get_mep_category_details(mep_id: int, category: str):
    """Return detailed activity entries for a MEP without caching huge datasets."""
    term = int(request.args.get('term', 10))
    offset = int(request.args.get('offset', 0))
    limit = int(request.args.get('limit', 15))

    if category == 'amendments':
        conn = _ensure_amendments_connection()
        if conn:
            cursor = conn.cursor()
            total_row = cursor.execute(
                """
                SELECT COUNT(*)
                FROM amendment_mep am
                JOIN amendments a ON a.id = am.amendment_id
                WHERE am.mep_id = ? AND a.term = ?
                """,
                (mep_id, term),
            ).fetchone()
            total = int(total_row[0]) if total_row else 0

            records = cursor.execute(
                """
                SELECT a.seq, a.date, a.reference, a.title, a.committee, a.location,
                       a.authors, a.new_json, a.old_json, a.src, a.dossiers
                FROM amendment_mep am
                JOIN amendments a ON a.id = am.amendment_id
                WHERE am.mep_id = ? AND a.term = ?
                ORDER BY a.date DESC, a.id DESC
                LIMIT ? OFFSET ?
                """,
                (mep_id, term, limit, offset),
            ).fetchall()

            data = []
            for row in records:
                data.append({
                    'seq': row['seq'],
                    'date': row['date'],
                    'reference': row['reference'],
                    'title': row['title'],
                    'committee': _parse_json_field(row['committee']),
                    'location': _parse_json_field(row['location']),
                    'authors': _parse_authors(row['authors']),
                    'new': _parse_json_field(row['new_json']),
                    'old': _parse_json_field(row['old_json']),
                    'src': row['src'],
                    'dossiers': _parse_json_field(row['dossiers']),
                })

            return jsonify({
                'success': True,
                'category': 'amendments',
                'mep_id': mep_id,
                'term': term,
                'total_count': total,
                'offset': offset,
                'limit': limit,
                'has_more': total > offset + limit,
                'data': data,
            })

        matches: List[Dict] = []
        total = 0
        for amendment in _iter_amendments_for_mep(mep_id, term):
            total += 1
            if total > offset and len(matches) < limit:
                matches.append(amendment)
        return jsonify({
            'success': True,
            'category': 'amendments',
            'mep_id': mep_id,
            'term': term,
            'total_count': total,
            'offset': offset,
            'limit': limit,
            'has_more': total > offset + len(matches),
            'data': matches
        })

    mep_data = _find_mep_activities(mep_id, term)
    if not mep_data:
        return jsonify({'success': False, 'error': 'MEP not found'}), 404

    if category == 'speeches':
        filtered = [
            item for item in mep_data.get('CRE', [])
            if 'Explanations of vote' not in item.get('title', '')
            and 'One-minute speeches' not in item.get('title', '')
            and item.get('term', 0) == term
        ]
        filtered.sort(key=lambda x: x.get('date', ''), reverse=True)

    elif category in {'questions', 'questions_written'}:
        filtered = [item for item in mep_data.get('WQ', []) if item.get('term', 0) == term]
        filtered.sort(key=lambda x: x.get('date', ''), reverse=True)

    elif category == 'questions_oral':
        filtered = [item for item in mep_data.get('OQ', []) if item.get('term', 0) == term]
        filtered.sort(key=lambda x: x.get('date', ''), reverse=True)

    elif category == 'motions':
        motions: List[Dict] = []
        for bucket in ('MOTION', 'IMOTION', 'WDECL'):
            motions.extend(mep_data.get(bucket, []))
        filtered = [item for item in motions if item.get('term', 0) == term]
        filtered.sort(key=_motion_sort_key, reverse=True)

    elif category == 'explanations':
        filtered = [
            item for item in mep_data.get('CRE', [])
            if 'Explanations of vote' in item.get('title', '') and item.get('term', 0) == term
        ]
        filtered.sort(key=lambda x: x.get('date', ''), reverse=True)

    else:
        key_map = {
            'reports_rapporteur': 'REPORT',
            'reports_shadow': 'REPORT-SHADOW',
            'opinions_rapporteur': 'COMPARL',
            'opinions_shadow': 'COMPARL-SHADOW',
        }
        bucket = key_map.get(category)
        if not bucket:
            return jsonify({'success': False, 'error': 'Unknown category'}), 400
        filtered = [item for item in mep_data.get(bucket, []) if item.get('term', 0) == term]
        filtered.sort(key=lambda x: x.get('date', ''), reverse=True)

    paginated = filtered[offset:offset + limit]
    return jsonify({
        'success': True,
        'category': category,
        'mep_id': mep_id,
        'term': term,
        'total_count': len(filtered),
        'offset': offset,
        'limit': limit,
        'has_more': len(filtered) > offset + len(paginated),
        'data': paginated
    })


@app.route('/api/health', methods=['GET'])
def health_check():
    """Ping endpoint used both by Render and by the Vercel frontend."""
    try:
        _stream_first_available((_get_term_file('ep_mep_activities', 10), PARLTRACK_DIR / 'ep_mep_activities.json'))
        _stream_first_available((_get_term_file('ep_amendments', 10), PARLTRACK_DIR / 'ep_amendments.json'))
        return jsonify({'success': True, 'status': 'ok'})
    except FileNotFoundError as exc:
        return jsonify({'success': False, 'status': 'error', 'error': str(exc)}), 500


if __name__ == '__main__':  # pragma: no cover
    app.run(debug=True, port=5001)
