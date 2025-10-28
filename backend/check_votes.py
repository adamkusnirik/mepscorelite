#!/usr/bin/env python3
import json
import zstandard as zstd
from pathlib import Path
from collections import Counter
from pprint import pprint

def load_json(fname):
    """Load JSON data from a file."""
    try:
        if fname.suffix == '.zst':
            with open(fname, 'rb') as fh:
                dctx = zstd.ZstdDecompressor()
                with dctx.stream_reader(fh) as reader:
                    text = reader.read().decode('utf-8')
                    return json.loads(text)
        else:
            return json.loads(Path(fname).read_text(encoding="utf-8"))
    except Exception as e:
        print(f"Error loading {fname}: {e}")
        return None

def analyze_votes(votes_data):
    """Analyze the structure of votes data."""
    field_counts = Counter()
    activity_types = Counter()
    
    # Process first vote in detail
    if votes_data and len(votes_data) > 0:
        first_vote = votes_data[0]
        print("\nFirst vote structure:")
        for key, value in first_vote.items():
            if isinstance(value, (str, int, bool, float)):
                print(f"  {key}: {value}")
            else:
                print(f"  {key}: {type(value)} with {len(value)} items")
        
        print("\nFirst vote full data:")
        print(json.dumps(first_vote, indent=2))
    
    # Count fields across all votes
    for vote in votes_data:
        for key in vote.keys():
            field_counts[key] += 1
    
    print("\nField counts across all votes:")
    for field, count in sorted(field_counts.items(), key=lambda x: (-x[1], x[0])):
        print(f"  {field}: {count}")
    
    # Look for activity-related fields
    print("\nChecking for activity-related fields:")
    activity_fields = ['speeches', 'questions', 'motions', 'opinions', 'rapporteur', 'shadows']
    for vote in votes_data:
        for field in activity_fields:
            if field in vote:
                value = vote[field]
                if isinstance(value, list):
                    print(f"\nExample of {field}:")
                    for item in value[:3]:  # Show first 3 items
                        print(f"  {item}")
                    break

def main():
    RAW = Path("data/parltrack")
    
    # Load votes data
    votes_file = RAW/"ep_votes.json.zst"
    print(f"Checking file: {votes_file}")
    print(f"File exists: {votes_file.exists()}")
    
    if not votes_file.exists():
        print("No votes data file found!")
        return
    
    # Load the data
    print("\nLoading votes data...")
    votes_data = load_json(votes_file)
    if not votes_data:
        print("Failed to load votes data")
        return
    
    print(f"\nTotal votes: {len(votes_data)}")
    
    # Analyze votes
    analyze_votes(votes_data)

if __name__ == "__main__":
    main() 