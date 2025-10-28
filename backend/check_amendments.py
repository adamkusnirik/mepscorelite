#!/usr/bin/env python3
import json
from pathlib import Path
from collections import Counter

from file_utils import load_combined_dataset

def analyze_amendments(amendments_data):
    """Analyze the structure of amendments data."""
    field_counts = Counter()
    mep_counts = Counter()
    
    # Process first amendment in detail
    if amendments_data and len(amendments_data) > 0:
        first_amendment = amendments_data[0]
        print("\nFirst amendment structure:")
        for key, value in first_amendment.items():
            if isinstance(value, (str, int, bool, float)):
                print(f"  {key}: {value}")
            else:
                print(f"  {key}: {type(value)} with {len(value)} items")
        
        print("\nFirst amendment full data:")
        print(json.dumps(first_amendment, indent=2))
    
    # Count fields across all amendments
    for amendment in amendments_data:
        for key in amendment.keys():
            field_counts[key] += 1
        
        # Count amendments per MEP
        if "meps" in amendment and isinstance(amendment["meps"], list):
            for mep in amendment["meps"]:
                if mep is not None:
                    mep_counts[str(mep)] += 1
    
    print("\nField counts across all amendments:")
    for field, count in sorted(field_counts.items(), key=lambda x: (-x[1], x[0])):
        print(f"  {field}: {count}")
    
    print("\nTop 10 MEPs by amendment count:")
    for mep, count in sorted(mep_counts.items(), key=lambda x: (-x[1], x[0]))[:10]:
        print(f"  MEP ID {mep}: {count} amendments")

def main():
    RAW = Path("data/parltrack")
    
    try:
        amendments_data = load_combined_dataset(
            RAW / "ep_amendments.json",
            [RAW / f"ep_amendments_term{term}.json" for term in (8, 9, 10)],
        )
    except FileNotFoundError:
        print("No amendments data files found!")
        return
    
    print(f"\nTotal amendments: {len(amendments_data)}")
    
    # Analyze amendments
    analyze_amendments(amendments_data)

if __name__ == "__main__":
    main() 
