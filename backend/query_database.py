#!/usr/bin/env python3
"""
Query the MEPs database to verify its structure and content
"""

import sqlite3
from pathlib import Path

DB = Path("data/meps.db")

def main():
    """Run queries on the database and print results"""
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    
    # Get table names
    c.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = c.fetchall()
    print("Database tables:")
    for table in tables:
        print(f"- {table[0]}")
    
    # Check schema for each table
    for table in tables:
        table_name = table[0]
        print(f"\nSchema for {table_name}:")
        c.execute(f"PRAGMA table_info({table_name})")
        columns = c.fetchall()
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
    
    # Count records in each table
    print("\nRecord counts:")
    for table in tables:
        table_name = table[0]
        c.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = c.fetchone()[0]
        print(f"- {table_name}: {count} records")
    
    # Show sample data from each table
    for table in tables:
        table_name = table[0]
        print(f"\nSample data from {table_name} (first 5 rows):")
        c.execute(f"SELECT * FROM {table_name} LIMIT 5")
        rows = c.fetchall()
        for row in rows:
            print(f"  {row}")
    
    # Show top 10 MEPs for term 9 (most recent full term)
    print("\nTop 10 MEPs for term 9 by total score:")
    c.execute("""
        SELECT m.mep_id, m.full_name, m.country, m.current_party_group, r.total_score
        FROM rankings r
        JOIN meps m ON r.mep_id = m.mep_id
        WHERE r.term = 9
        ORDER BY r.total_score DESC
        LIMIT 10
    """)
    
    for row in c.fetchall():
        print(f"{row[1]} ({row[2]}, {row[3]}) - Score: {row[4]}")
    
    # Show activity breakdown for top MEP in term 9
    c.execute("""
        SELECT r.mep_id, m.full_name
        FROM rankings r
        JOIN meps m ON r.mep_id = m.mep_id
        WHERE r.term = 9
        ORDER BY r.total_score DESC
        LIMIT 1
    """)
    top_mep = c.fetchone()
    
    if top_mep:
        print(f"\nActivity breakdown for top MEP in term 9: {top_mep[1]}")
        c.execute("""
            SELECT speeches, reports_rapporteur, reports_shadow, amendments, 
                   questions_written, questions_oral, questions_major,
                   motions, motions_individual, 
                   opinions_rapporteur, opinions_shadow,
                   declarations, explanations
            FROM activities
            WHERE mep_id = ? AND term = 9
        """, (top_mep[0],))
        
        activities = c.fetchone()
        if activities:
            print(f"  Speeches: {activities[0]}")
            print(f"  Reports (Rapporteur): {activities[1]}")
            print(f"  Reports (Shadow): {activities[2]}")
            print(f"  Amendments: {activities[3]}")
            print(f"  Questions (Written): {activities[4]}")
            print(f"  Questions (Oral): {activities[5]}")
            print(f"  Questions (Major): {activities[6]}")
            print(f"  Motions: {activities[7]}")
            print(f"  Motions (Individual): {activities[8]}")
            print(f"  Opinions (Rapporteur): {activities[9]}")
            print(f"  Opinions (Shadow): {activities[10]}")
            print(f"  Declarations: {activities[11]}")
            print(f"  Explanations: {activities[12]}")
    
    conn.close()

if __name__ == "__main__":
    main() 