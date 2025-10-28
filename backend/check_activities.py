#!/usr/bin/env python3
import sqlite3
from pathlib import Path

def main():
    """Check the counts of activities in the database."""
    try:
        # Connect to SQLite database
        conn = sqlite3.connect('data/meps.db')
        c = conn.cursor()
        
        # Get column names
        c.execute('PRAGMA table_info(activities)')
        columns = [row[1] for row in c.fetchall()]
        print("Activities table columns:", columns)
        
        # Check for non-zero values in each activity field
        activity_fields = ['speeches', 'reports_rapporteur', 'reports_shadow', 'amendments', 
                         'questions', 'motions', 'opinions']
        
        for field in activity_fields:
            if field not in columns:
                print(f"\nWarning: Field '{field}' not found in activities table")
                continue
            
            # Get total count
            c.execute(f'SELECT SUM({field}) FROM activities')
            total = c.fetchone()[0] or 0
            print(f"\nTotal {field}: {total:,}")
            
            # Get count of MEPs with non-zero values
            c.execute(f'SELECT COUNT(DISTINCT mep_id) FROM activities WHERE {field} > 0')
            mep_count = c.fetchone()[0]
            print(f"MEPs with {field}: {mep_count:,}")
            
            # Get top 5 MEPs for this activity
            c.execute(f'''
                SELECT m.full_name, m.country, a.term, a.{field}
                FROM activities a
                JOIN meps m ON a.mep_id = m.mep_id
                WHERE a.{field} > 0
                ORDER BY a.{field} DESC
                LIMIT 5
            ''')
            print(f"Top 5 MEPs by {field}:")
            for row in c.fetchall():
                print(f"  {row[0]} ({row[1]}, Term {row[2]}): {row[3]:,}")
        
        # Get total activities by term
        print("\nTotal activities by term:")
        c.execute('''
            SELECT term, 
                   SUM(speeches) as speeches,
                   SUM(reports_rapporteur) as reports_rapporteur,
                   SUM(reports_shadow) as reports_shadow,
                   SUM(amendments) as amendments,
                   SUM(questions) as questions,
                   SUM(motions) as motions,
                   SUM(opinions) as opinions
            FROM activities
            GROUP BY term
            ORDER BY term
        ''')
        rows = c.fetchall()
        for row in rows:
            print(f"\nTerm {row[0]}:")
            for i, field in enumerate(activity_fields):
                print(f"  {field}: {row[i+1]:,}")
    
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main() 