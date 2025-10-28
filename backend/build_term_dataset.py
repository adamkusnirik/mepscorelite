#!/usr/bin/env python3
"""
Build static JSON datasets for each EP term using data from the SQLite database.
Uses new 4-category methodology: Legislative Production, Control & Transparency, 
Engagement & Presence, and Institutional Roles.
Outputs files to public/data/ directory.
"""

import os
import json
import sqlite3
from pathlib import Path
import csv
import re
import xml.etree.ElementTree as ET
# from tqdm import tqdm - removed dependency
import logging, time
import zstandard as zstd
from mep_score_scorer import MEPScoreScorer

logging.basicConfig(
    format="%(asctime)s │ %(levelname)-8s │ %(message)s",
    level=logging.INFO,  # Changed to INFO by default
    datefmt="%H:%M:%S",
)

# Paths
DB = Path("data/meps.db")
OUTPUT_DIR = Path("public/data")
PUBLIC = Path("public/data")
PARLTRACK_DIR = Path("data/parltrack")

# Store MEP names/metadata by ID
NAME_BY_ID = {}

def standardize_group_name(group_name: str) -> str:
    """Standardize political group names to their common abbreviations"""
    group_mappings = {
        "Group of the European People's Party (Christian Democrats)": "EPP",
        "Group of the Progressive Alliance of Socialists and Democrats in the European Parliament": "S&D",
        "European Conservatives and Reformists Group": "ECR",
        "Group of the Alliance of Liberals and Democrats for Europe": "ALDE",
        "Renew Europe Group": "RE",
        "Group of the Greens/European Free Alliance": "Greens/EFA",
        "The Left group in the European Parliament - GUE/NGL": "GUE/NGL",
        "Confederal Group of the European United Left/Nordic Green Left": "GUE/NGL",
        "Europe of Freedom and Direct Democracy Group": "EFDD",
        "Identity and Democracy Group": "ID",
        "Europe of Nations and Freedom Group": "ENF",
        "Patriots for Europe Group": "PfE",
        "Europe of Sovereign Nations": "ESN",
        "Non-attached Members": "NI",
        "Unknown": "NI"
    }
    return group_mappings.get(group_name, group_name)

def load_mep_data():
    """Load MEP data from ParlTrack to get country information"""
    logging.info("Loading MEP data from ParlTrack")
    mep_file = PARLTRACK_DIR / "ep_meps.json.zst"
    
    try:
        with open(mep_file, 'rb') as fh:
            dctx = zstd.ZstdDecompressor()
            with dctx.stream_reader(fh) as reader:
                text = reader.read().decode('utf-8')
                meps_data = json.loads(text)
                logging.info(f"Loaded {len(meps_data)} MEP records")
                
                if not meps_data:
                    logging.error("No MEP data found in file")
                    return {}
                
                # Debug first record
                if meps_data:
                    logging.info(f"First record: {json.dumps(meps_data[0], indent=2)}")
                
        mep_info = {}
        for mep in meps_data:
            if not isinstance(mep, dict):
                logging.warning(f"Skipping non-dict MEP record: {type(mep)}")
                continue
                
            mep_id = mep.get("UserID")
            if not mep_id:
                logging.warning("Skipping MEP record without UserID")
                continue
                
            constituencies = mep.get("Constituencies", [])
            if not constituencies:
                country = "Unknown"
                logging.debug(f"No constituencies for MEP {mep_id}")
            else:
                # Get most recent constituency
                try:
                    current_constituency = sorted(
                        [c for c in constituencies if isinstance(c, dict)],
                        key=lambda x: x.get("end", "9999"),
                        reverse=True
                    )[0]
                    country = current_constituency.get("country", "Unknown")
                except (IndexError, KeyError) as e:
                    logging.warning(f"Error getting constituency for MEP {mep_id}: {e}")
                    country = "Unknown"
            
            # Get current group info
            groups = mep.get("Groups", [])
            if not groups:
                party_group = "Unknown"
                logging.debug(f"No groups for MEP {mep_id}")
            else:
                try:
                    # Get most recent group
                    current_group = sorted(
                        [g for g in groups if isinstance(g, dict)],
                        key=lambda x: x.get("end", "9999"),
                        reverse=True
                    )[0]
                    party_group = current_group.get("Organization", "Unknown")
                    party_group = standardize_group_name(party_group)
                except (IndexError, KeyError) as e:
                    logging.warning(f"Error getting group for MEP {mep_id}: {e}")
                    party_group = "NI"
            
            name = mep.get("Name", {})
            full_name = name.get("full", "Unknown")
            
            mep_info[mep_id] = {
                "Name": full_name,
                "Country": country,
                "Groups": [{"Organization": party_group}]
            }
            
        logging.info(f"Processed {len(mep_info)} MEP records successfully")
        return mep_info
    except Exception as e:
        logging.error(f"Error loading MEP data: {e}")
        import traceback
        logging.error(traceback.format_exc())
        return {}

def load_official_ids(term: int) -> set[int]:
    """
    Load official MEP IDs from the term list XML files.
    
    Args:
        term: The parliamentary term (integer: 8, 9, or 10)
    
    Returns:
        A set of MEP IDs listed in the official term list
    """
    logging.info(f"Loading official IDs for term {term}")
    xml_path = Path("data/term_list") / f"{term}th term_raw.csv"
    
    try:
        # Parse XML directly
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # Extract all MEP elements
        meps = root.findall('.//mep')
        
        # Load MEP data from ParlTrack
        mep_info = load_mep_data()
        
        # Build set of IDs and metadata
        ids = set()
        for i, mep in enumerate(meps):
            try:
                mep_id = int(mep.find('id').text)
                
                # Use ParlTrack data if available, otherwise use XML data
                if mep_id in mep_info:
                    NAME_BY_ID[mep_id] = mep_info[mep_id]
                else:
                    full_name = mep.find('fullName').text
                    NAME_BY_ID[mep_id] = {
                        "Name": full_name,
                        "Country": "Unknown",
                        "Groups": [{"Organization": "Unknown"}]
                    }
                
                ids.add(mep_id)
            except (AttributeError, ValueError) as e:
                logging.warning(f"Error processing MEP element: {e}")
                continue
        
        expected = {8: 860, 9: 875, 10: 719}[term]
        if len(ids) != expected:
            logging.warning(f"Term {term}: expected {expected} IDs but found {len(ids)}")
        
        return ids
        
    except ET.ParseError as e:
        logging.error(f"XML parsing error in {xml_path}: {e}")
        return set()
    except Exception as e:
        logging.error(f"Error processing {xml_path}: {e}")
        return set()

def fetch_data(cur, table: str, term: int, ids: set[int]) -> dict:
    """Helper function to fetch data with progress bar"""
    logging.info(f"Fetching {table} data for term {term}")
    q_ids = ",".join("?"*len(ids))
    
    # First count total rows
    cur.execute(f"SELECT COUNT(*) FROM {table} WHERE term=? AND mep_id IN ({q_ids})",
               (term, *ids))
    total = cur.fetchone()[0]
    
    # Then fetch with progress bar
    cur.execute(f"SELECT * FROM {table} WHERE term=? AND mep_id IN ({q_ids})",
               (term, *ids))
    
    result = {}
    for i, row in enumerate(map(dict, cur)):
        result[row["mep_id"]] = row
        if i % 100 == 0:
            logging.info(f"Loading {table}: {i}/{total}")
            
    return result

def build(term: int):
    """Build a static JSON dataset for a specific EP term."""
    start_time = time.time()
    logging.info(f"Building dataset for term {term}")
    
    # Load official MEP IDs for this term
    ids = load_official_ids(term)
    if not ids:
        logging.error(f"No official IDs found for term {term}")
        return
    
    # Get data from database
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.row_factory = sqlite3.Row
    
    # Get MEP basic info including current_party
    c.execute("""
        SELECT mep_id, current_party FROM meps WHERE mep_id IN ({})
    """.format(','.join('?' * len(ids))), list(ids))
    mep_parties = {row["mep_id"]: row["current_party"] for row in c.fetchall()}
    
    # Get activities
    c.execute("""
        SELECT * FROM activities WHERE term = ?
    """, (term,))
    acts_by_id = {row["mep_id"]: dict(row) for row in c.fetchall()}
    
    # Get roles
    c.execute("""
        SELECT mep_id,
            COUNT(*) FILTER (WHERE role = 'Chair' AND role_type = 'committee') as committee_chair,
            COUNT(*) FILTER (WHERE role = 'Vice-Chair' AND role_type = 'committee') as committee_vice_chair,
            COUNT(*) FILTER (WHERE role = 'Member' AND role_type = 'committee') as committee_member,
            COUNT(*) FILTER (WHERE role = 'Substitute' AND role_type = 'committee') as committee_substitute,
            COUNT(*) FILTER (WHERE role = 'Chair' AND role_type = 'delegation') as delegation_chair,
            COUNT(*) FILTER (WHERE role = 'Vice-Chair' AND role_type = 'delegation') as delegation_vice_chair,
            COUNT(*) FILTER (WHERE role = 'Member' AND role_type = 'delegation') as delegation_member,
            COUNT(*) FILTER (WHERE role = 'Substitute' AND role_type = 'delegation') as delegation_substitute,
            COUNT(*) FILTER (WHERE role = 'President' AND role_type = 'ep') as ep_president,
            COUNT(*) FILTER (WHERE role = 'Vice-President' AND role_type = 'ep') as ep_vice_president,
            COUNT(*) FILTER (WHERE role = 'Quaestor' AND role_type = 'ep') as ep_quaestor
        FROM roles 
        WHERE term = ?
        GROUP BY mep_id
    """, (term,))
    roles_by_id = {row["mep_id"]: dict(row) for row in c.fetchall()}
    
    # Get votes attendance data
    c.execute("""
        SELECT mep_id, votes_attended
        FROM mep_vote_summary
        WHERE term = ?
    """, (term,))
    votes_by_id = {row["mep_id"]: row["votes_attended"] for row in c.fetchall()}
    
    # Get detailed roles for each MEP
    logging.info(f"Fetching detailed roles for term {term}")
    c.execute("""
        SELECT mep_id, role_type, organization, organization_abbr, role, start_date, end_date
        FROM roles 
        WHERE term = ?
        ORDER BY mep_id, role_type, organization
    """, (term,))
    
    detailed_roles_by_id = {}
    for row in c.fetchall():
        mep_id = row['mep_id']
        if mep_id not in detailed_roles_by_id:
            detailed_roles_by_id[mep_id] = []
        
        detailed_roles_by_id[mep_id].append({
            'type': row['role_type'],
            'name': row['organization'],
            'acronym': row['organization_abbr'],
            'role': row['role'],
            'start_date': row['start_date'],
            'end_date': row['end_date']
        })

    # Get MEP scores using the new 4-category methodology
    logging.info(f"Calculating MEP scores using 4-category methodology for term {term}")
    scorer = MEPScoreScorer()
    mep_scores = scorer.score_all_meps(term)
    scores_by_id = {score['mep_id']: score for score in mep_scores}
    
    # Data validation: Check for score calculation issues
    logging.info(f"Validating score calculations for {len(mep_scores)} MEPs")
    zero_score_count = 0
    high_score_count = 0
    
    for score in mep_scores:
        if score['final_score'] == 0:
            zero_score_count += 1
            if zero_score_count <= 5:  # Only log first 5 to avoid spam
                logging.warning(f"Zero score: {score['full_name']} - "
                              f"legislative_production: {score.get('legislative_production_score', 0)}, "
                              f"control_transparency: {score.get('control_transparency_score', 0)}, "
                              f"engagement_presence: {score.get('engagement_presence_score', 0)}")
        
        if score['final_score'] > 100:  # Unusually high scores
            high_score_count += 1
            if high_score_count <= 5:
                logging.warning(f"High score: {score['full_name']} - {score['final_score']:.1f}")
    
    logging.info(f"Score validation: {zero_score_count} zero scores, {high_score_count} high scores (>100)")
    
    # Build full dataset
    full = []
    missing = []
    missing_meta = []
    
    for i, mep_id in enumerate(sorted(ids)):
        if i % 100 == 0:
            logging.info(f"Building dataset: {i}/{len(ids)}")
        meta = NAME_BY_ID.get(mep_id, {})          # always present
        acts = acts_by_id.get(mep_id, {})
        roles = roles_by_id.get(mep_id, {})
        votes_attended = votes_by_id.get(mep_id, 0)

        # MUST have meta – otherwise something went wrong during ingest
        if not meta:
            missing_meta.append(mep_id)
            continue          # skip rows with no real metadata

        if not acts and not roles:
            missing.append(mep_id)                 # track for log

        # Get MEP Ranking score data
        score_data = scores_by_id.get(mep_id, {})
        
        full.append({
            "mep_id": mep_id,
            "full_name": meta["Name"],
            "country": meta["Country"],
            "group": meta["Groups"][-1]["Organization"],
            "national_party": mep_parties.get(mep_id, "Unknown"),
            # activities (fallback to 0)
            "speeches": acts.get("speeches", 0),
            "amendments": acts.get("amendments", 0),
            "reports_rapporteur": acts.get("reports_rapporteur", 0),
            "reports_shadow": acts.get("reports_shadow", 0),
            "questions": acts.get("questions_written", 0) + acts.get("questions_oral", 0) + acts.get("questions_major", 0),
            "questions_written": acts.get("questions_written", 0),
            "questions_oral": acts.get("questions_oral", 0),
            "motions": acts.get("motions", 0),
            "opinions_rapporteur": acts.get("opinions_rapporteur", 0),
            "opinions_shadow": acts.get("opinions_shadow", 0),
            "explanations": acts.get("explanations", 0),
            "votes_attended": votes_attended,
            "votes_total": score_data.get("votes_total", 0),
            # committee roles
            "committee_chair": roles.get("committee_chair", 0),
            "committee_vice_chair": roles.get("committee_vice_chair", 0),
            "committee_member": roles.get("committee_member", 0),
            "committee_substitute": roles.get("committee_substitute", 0),
            # delegation roles
            "delegation_chair": roles.get("delegation_chair", 0),
            "delegation_vice_chair": roles.get("delegation_vice_chair", 0),
            "delegation_member": roles.get("delegation_member", 0),
            "delegation_substitute": roles.get("delegation_substitute", 0),
            # EP leadership roles
            "ep_president": roles.get("ep_president", 0),
            "ep_vice_president": roles.get("ep_vice_president", 0),
            "ep_quaestor": roles.get("ep_quaestor", 0),
            # New 4-category methodology scores
            "final_score": score_data.get("final_score", 0),
            "legislative_production_score": score_data.get("legislative_production_score", 0),
            "control_transparency_score": score_data.get("control_transparency_score", 0),
            "engagement_presence_score": score_data.get("engagement_presence_score", 0),
            "institutional_roles_multiplier": score_data.get("institutional_roles_multiplier", 1.0),
            # Legacy compatibility scores
            "reports_score": score_data.get("reports_score", 0),
            "amendments_score": score_data.get("amendments_score", 0),
            "statements_score": score_data.get("control_transparency_score", 0),  # Map to control_transparency for backward compatibility
            "base_score": score_data.get("base_score", 0),
            "roles_multiplier": score_data.get("roles_multiplier", 1.0),
            "score_with_roles": score_data.get("score_with_roles", 0),
            "attendance_penalty": score_data.get("attendance_penalty", 1.0),
            "attendance_rate": score_data.get("attendance_rate", 0),
            # Individual report scores for breakdown
            "reports_rapporteur_score": score_data.get("reports_rapporteur_score", 0),
            "reports_shadow_score": score_data.get("reports_shadow_score", 0),
            "opinions_rapporteur_score": score_data.get("opinions_rapporteur_score", 0),
            "opinions_shadow_score": score_data.get("opinions_shadow_score", 0),
            # Individual statement scores for breakdown
            "speeches_score": score_data.get("speeches_score", 0),
            "explanations_score": score_data.get("explanations_score", 0),
            "oral_questions_score": score_data.get("oral_questions_score", 0),
            "written_questions_score": score_data.get("written_questions_score", 0),
            # Role information for breakdown
            "top_role": score_data.get("top_role", ""),
            "roles_percentage": score_data.get("roles_percentage", 0),
            # Detailed role information for profile pages
            "detailed_roles": detailed_roles_by_id.get(mep_id, []),
            # Backward compatibility
            "score": score_data.get("final_score", 0),
            "rank": score_data.get("rank", 0),
        })

    assert len(full) == len(ids) - len(missing_meta), "Left‑join lost rows!"
    logging.info(f"Term {term}: built {len(full)} rows "
                f"({len(missing)} had no activity/role rows, {len(missing_meta)} missing meta)")

    # ---- final ranking pass (covers MEPs with final_score==0) ----
    logging.info(f"Sorting and ranking MEPs for term {term}")
    full.sort(
        key=lambda r: (
            -r["final_score"],           # high final_score first
            -r.get("speeches", 0),       # tie-break by speeches
            r["full_name"].lower()       # then alphabetical
        )
    )
    for i, row in enumerate(full, 1):
        row["rank"] = i
        # Update backward compatibility score field
        row["score"] = row["final_score"]

    # Calculate averages for profile page
    logging.info(f"Calculating averages for term {term}")
    
    # Calculate EP-wide averages
    ep_averages = {}
    activity_fields = ['speeches', 'amendments', 'reports_rapporteur', 'reports_shadow', 
                      'questions', 'questions_written', 'questions_oral', 'motions', 'opinions_rapporteur', 'opinions_shadow', 
                      'explanations', 'votes_attended', 'attendance_rate']
    
    for field in activity_fields:
        values = [row[field] for row in full if row[field] is not None]
        ep_averages[field] = sum(values) / len(values) if values else 0
    
    # Calculate averages by group
    group_averages = {}
    for row in full:
        group = row['group']
        if group not in group_averages:
            group_averages[group] = {field: [] for field in activity_fields}
        
        for field in activity_fields:
            if row[field] is not None:
                group_averages[group][field].append(row[field])
    
    # Convert group lists to averages
    for group in group_averages:
        for field in activity_fields:
            values = group_averages[group][field]
            group_averages[group][field] = sum(values) / len(values) if values else 0
    
    # Calculate averages by country
    country_averages = {}
    for row in full:
        country = row['country']
        if country not in country_averages:
            country_averages[country] = {field: [] for field in activity_fields}
        
        for field in activity_fields:
            if row[field] is not None:
                country_averages[country][field].append(row[field])
    
    # Convert country lists to averages
    for country in country_averages:
        for field in activity_fields:
            values = country_averages[country][field]
            country_averages[country][field] = sum(values) / len(values) if values else 0
    
    # Create the final dataset structure expected by profile page
    dataset = {
        "meps": full,
        "averages": {
            "ep": ep_averages,
            "groups": group_averages,
            "countries": country_averages
        }
    }

    logging.info(f"Writing JSON output for term {term}")
    output_path = PUBLIC / f"term{term}_dataset.json"
    output_path.write_text(
        json.dumps(dataset, ensure_ascii=False, indent=2), "utf‑8")
    
    if missing_meta:
        logging.warning(f"WARNING: {len(missing_meta)} ids had no meta – fix ingest first")
    
    elapsed = time.time() - start_time
    logging.info(f"Term {term} dataset complete in {elapsed:.2f} seconds")

def main():
    """Build datasets for all terms."""
    logging.info("Starting dataset generation")
    
    # Build datasets for all terms
    for term in (8, 9, 10):
        build(term)
    
    logging.info(f"All term datasets created successfully!")

if __name__ == "__main__":
    main() 
