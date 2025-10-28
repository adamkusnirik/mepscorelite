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

def get_latest_constituency(constituencies):
    """Get the most recent constituency from the list."""
    if not constituencies:
        return None
    return sorted(constituencies, key=lambda x: x.get('end', ''), reverse=True)[0]

def analyze_meps(meps_data):
    """Analyze the MEP data and look up specific MEPs."""
    field_counts = Counter()
    activity_types = Counter()
    
    # Process first MEP in detail
    if meps_data and len(meps_data) > 0:
        first_mep = meps_data[0]
        print("\nFirst MEP structure:")
        for key, value in first_mep.items():
            if isinstance(value, (str, int, bool, float)):
                print(f"  {key}: {value}")
            else:
                print(f"  {key}: {type(value)} with {len(value)} items")
        
        print("\nFirst MEP full data:")
        print(json.dumps(first_mep, indent=2))
    
    # Count fields across all MEPs
    for mep in meps_data:
        for key in mep.keys():
            field_counts[key] += 1
        
        # Count activity types
        for activity in mep.get("Activity", []):
            if isinstance(activity, dict):
                for key in activity.keys():
                    activity_types[key] += 1
    
    print("\nField counts across all MEPs:")
    for field, count in sorted(field_counts.items(), key=lambda x: (-x[1], x[0])):
        print(f"  {field}: {count}")
    
    print("\nActivity types found:")
    for activity_type, count in sorted(activity_types.items(), key=lambda x: (-x[1], x[0])):
        print(f"  {activity_type}: {count}")
    
    # Look for MEPs with activities
    print("\nExample MEP with activities:")
    for mep in meps_data:
        if mep.get("Activity"):
            name = mep.get("Name", {}).get("full", "Unknown")
            print(f"\nActivities for {name}:")
            for activity in mep.get("Activity", []):
                if isinstance(activity, dict):
                    print(f"\nTerm {activity.get('term')}:")
                    for key, value in activity.items():
                        if key != "term":
                            print(f"  {key}: {value}")
            break

def main():
    RAW = Path("data/parltrack")
    
    # Load MEP data
    meps_file = RAW/"ep_meps.json.zst"
    print(f"Checking file: {meps_file}")
    print(f"File exists: {meps_file.exists()}")
    
    if not meps_file.exists():
        print("No MEP data file found!")
        return
    
    # Load the data
    print("\nLoading MEP data...")
    meps_data = load_json(meps_file)
    if not meps_data:
        print("Failed to load MEP data")
        return
    
    print(f"\nTotal MEPs: {len(meps_data)}")
    
    # Analyze MEPs
    analyze_meps(meps_data)

if __name__ == "__main__":
    main() 