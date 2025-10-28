#!/usr/bin/env python3
"""
Restore script for ParlTrack data optimization
Restores original files from backup directory
"""

import shutil
from pathlib import Path
import sys

def restore_original_files():
    parltrack_dir = Path("data/parltrack")
    backup_dir = parltrack_dir / "backup_original"
    
    if not backup_dir.exists():
        print("ERROR: Backup directory not found!")
        sys.exit(1)
    
    # Restore original files
    for backup_file in backup_dir.glob("*.json"):
        original_path = parltrack_dir / backup_file.name
        print(f"Restoring {backup_file.name}...")
        shutil.copy2(backup_file, original_path)
    
    # Remove optimized files
    for optimized_file in parltrack_dir.glob("*_term*.json"):
        print(f"Removing optimized file {optimized_file.name}...")
        optimized_file.unlink()
    
    # Remove metadata
    metadata_file = parltrack_dir / "optimization_metadata.json"
    if metadata_file.exists():
        metadata_file.unlink()
        print("Removed optimization metadata")
    
    print("Original files restored successfully!")

if __name__ == "__main__":
    restore_original_files()
