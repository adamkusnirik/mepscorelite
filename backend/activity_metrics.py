#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import glob
import json
import lzma
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime

def load_dumps(path_pattern: str) -> List[Dict[str, Any]]:
    """
    Load MEP data dumps from files matching the provided pattern.
    
    Args:
        path_pattern: Glob pattern to match data dump files (e.g., 'data/raw/*.xz')
    
    Returns:
        A list of dictionaries, each containing a parsed data dump
    """
    dumps = []
    for file_path in glob.glob(path_pattern):
        with lzma.open(file_path, "rt", encoding="utf-8") as f:
            dump = json.load(f)
            dumps.append(dump)
    return dumps


def filter_active_meps(dump: Dict[str, Any], term_start: str, term_end: str) -> Dict[str, Any]:
    """
    Filter the MEP data dump to keep only active MEPs during the specified term.
    
    An MEP is considered active if their role status is either:
    - "end of mandate" (meaning they served during the term but are no longer in office)
    - blank/empty (meaning they are still in office)
    
    Args:
        dump: The MEP data dump dictionary
        term_start: Start date of the term (ISO format: YYYY-MM-DD)
        term_end: End date of the term (ISO format: YYYY-MM-DD)
    
    Returns:
        A filtered data dump containing only active MEPs
    """
    filtered_dump = {}
    for mep_id, mep_data in dump.items():
        if "roles" in mep_data:
            for role in mep_data["roles"]:
                # Keep if the role is still active (end is None) or ended at term_end
                if role.get("end") == term_end or role.get("end") is None:
                    if mep_id not in filtered_dump:
                        filtered_dump[mep_id] = mep_data
                    break
    
    return filtered_dump


def count_activities(dump: Dict[str, Any], term_start: str, term_end: str) -> Dict[str, Dict[str, int]]:
    """
    Count the activities of each MEP during the specified term.
    
    This follows the original logic from the first app, tallying activities
    such as reports, opinions, motions, etc.
    
    Args:
        dump: The MEP data dump dictionary
        term_start: Start date of the term (ISO format: YYYY-MM-DD)
        term_end: End date of the term (ISO format: YYYY-MM-DD)
    
    Returns:
        A dictionary mapping MEP IDs to their activity counts
    """
    # Convert term dates to datetime objects for comparison
    term_start_date = datetime.fromisoformat(term_start)
    term_end_date = datetime.fromisoformat(term_end)
    
    activity_counts = {}
    
    for mep_id, mep_data in dump.items():
        # Initialize activity counts for this MEP
        activity_counts[mep_id] = {
            "speeches": 0,
            "reports": 0,
            "amendments": 0
        }
        
        # Count speeches
        if "speeches" in mep_data:
            for speech in mep_data["speeches"]:
                if "date" in speech:
                    speech_date = datetime.fromisoformat(speech["date"])
                    if term_start_date <= speech_date <= term_end_date:
                        activity_counts[mep_id]["speeches"] += 1
        
        # Count reports
        if "reports" in mep_data:
            for report in mep_data["reports"]:
                if "date" in report:
                    report_date = datetime.fromisoformat(report["date"])
                    if term_start_date <= report_date <= term_end_date:
                        activity_counts[mep_id]["reports"] += 1
        
        # Count amendments
        if "amendments" in mep_data:
            for amendment in mep_data["amendments"]:
                if "date" in amendment:
                    amendment_date = datetime.fromisoformat(amendment["date"])
                    if term_start_date <= amendment_date <= term_end_date:
                        activity_counts[mep_id]["amendments"] += 1
    
    return activity_counts


def calculate_score(speeches, amendments, reports_rapporteur, reports_shadow):
    """Calculate activity score for an MEP based on their activities.
    
    Args:
        speeches (int): Number of speeches
        amendments (int): Number of amendments
        reports_rapporteur (int): Number of reports as rapporteur
        reports_shadow (int): Number of reports as shadow rapporteur
        
    Returns:
        float: Activity score
    """
    # Weights for different activities
    SPEECH_WEIGHT = 1.0
    AMENDMENT_WEIGHT = 1.0
    REPORT_RAPPORTEUR_WEIGHT = 10.0
    REPORT_SHADOW_WEIGHT = 5.0
    
    # Calculate weighted sum
    score = (
        speeches * SPEECH_WEIGHT +
        amendments * AMENDMENT_WEIGHT +
        reports_rapporteur * REPORT_RAPPORTEUR_WEIGHT +
        reports_shadow * REPORT_SHADOW_WEIGHT
    )
    
    return float(score)


def build_ranking(term: str, dump_dir: str = "data/raw") -> pd.DataFrame:
    """
    Build a ranking of MEPs based on their activities during the specified term.
    
    Args:
        term: The term identifier (e.g., '9' for the 9th European Parliament)
        dump_dir: Directory containing the data dumps
    
    Returns:
        A pandas DataFrame with MEP rankings
    """
    # Load the processed MEP data
    json_file = os.path.join(dump_dir, 'meps_data.json')
    if not os.path.exists(json_file):
        raise FileNotFoundError(f"MEP data file not found: {json_file}")
    
    with open(json_file, 'r', encoding='utf-8') as f:
        meps_data = json.load(f)
    
    # Build DataFrame
    rows = []
    for mep_id, mep_data in meps_data.items():
        # Count activities
        speeches = len(mep_data.get('speeches', []))
        amendments = len(mep_data.get('amendments', []))
        reports_rapporteur = len(mep_data.get('reports', []))
        reports_shadow = len(mep_data.get('shadow_reports', []))
        
        # Calculate score
        score = calculate_score(speeches, amendments, reports_rapporteur, reports_shadow)
        
        # Create MEP data dictionary
        row = {
            "mep_id": mep_id,
            "full_name": mep_data.get('name', 'Unknown'),
            "country": mep_data.get('country', 'Unknown'),
            "group": mep_data.get('party', 'Unknown'),
            "national_party": mep_data.get('national_party', ''),
            "speeches": speeches,
            "amendments": amendments,
            "reports_rapporteur": reports_rapporteur,
            "reports_shadow": reports_shadow,
            "score": score
        }
        
        rows.append(row)
    
    # Create DataFrame
    df = pd.DataFrame(rows)
    
    # Sort by score
    if not df.empty and "score" in df.columns:
        df = df.sort_values("score", ascending=False).reset_index(drop=True)
        df['rank'] = df.index + 1
    
    # Ensure the public/data directory exists
    os.makedirs('public/data', exist_ok=True)
    
    # Write the ranking to JSON
    output_file = os.path.join('public/data', f'term{term}_dataset.json')
    df.to_json(output_file, orient='records', indent=2)
    
    return df 