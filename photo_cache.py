#!/usr/bin/env python3
"""
MEP Photo Caching System
Downloads and caches MEP photos locally for faster loading
"""

import os
import requests
import hashlib
import time
from pathlib import Path
import json
import threading
from concurrent.futures import ThreadPoolExecutor
import sys

# Configuration
PHOTO_CACHE_DIR = Path("public/photos")
EUROPARL_PHOTO_BASE = "https://www.europarl.europa.eu/mepphoto"
CACHE_DURATION_DAYS = 30
MAX_CONCURRENT_DOWNLOADS = 5
PHOTO_TIMEOUT = 10

def setup_cache_directory():
    """Create cache directory if it doesn't exist"""
    PHOTO_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
def get_cache_path(mep_id):
    """Get local cache path for MEP photo"""
    return PHOTO_CACHE_DIR / f"{mep_id}.jpg"

def is_cache_valid(cache_path):
    """Check if cached photo is still valid"""
    if not cache_path.exists():
        return False
    
    # Check if file is recent enough
    file_age = time.time() - cache_path.stat().st_mtime
    return file_age < (CACHE_DURATION_DAYS * 24 * 3600)

def download_mep_photo(mep_id):
    """Download MEP photo from Europarl website"""
    try:
        photo_url = f"{EUROPARL_PHOTO_BASE}/{mep_id}.jpg"
        cache_path = get_cache_path(mep_id)
        
        # Skip if already cached and valid
        if is_cache_valid(cache_path):
            return True
            
        print(f"Downloading photo for MEP {mep_id}...")
        
        response = requests.get(photo_url, timeout=PHOTO_TIMEOUT, stream=True)
        
        if response.status_code == 200:
            # Check if it's actually an image
            content_type = response.headers.get('content-type', '')
            if 'image' in content_type:
                with open(cache_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"✓ Cached photo for MEP {mep_id}")
                return True
            else:
                print(f"✗ Invalid content type for MEP {mep_id}: {content_type}")
                
        elif response.status_code == 404:
            # Create a placeholder file to avoid repeated 404 requests
            cache_path.touch()
            print(f"- No photo available for MEP {mep_id}")
        else:
            print(f"✗ HTTP {response.status_code} for MEP {mep_id}")
            
    except requests.RequestException as e:
        print(f"✗ Download failed for MEP {mep_id}: {e}")
    except Exception as e:
        print(f"✗ Unexpected error for MEP {mep_id}: {e}")
    
    return False

def get_mep_ids_from_datasets():
    """Extract MEP IDs from dataset files"""
    mep_ids = set()
    
    for term in [8, 9, 10]:
        dataset_path = Path(f"public/data/term{term}_dataset.json")
        if dataset_path.exists():
            try:
                with open(dataset_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Handle different dataset structures
                if isinstance(data, dict) and 'meps' in data:
                    mep_list = data['meps']
                elif isinstance(data, list):
                    mep_list = data
                else:
                    print(f"Unknown dataset structure in term {term}")
                    continue
                    
                for mep in mep_list:
                    if 'mep_id' in mep:
                        mep_ids.add(mep['mep_id'])
                print(f"Found {len([m for m in mep_list if 'mep_id' in m])} MEPs in term {term}")
            except Exception as e:
                print(f"Error reading term {term} dataset: {e}")
    
    return sorted(mep_ids)

def cache_all_photos():
    """Download and cache all MEP photos"""
    setup_cache_directory()
    
    print("Starting MEP photo caching...")
    mep_ids = get_mep_ids_from_datasets()
    
    if not mep_ids:
        print("No MEP IDs found in datasets")
        return
    
    print(f"Found {len(mep_ids)} unique MEPs across all terms")
    
    # Use ThreadPoolExecutor for concurrent downloads
    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_DOWNLOADS) as executor:
        futures = [executor.submit(download_mep_photo, mep_id) for mep_id in mep_ids]
        
        # Wait for completion and count results
        successful = 0
        for i, future in enumerate(futures):
            try:
                if future.result():
                    successful += 1
                if (i + 1) % 50 == 0:
                    print(f"Progress: {i + 1}/{len(mep_ids)} photos processed")
            except Exception as e:
                print(f"Error processing photo: {e}")
    
    print(f"\nPhoto caching completed:")
    print(f"- Total MEPs: {len(mep_ids)}")
    print(f"- Successfully cached: {successful}")
    print(f"- Cache directory: {PHOTO_CACHE_DIR.absolute()}")

def clean_old_cache():
    """Remove old cached photos"""
    if not PHOTO_CACHE_DIR.exists():
        return
    
    cleaned = 0
    for photo_file in PHOTO_CACHE_DIR.glob("*.jpg"):
        if not is_cache_valid(photo_file):
            photo_file.unlink()
            cleaned += 1
    
    if cleaned > 0:
        print(f"Cleaned {cleaned} old cached photos")

def get_cache_stats():
    """Get statistics about the photo cache"""
    if not PHOTO_CACHE_DIR.exists():
        return {"cached_photos": 0, "cache_size_mb": 0}
    
    photos = list(PHOTO_CACHE_DIR.glob("*.jpg"))
    total_size = sum(f.stat().st_size for f in photos if f.stat().st_size > 0)
    
    return {
        "cached_photos": len([f for f in photos if f.stat().st_size > 0]),
        "placeholder_files": len([f for f in photos if f.stat().st_size == 0]),
        "cache_size_mb": round(total_size / 1024 / 1024, 2),
        "cache_directory": str(PHOTO_CACHE_DIR.absolute())
    }

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "stats":
            stats = get_cache_stats()
            print("Photo Cache Statistics:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
        elif command == "clean":
            clean_old_cache()
        elif command == "single" and len(sys.argv) > 2:
            mep_id = sys.argv[2]
            setup_cache_directory()
            download_mep_photo(mep_id)
        else:
            print("Usage: python photo_cache.py [stats|clean|single <mep_id>]")
    else:
        cache_all_photos()