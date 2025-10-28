#!/usr/bin/env python3
"""
Check the counts of unique MEPs in the database for each term.
"""

import sqlite3
from pathlib import Path

DB = Path("data/meps.db")

def main():
    """Check the counts of unique MEPs in the database for each term."""
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    
    print("Checking unique MEP counts in rankings table:")
    for term in (8, 9, 10):
        cursor.execute("""
            SELECT COUNT(DISTINCT mep_id) 
            FROM rankings 
            WHERE term = ?
        """, (term,))
        count = cursor.fetchone()[0]
        print(f"Term {term}: {count} unique MEPs")
    
    print("\nRunning SQL for term 9 dataset to check for duplicates:")
    cursor.execute("""
        SELECT COUNT(*), COUNT(DISTINCT mep_id)
        FROM (
            SELECT 
                m.mep_id
            FROM 
                rankings r
            JOIN 
                meps m ON r.mep_id = m.mep_id
            LEFT JOIN 
                activities a ON r.mep_id = a.mep_id AND r.term = a.term
            LEFT JOIN 
                roles ro ON r.mep_id = ro.mep_id AND r.term = ro.term
            WHERE 
                r.term = 9
        )
    """)
    total, unique = cursor.fetchone()
    print(f"Total rows: {total}, Unique MEPs: {unique}")
    print(f"Duplicate MEPs: {total - unique}")
    
    conn.close()

if __name__ == "__main__":
    main() 