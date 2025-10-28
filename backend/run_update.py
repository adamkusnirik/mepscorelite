#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import requests
from tqdm import tqdm
import datetime

# Set paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(ROOT_DIR, 'data')
RAW_DIR = os.path.join(DATA_DIR, 'raw')

# Create dirs if they don't exist
os.makedirs(RAW_DIR, exist_ok=True)

# URL for the data dump
DATA_URL = "https://www.europarl.europa.eu/meps/en/full-list/xml/"
OUTPUT_FILE = os.path.join(RAW_DIR, "meps_data.xml")

def download_file(url, output_path):
    """
    Download a file with progress bar
    """
    response = requests.get(url, stream=True)
    
    if response.status_code != 200:
        print(f"❌ Failed to download: Status code {response.status_code}")
        return False
    
    total_size = int(response.headers.get('content-length', 0))
    block_size = 1024  # 1 Kibibyte
    
    with open(output_path, 'wb') as f:
        desc = f"Downloading {os.path.basename(output_path)}"
        with tqdm(total=total_size, unit='B', unit_scale=True, desc=desc) as pbar:
            for data in response.iter_content(block_size):
                f.write(data)
                pbar.update(len(data))
    
    return True

def main():
    """
    Main function to download data dump
    """
    print(f"Starting data update at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check if file already exists to determine if this is an update or initial download
    is_first_run = not os.path.exists(OUTPUT_FILE)
    
    # Download the file
    success = download_file(DATA_URL, OUTPUT_FILE)
    
    if success:
        if is_first_run:
            print("✅ Downloaded new dump")
        else:
            print("✅ Updated data dump")
    else:
        print("❌ Failed to download data")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 