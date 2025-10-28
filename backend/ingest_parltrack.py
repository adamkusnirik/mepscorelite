#!/usr/bin/env python3
"""
Ingest Parltrack data into SQLite database for MEP ranking analysis.
Creates tables for MEPs, activities, roles, and rankings in a SQLite database.
"""

import json
import sqlite3
import re
import datetime as dt
from pathlib import Path
import os

from file_utils import load_combined_dataset, load_json_auto
from vote_summary import Config as VoteSummaryConfig, VoteSummaryError, update_vote_summary

RAW = Path("data/parltrack")
DB = Path("data/meps.db")
PARLTRACK_BACKUP = Path("data/parltrack backup")
ACTIVITIES_8_TERM_FILE = Path("data/parltrack/8th term/ep_mep_activities-2019-07-03.json")
ACTIVITIES_9_TERM_FILE = Path("data/parltrack/9th term/ep_mep_activities-2024-07-02.json")

if not os.path.exists(os.path.dirname(DB)):
    os.makedirs(os.path.dirname(DB))

# Connect to SQLite database
conn = sqlite3.connect(DB)
c = conn.cursor()

# Create tables if they don't exist
c.execute('''
CREATE TABLE IF NOT EXISTS meps (
    mep_id INTEGER PRIMARY KEY,
    full_name TEXT,
    surname TEXT,
    family_name TEXT,
    gender TEXT,
    birth_date TEXT,
    birth_place TEXT,
    death_date TEXT,
    country TEXT,
    current_party TEXT,
    current_party_group TEXT,
    current_party_group_id TEXT,
    photo_url TEXT,
    twitter_url TEXT,
    facebook_url TEXT,
    instagram_url TEXT,
    homepage_url TEXT,
    email TEXT,
    brussels_office TEXT,
    brussels_phone TEXT,
    strasbourg_office TEXT,
    strasbourg_phone TEXT,
    cv_summary TEXT
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mep_id INTEGER,
    term INTEGER,
    speeches INTEGER DEFAULT 0,
    reports_rapporteur INTEGER DEFAULT 0,
    reports_shadow INTEGER DEFAULT 0,
    amendments INTEGER DEFAULT 0,
    questions_written INTEGER DEFAULT 0,
    questions_oral INTEGER DEFAULT 0,
    questions_major INTEGER DEFAULT 0,
    motions INTEGER DEFAULT 0,
    motions_individual INTEGER DEFAULT 0,
    opinions_rapporteur INTEGER DEFAULT 0,
    opinions_shadow INTEGER DEFAULT 0,
    declarations INTEGER DEFAULT 0,
    explanations INTEGER DEFAULT 0,
    FOREIGN KEY (mep_id) REFERENCES meps(mep_id)
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mep_id INTEGER,
    term INTEGER,
    role_type TEXT,           -- 'committee', 'delegation', 'staff', or 'ep'
    organization TEXT,        -- Full name of committee/delegation/etc
    organization_abbr TEXT,   -- Abbreviation (e.g. BUDG, AFET)
    role TEXT,               -- Member, Chair, Vice-Chair, etc
    start_date TEXT,
    end_date TEXT,
    FOREIGN KEY (mep_id) REFERENCES meps(mep_id)
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS rankings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mep_id INTEGER,
    term INTEGER,
    total_score REAL,
    FOREIGN KEY (mep_id) REFERENCES meps(mep_id),
    UNIQUE(mep_id, term)
)
''')

def get_term_for_date(date_str):
    """Determine EP term based on date."""
    try:
        date = dt.datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        
        if dt.datetime(2009, 7, 14) <= date < dt.datetime(2014, 7, 1):
            return 7
        elif dt.datetime(2014, 7, 1) <= date < dt.datetime(2019, 7, 2):
            return 8
        elif dt.datetime(2019, 7, 2) <= date < dt.datetime(2024, 7, 16):
            return 9
        elif dt.datetime(2024, 7, 16) <= date:
            return 10
    except Exception:
        pass
    
    return None

def populate_meps_table():
    """Populate the meps table with detailed MEP information."""
    print("Populating MEPs table...")
    
    # Load MEP data
    meps_data = load_json_auto(RAW/"ep_meps.json.zst")
    if not meps_data:
        print("Failed to load MEP data")
        return
    
    # Clear existing data
    c.execute("DELETE FROM meps")
    
    # Process each MEP
    for mep in meps_data:
        try:
            # Basic info
            mep_id = mep["UserID"]
            
            # Name components
            name = mep.get("Name", {})
            full_name = name.get("full", "Unknown")
            surname = name.get("sur")
            family_name = name.get("family")
            
            # Personal info
            gender = mep.get("Gender")
            birth = mep.get("Birth", {})
            birth_date = birth.get("date")
            birth_place = birth.get("place")
            death_date = mep.get("Death")
            
            # Get current constituency info
            constituencies = mep.get("Constituencies", [])
            current_constituency = sorted(constituencies, key=lambda x: x.get("end", "9999"), reverse=True)[0] if constituencies else {}
            country = current_constituency.get("country")
            current_party = current_constituency.get("party")
            
            # Get current group info
            groups = mep.get("Groups", [])
            current_group = sorted(groups, key=lambda x: x.get("end", "9999"), reverse=True)[0] if groups else {}
            current_party_group = current_group.get("Organization")
            current_party_group_id = current_group.get("groupid")
            
            # URLs and contact info
            photo_url = mep.get("Photo")
            twitter_urls = mep.get("Twitter", [])
            twitter_url = twitter_urls[0] if twitter_urls else None
            facebook_urls = mep.get("Facebook", [])
            facebook_url = facebook_urls[0] if facebook_urls else None
            instagram_urls = mep.get("Instagram", [])
            instagram_url = instagram_urls[0] if instagram_urls else None
            homepage_urls = mep.get("Homepage", [])
            homepage_url = homepage_urls[0] if homepage_urls else None
            
            # Email
            emails = mep.get("Mail", [])
            email = emails[0] if emails else None
            
            # Office info
            addresses = mep.get("Addresses", {})
            brussels = addresses.get("Brussels", {})
            brussels_addr = brussels.get("Address", {})
            brussels_office = brussels_addr.get("Office")
            brussels_phone = brussels.get("Phone")
            
            strasbourg = addresses.get("Strasbourg", {})
            strasbourg_addr = strasbourg.get("Address", {})
            strasbourg_office = strasbourg_addr.get("Office")
            strasbourg_phone = strasbourg.get("Phone")
            
            # CV summary (first few entries)
            cv_entries = mep.get("CV", [])
            cv_summary = "; ".join(cv_entries[:3]) if isinstance(cv_entries, list) else None
            
            # Insert into database
            c.execute("""
                INSERT INTO meps (
                    mep_id, full_name, surname, family_name, gender,
                    birth_date, birth_place, death_date,
                    country, current_party, current_party_group, current_party_group_id,
                    photo_url, twitter_url, facebook_url, instagram_url, homepage_url,
                    email, brussels_office, brussels_phone,
                    strasbourg_office, strasbourg_phone, cv_summary
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                mep_id, full_name, surname, family_name, gender,
                birth_date, birth_place, death_date,
                country, current_party, current_party_group, current_party_group_id,
                photo_url, twitter_url, facebook_url, instagram_url, homepage_url,
                email, brussels_office, brussels_phone,
                strasbourg_office, strasbourg_phone, cv_summary
            ))
            
        except Exception as e:
            print(f"Error processing MEP {mep.get('UserID', 'unknown')}: {e}")
            continue
    
    conn.commit()
    print(f"Added {c.execute('SELECT COUNT(*) FROM meps').fetchone()[0]} MEPs to the database")

def count_amendments_activity():
    """Process amendments data to count amendments per MEP per term."""
    print("Processing amendments data...")
    activity_counts = {}  # (mep_id, term) -> {"amendments": count}
    
    amendments_data = load_combined_dataset(
        RAW / "ep_amendments.json",
        [RAW / f"ep_amendments_term{term}.json" for term in (8, 9, 10)],
    )
    if not amendments_data:
        print("No amendments data available")
        return activity_counts
    
    print(f"Processing {len(amendments_data)} amendments...")
    processed_amendment_count = 0

    for i, amendment in enumerate(amendments_data):
        try:
            # Use the 'date' field for term
            date_str = amendment.get("date")
            if not date_str:
                # if i < 100: print(f"Skipping amendment (no date): {amendment.get('id')}")
                continue
            
            term = get_term_for_date(date_str)
            if not term:
                # if i < 100: print(f"Skipping amendment (no term for date {date_str}): {amendment.get('id')}")
                continue

            # Iterate through MEPs listed in the 'meps' field
            mep_ids_in_amendment = amendment.get("meps")
            if not mep_ids_in_amendment or not isinstance(mep_ids_in_amendment, list):
                # if i < 100: print(f"Skipping amendment (no mep_ids list): {amendment.get('id')}")
                continue

            for mep_id in mep_ids_in_amendment:
                if not isinstance(mep_id, int): # MEP IDs are integers
                    # if i < 100: print(f"Skipping invalid mep_id {mep_id} in amendment {amendment.get('id')}")
                    continue

                key = (mep_id, term)
                if key not in activity_counts:
                    activity_counts[key] = {"amendments": 0}
                activity_counts[key]["amendments"] += 1
                processed_amendment_count +=1

                if processed_amendment_count == 1: # Debug for the very first successfully processed amendment
                    print(f"DEBUG: First amendment counted for MEP {mep_id} in term {term}. Amendment ID: {amendment.get('id')}")
            
        except Exception as e:
            # print(f"Error processing amendment {amendment.get('id', 'Unknown ID')} at index {i}: {e}")
            continue
    
    if processed_amendment_count == 0:
        print("DEBUG: No amendments were successfully processed and counted for any MEP.")
    else:
        print(f"DEBUG: Successfully processed and counted {processed_amendment_count} amendment instances for MEPs across terms.")
        print(f"DEBUG: Total unique (MEP, term) entries with amendments: {len(activity_counts)}")
        # Print sample
        for i, ((mep_id, term), counts) in enumerate(activity_counts.items()):
            if i < 5: # Print first 5 samples
                print(f"DEBUG Sample: MEP {mep_id}, Term {term}, Amendments: {counts['amendments']}")
            else:
                break
    return activity_counts

def count_reports_activity():
    """Process votes data to count reports (rapporteur and shadow) per MEP per term."""
    print("Processing votes data for reports...")
    activity_counts = {}  # (mep_id, term) -> {"reports_rapporteur": count, "reports_shadow": count}
    
    # Load votes data
    votes_data = load_json_auto(RAW/"ep_votes.json.zst")
    if not votes_data:
        print("No votes data available")
        return activity_counts
    
    print(f"Processing {len(votes_data)} votes...")
    
    # Process votes
    for vote in votes_data:
        try:
            if not isinstance(vote, dict):
                continue
            
            # Get the term based on date
            term = None
            if "date" in vote:
                term = get_term_for_date(vote["date"])
            
            if not term:
                continue
            
            # Process rapporteurs
            for rapporteur in vote.get("rapporteur", []):
                if not isinstance(rapporteur, dict):
                    continue
                
                mep_id = rapporteur.get("UserID")
                if not mep_id:
                    continue
                
                key = (mep_id, term)
                if key not in activity_counts:
                    activity_counts[key] = {"reports_rapporteur": 0, "reports_shadow": 0}
                activity_counts[key]["reports_rapporteur"] += 1
            
            # Process shadow rapporteurs
            for shadow in vote.get("shadows", []):
                if not isinstance(shadow, dict):
                    continue
                
                mep_id = shadow.get("UserID")
                if not mep_id:
                    continue
                
                key = (mep_id, term)
                if key not in activity_counts:
                    activity_counts[key] = {"reports_rapporteur": 0, "reports_shadow": 0}
                activity_counts[key]["reports_shadow"] += 1
        
        except Exception as e:
            print(f"Error processing vote: {e}")
            continue
    
    return activity_counts

def process_mep_activities(mep_activities):
    """Process activities from the ep_mep_activities dataset structure."""
    activity_counts = {}  # (mep_id, term) -> activity counts
    
    if not isinstance(mep_activities, dict):
        return activity_counts
    
    mep_id = mep_activities.get("mep_id")
    if not mep_id:
        return activity_counts
    
    def init_counts(key):
        """Initialize activity counts for a key if not present."""
        if key not in activity_counts:
            activity_counts[key] = {
                "speeches": 0,
                "reports_rapporteur": 0,
                "reports_shadow": 0,
                "amendments": 0,
                "questions_written": 0,
                "questions_oral": 0,
                "questions_major": 0,
                "motions": 0,
                "motions_individual": 0,
                "opinions_rapporteur": 0,
                "opinions_shadow": 0,
                "declarations": 0,
                "explanations": 0
            }
    
    # Process CRE (speeches)
    for speech in mep_activities.get("CRE", []):
        term = speech.get("term")
        if not term:
            continue
        key = (mep_id, term)
        init_counts(key)
        activity_counts[key]["speeches"] += 1
    
    # Process REPORT and REPORT-SHADOW
    for report in mep_activities.get("REPORT", []):
        term = report.get("term")
        if not term:
            continue
        key = (mep_id, term)
        init_counts(key)
        activity_counts[key]["reports_rapporteur"] += 1
    
    for shadow in mep_activities.get("REPORT-SHADOW", []):
        term = shadow.get("term")
        if not term:
            continue
        key = (mep_id, term)
        init_counts(key)
        activity_counts[key]["reports_shadow"] += 1
    
    # Process COMPARL and COMPARL-SHADOW (opinions)
    for opinion in mep_activities.get("COMPARL", []):
        term = opinion.get("term")
        if not term:
            continue
        key = (mep_id, term)
        init_counts(key)
        activity_counts[key]["opinions_rapporteur"] += 1
    
    for shadow_opinion in mep_activities.get("COMPARL-SHADOW", []):
        term = shadow_opinion.get("term")
        if not term:
            continue
        key = (mep_id, term)
        init_counts(key)
        activity_counts[key]["opinions_shadow"] += 1
    
    # Process written questions (WQ)
    for question in mep_activities.get("WQ", []):
        term = question.get("term")
        if not term:
            continue
        key = (mep_id, term)
        init_counts(key)
        activity_counts[key]["questions_written"] += 1
    
    # Process oral questions (OQ)
    for question in mep_activities.get("OQ", []):
        term = question.get("term")
        if not term:
            continue
        key = (mep_id, term)
        init_counts(key)
        activity_counts[key]["questions_oral"] += 1
    
    # Process major interpellations (MINT)
    for question in mep_activities.get("MINT", []):
        term = question.get("term")
        if not term:
            continue
        key = (mep_id, term)
        init_counts(key)
        activity_counts[key]["questions_major"] += 1
    
    # Process motions (MOTION)
    for motion in mep_activities.get("MOTION", []):
        term = motion.get("term")
        if not term:
            continue
        key = (mep_id, term)
        init_counts(key)
        activity_counts[key]["motions"] += 1
    
    # Process individual motions (IMOTION)
    for motion in mep_activities.get("IMOTION", []):
        term = motion.get("term")
        if not term:
            continue
        key = (mep_id, term)
        init_counts(key)
        activity_counts[key]["motions_individual"] += 1
    
    # Process written declarations (WDECL)
    for decl in mep_activities.get("WDECL", []):
        term = decl.get("term")
        if not term:
            continue
        key = (mep_id, term)
        init_counts(key)
        activity_counts[key]["declarations"] += 1
    
    # Process written explanations (WEXP)
    for exp in mep_activities.get("WEXP", []):
        term = exp.get("term")
        if not term:
            continue
        key = (mep_id, term)
        init_counts(key)
        activity_counts[key]["explanations"] += 1
    
    return activity_counts

def count_other_activities():
    """Process other activities (speeches, questions, motions, opinions) per MEP per term."""
    print("Processing other activities...")
    activity_counts = {}  # (mep_id, term) -> activity counts
    
    # Load MEP activities data
    activities_data_10_source = load_json_auto(RAW/"ep_mep_activities.json")
    activities_data_8_source = load_json_auto(ACTIVITIES_8_TERM_FILE)
    activities_data_9_source = load_json_auto(ACTIVITIES_9_TERM_FILE)

    # Start with the definitive data for terms 8 and 9 from backup files.
    all_mep_activities = []
    if activities_data_8_source:
        all_mep_activities.extend(activities_data_8_source)
    if activities_data_9_source:
        all_mep_activities.extend(activities_data_9_source)

    # Process the live data, but only extract term 10 activities to avoid overwriting the correct 8/9 data.
    if activities_data_10_source:
        term10_mep_activities = []
        for mep_activity_bundle in activities_data_10_source:
            term10_mep_bundle = {'mep_id': mep_activity_bundle.get('mep_id')}
            has_term10_activity = False

            for activity_type, activities in mep_activity_bundle.items():
                if activity_type == 'mep_id' or not isinstance(activities, list):
                    continue
                
                term10_filtered_activities = [
                    activity for activity in activities 
                    if isinstance(activity, dict) and activity.get('term') == 10
                ]
                
                if term10_filtered_activities:
                    term10_mep_bundle[activity_type] = term10_filtered_activities
                    has_term10_activity = True
            
            if has_term10_activity:
                term10_mep_activities.append(term10_mep_bundle)
        
        all_mep_activities.extend(term10_mep_activities)

    if not all_mep_activities:
        print("No MEP activities data available")
        return activity_counts
    
    print(f"Processing activities for {len(all_mep_activities)} MEPs...")
    
    # Process each MEP's activities
    for mep_activities in all_mep_activities:
        try:
            mep_counts = process_mep_activities(mep_activities)
            activity_counts.update(mep_counts)
        except Exception as e:
            print(f"Error processing MEP activities: {e}")
            continue
    
    return activity_counts

def merge_activity_counts(*counts_list):
    """Merge multiple activity count dictionaries."""
    merged = {}
    for counts in counts_list:
        for key, activities in counts.items():
            if key not in merged:
                merged[key] = {
                    "speeches": 0,
                    "reports_rapporteur": 0,
                    "reports_shadow": 0,
                    "amendments": 0,
                    "questions_written": 0,
                    "questions_oral": 0,
                    "questions_major": 0,
                    "motions": 0,
                    "motions_individual": 0,
                    "opinions_rapporteur": 0,
                    "opinions_shadow": 0,
                    "declarations": 0,
                    "explanations": 0
                }
            for activity_type, count in activities.items():
                if activity_type in merged[key]:
                    merged[key][activity_type] += count
    return merged

def populate_activities_table():
    """Populate the activities table with aggregated counts from various sources."""
    print("Populating activities table...")
    
    # Count activities from different sources
    amendments_counts = count_amendments_activity()
    reports_counts = count_reports_activity()
    other_activities_counts = count_other_activities()
    
    # Merge all activity counts
    # Ensure merge_activity_counts can handle cases where some dicts might be empty
    # or not have all MEPs.
    all_activities = merge_activity_counts(
        amendments_counts if amendments_counts else {}, 
        reports_counts if reports_counts else {}, 
        other_activities_counts if other_activities_counts else {}
    )

    if not all_activities:
        print("No activity data to populate. Exiting populate_activities_table.")
        return

    print(f"DEBUG: Merged activities for {len(all_activities)} MEP-term combinations.")
    # Clear existing data
    c.execute("DELETE FROM activities")
    
    # Insert data
    for (mep_id, term), counts in all_activities.items():
        try:
            # Ensure mep_id exists in meps table
            c.execute("SELECT 1 FROM meps WHERE mep_id = ?", (mep_id,))
            if not c.fetchone():
                # print(f"Skipping activities for MEP {mep_id}, not found in meps table.")
                continue

            if term is None: # Skip if term is None
                # print(f"Skipping activities for MEP {mep_id} due to None term.")
                continue

            # Debug print for amendment counts before insertion
            if counts.get("amendments", 0) > 0:
                print(f"DEBUG populate_activities_table: MEP {mep_id}, Term {term}, Amendments: {counts.get('amendments', 0)}")

            c.execute("""
                INSERT INTO activities (
                    mep_id, term, speeches, reports_rapporteur, reports_shadow,
                    amendments, questions_written, questions_oral, questions_major,
                    motions, motions_individual, opinions_rapporteur, opinions_shadow,
                    declarations, explanations
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                mep_id, term,
                counts.get("speeches", 0),
                counts.get("reports_rapporteur", 0),
                counts.get("reports_shadow", 0),
                counts.get("amendments", 0),
                counts.get("questions_written", 0),
                counts.get("questions_oral", 0),
                counts.get("questions_major", 0),
                counts.get("motions", 0),
                counts.get("motions_individual", 0),
                counts.get("opinions_rapporteur", 0),
                counts.get("opinions_shadow", 0),
                counts.get("declarations", 0),
                counts.get("explanations", 0)
            ))
        except Exception as e:
            # print(f"Error inserting activities for MEP {mep_id}, Term {term}: {e}")
            continue
            
    conn.commit()
    print(f"Populated activities table with {c.execute('SELECT COUNT(*) FROM activities').fetchone()[0]} records.")

def populate_roles_table():
    """Populate the roles table with MEP roles in committees, delegations, etc."""
    print("Populating roles table...")
    meps_data = load_json_auto(RAW/"ep_meps.json.zst")
    if not meps_data:
        print("Failed to load MEP data for roles")
        return

    # Clear existing data
    c.execute("DELETE FROM roles")
    
    roles_added_count = 0
    # DEBUG: Print keys of the first MEP to understand its structure
    if meps_data and len(meps_data) > 0:
        first_mep_entry = meps_data[0]
        print(f"DEBUG: Keys in first MEP entry from ep_meps.json.zst: {list(first_mep_entry.keys())}")
        # You can also print the full first MEP entry if needed, but it might be large
        # print(f"DEBUG: First MEP entry full data: {json.dumps(first_mep_entry, indent=2)}")

    for mep in meps_data:
        mep_id = mep.get("UserID")
        if not mep_id:
            continue

        # Helper to insert role
        def insert_role(role_type, org, org_abbr, role_title, start, end):
            nonlocal roles_added_count
            term = get_term_for_date(start) if start else None
            if not term and end:
                term = get_term_for_date(end)
            
            if term is None:
                return

            # Standardize EP leadership roles before inserting
            normalized_role_title = role_title
            current_role_type = role_type

            if org == "European Parliament": # Check if the organization is the EP itself
                # print(f"DEBUG Potential EP Leadership: MEP {mep_id}, Org: {org}, Role: {role_title}, Start: {start}")
                if "president" in role_title.lower() and "vice" not in role_title.lower() and "committee" not in role_title.lower() and "delegation" not in role_title.lower(): # More specific
                    normalized_role_title = "President"
                    current_role_type = "ep"
                    print(f"DEBUG Normalized to EP President: MEP {mep_id}, Original Role: {role_title}")
                elif ("vice-president" in role_title.lower() or "vice president" in role_title.lower()) and "committee" not in role_title.lower() and "delegation" not in role_title.lower(): # More specific
                    normalized_role_title = "Vice-President"
                    current_role_type = "ep"
                    print(f"DEBUG Normalized to EP Vice-President: MEP {mep_id}, Original Role: {role_title}")
                elif "quaestor" in role_title.lower() and "committee" not in role_title.lower() and "delegation" not in role_title.lower(): # Ensure it's not a committee/delegation quaestor if such a thing exists
                    normalized_role_title = "Quaestor"
                    current_role_type = "ep"
                    print(f"DEBUG Normalized to EP Quaestor: MEP {mep_id}, Original Role: {role_title}")

            try:
                c.execute("""
                    INSERT INTO roles (mep_id, term, role_type, organization, organization_abbr, role, start_date, end_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (mep_id, term, current_role_type, org, org_abbr, normalized_role_title, start, end))
                roles_added_count += 1
            except Exception as e:
                pass

        # Constituencies (Term information primarily)
        # for constituency in mep.get("Constituencies", []):
            # start = constituency.get("start")
            # end = constituency.get("end")
            # insert_role('constituency', constituency.get("country"), constituency.get("name"), "MEP", start, end)

        # Groups and their Offices (potential source of EP leadership roles)
        if "Groups" in mep:
            for group in mep["Groups"]:
                group_org = group.get("Organization")
                group_abbr = group.get("groupid") # Using groupid as abbr
                group_start = group.get("start")
                group_end = group.get("end")
                # Insert the general group membership
                # insert_role('group', group_org, group_abbr, "Member", group_start, group_end)
                print(f"DEBUG Processing Group for MEP {mep_id}: Org='{group_org}', Abbr='{group_abbr}', Start='{group_start}'")

                if "Offices" in group:
                    for office in group["Offices"]:
                        office_title = office.get("Office")
                        office_org = group_org # Office is within the group
                        office_org_abbr = group_abbr
                        # If Office Body is European Parliament, it might be an EP leadership role
                        if office.get("Body") == "European Parliament":
                            office_org = "European Parliament"
                            office_org_abbr = "EP"
                            print(f"DEBUG EP Office Found: MEP {mep_id}, Office Title: {office_title}, Body: {office.get('Body')}")
                        
                        # Fallback for office title if not present
                        if not office_title:
                            office_title = office.get("Function", "Unknown Office") # Use Function as fallback

                        office_start = office.get("start", group_start) # Inherit start from group if not specified
                        office_end = office.get("end", group_end) # Inherit end from group if not specified
                        print(f"DEBUG ==> Office/Function within Group '{group_org}': Title='{office_title}', OrgBody='{office.get('Body')}', Start='{office_start}'")
                        insert_role('group_office', office_org, office_org_abbr, office_title, office_start, office_end)

        # EP Functions (Original check - now superseded by checking Offices within Groups like "European Parliament")
        # if "EPFunctions" in mep: # This key was not found in data
        #    ... (old code commented out or removed)

        # Committees
        if "Committees" in mep:
            for committee in mep["Committees"]:
                org = committee.get("Organization")
                org_abbr = committee.get("abbr")
                role_title = committee.get("role")
                start = committee.get("start")
                end = committee.get("end")
                insert_role('committee', org, org_abbr, role_title, start, end)

        # Delegations
        if "Delegations" in mep:
            for delegation in mep["Delegations"]:
                org = delegation.get("Organization")
                org_abbr = delegation.get("abbr")
                role_title = delegation.get("role")
                start = delegation.get("start")
                end = delegation.get("end")
                insert_role('delegation', org, org_abbr, role_title, start, end)

        # Staff
        if "Staff" in mep:
            for staff in mep["Staff"]:
                org = staff.get("Organization")
                org_abbr = staff.get("abbr")
                role_title = staff.get("role")
                start = staff.get("start")
                end = staff.get("end")
                insert_role('staff', org, org_abbr, role_title, start, end)

    conn.commit()
    print(f"Added {roles_added_count} roles for MEPs to the database")

def calculate_rankings():
    """Calculate and store rankings based on activity and role data."""
    print("Calculating rankings...")
    
    # First, clear existing rankings to avoid duplicates
    c.execute("DELETE FROM rankings")
    conn.commit()
    
    # Define weights for activities and roles
    activity_weights = {
        "speeches": 1,
        "reports_rapporteur": 5,
        "reports_shadow": 3,
        "amendments": 1,
        "questions_written": 1,
        "questions_oral": 1,
        "questions_major": 2,
        "motions": 2,
        "motions_individual": 2,
        "opinions_rapporteur": 3,
        "opinions_shadow": 2,
        "declarations": 1,
        "explanations": 1
    }
    
    role_weights = {
        "committee_chair": 10,
        "committee_vice_chair": 7,
        "committee_member": 5,
        "committee_substitute": 3,
        "delegation_chair": 8,
        "delegation_vice_chair": 6,
        "delegation_member": 4,
        "delegation_substitute": 2,
        "ep_president": 15,  # EP leadership roles
        "ep_vice_president": 12,
        "ep_quaestor": 10
    }
    
    # Get all MEPs with activities or roles
    c.execute("SELECT DISTINCT mep_id FROM activities UNION SELECT DISTINCT mep_id FROM roles")
    mep_ids = [row[0] for row in c.fetchall()]
    
    for mep_id in mep_ids:
        for term in (8, 9, 10):
            # Get activity data
            c.execute("SELECT * FROM activities WHERE mep_id = ? AND term = ?", (mep_id, term))
            activity_row = c.fetchone()
            
            # Get role data
            c.execute("SELECT * FROM roles WHERE mep_id = ? AND term = ?", (mep_id, term))
            role_row = c.fetchone()
            
            if not activity_row and not role_row:
                continue
            
            # Calculate weighted score
            total_score = 0
            
            if activity_row:
                # Activities columns start at index 3 (after id, mep_id, term)
                for i, activity in enumerate(activity_weights.keys()):
                    if activity_row[i+3] is not None:  # Check for NULL values
                        try:
                            total_score += int(activity_row[i+3]) * activity_weights[activity]
                        except (ValueError, TypeError):
                            print(f"Warning: Invalid value for {activity} for MEP {mep_id}")
            
            if role_row:
                # Get role counts from the roles table
                c.execute("""
                    SELECT 
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
                    WHERE mep_id = ? AND term = ?
                """, (mep_id, term))
                role_counts = c.fetchone()
                
                if role_counts:
                    for i, role in enumerate(role_weights.keys()):
                        if role_counts[i] is not None:
                            total_score += int(role_counts[i]) * role_weights[role]
            
            # Insert ranking
            c.execute(
                "INSERT INTO rankings (mep_id, term, total_score) VALUES (?, ?, ?)",
                (mep_id, term, total_score)
            )
    
    conn.commit()
    print(f"Added rankings for {c.execute('SELECT COUNT(DISTINCT mep_id) FROM rankings').fetchone()[0]} MEPs")

def main():
    print("Starting Parltrack data ingest...")
    populate_meps_table()
    populate_activities_table()
    populate_roles_table()
    try:
        inserted_rows, term_rows = update_vote_summary(VoteSummaryConfig())
        print(f"Vote attendance summary updated ({inserted_rows} rows across {term_rows} terms).")
    except VoteSummaryError as exc:
        print(f"WARNING: vote summary not updated: {exc}")
    calculate_rankings()
    print("Ingest complete!")
    
    # Print some statistics
    c.execute("SELECT COUNT(*) FROM meps")
    print(f"Total MEPs: {c.fetchone()[0]}")
    
    for term in (8, 9, 10):
        c.execute("SELECT COUNT(*) FROM rankings WHERE term = ?", (term,))
        print(f"MEPs with rankings for term {term}: {c.fetchone()[0]}")
    
    # Print top 10 MEPs for the latest term
    print("\nTop 10 MEPs for term 10 by total score:")
    c.execute("""
        SELECT m.mep_id, m.full_name, m.country, m.current_party_group, r.total_score
        FROM rankings r
        JOIN meps m ON r.mep_id = m.mep_id
        WHERE r.term = 10
        ORDER BY r.total_score DESC
        LIMIT 10
    """)
    for row in c.fetchall():
        print(f"{row[1]} ({row[2]}, {row[3]}) - Score: {row[4]}")
    
    # Close DB connection
    conn.close()

if __name__ == "__main__":
    main()
