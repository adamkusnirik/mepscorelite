#!/usr/bin/env python3
"""
Simple diagnostic script for MEP Score production issues
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def check_file_exists(filepath, description):
    """Check if a file exists and print status"""
    if os.path.exists(filepath):
        print(f"✓ {description}: {filepath}")
        return True
    else:
        print(f"✗ {description}: {filepath} (MISSING)")
        return False

def check_python_modules():
    """Check if required Python modules are available"""
    modules = ['sqlite3', 'json', 'http.server', 'socketserver']
    optional_modules = ['psutil', 'flask', 'flask_cors']
    
    print("\nChecking Python modules...")
    all_good = True
    
    for module in modules:
        try:
            __import__(module)
            print(f"✓ {module}")
        except ImportError:
            print(f"✗ {module} (REQUIRED)")
            all_good = False
    
    for module in optional_modules:
        try:
            __import__(module)
            print(f"✓ {module} (optional)")
        except ImportError:
            print(f"- {module} (optional, not available)")
    
    return all_good

def test_database():
    """Test database connectivity"""
    print("\nTesting database...")
    try:
        import sqlite3
        conn = sqlite3.connect('data/meps.db', timeout=5)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM meps WHERE term = 10")
        count = cursor.fetchone()[0]
        conn.close()
        print(f"✓ Database accessible, {count} MEPs in term 10")
        return True
    except Exception as e:
        print(f"✗ Database error: {e}")
        return False

def test_data_files():
    """Test if key data files exist and are readable"""
    print("\nChecking data files...")
    data_files = [
        'data/meps.db',
        'data/parltrack/ep_mep_activities.json',
        'data/parltrack/ep_amendments.json',
        'public/data/term10_dataset.json'
    ]
    
    all_good = True
    for filepath in data_files:
        if check_file_exists(filepath, "Data file"):
            try:
                if filepath.endswith('.json'):
                    with open(filepath, 'r') as f:
                        # Just read first 1000 chars to verify it's valid
                        data = f.read(1000)
                        if data.strip().startswith('[') or data.strip().startswith('{'):
                            print(f"  → JSON format looks good")
                        else:
                            print(f"  → Warning: doesn't look like JSON")
                            all_good = False
            except Exception as e:
                print(f"  → Error reading file: {e}")
                all_good = False
        else:
            all_good = False
    
    return all_good

def test_simple_server():
    """Test if we can start a simple HTTP server"""
    print("\nTesting simple server startup...")
    try:
        # Try to import the server modules
        import http.server
        import socketserver
        
        # Test if port 8000 is available
        test_server = socketserver.TCPServer(("", 8001), http.server.SimpleHTTPRequestHandler)
        test_server.server_close()
        print("✓ Can create HTTP server")
        return True
    except Exception as e:
        print(f"✗ Cannot create HTTP server: {e}")
        return False

def main():
    print("======================================")
    print("MEP Score Production Diagnostics")
    print("======================================")
    
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    print(f"Current user: {os.getenv('USER', 'unknown')}")
    
    # Check core files
    print("\nChecking core files...")
    files_ok = True
    core_files = [
        ('serve.py', 'Main server script'),
        ('deployment/production_serve.py', 'Production server script'),
        ('public/index.html', 'Frontend main page'),
        ('public/profile.html', 'Profile page'),
        ('public/js/profile.js', 'Profile JavaScript')
    ]
    
    for filepath, description in core_files:
        if not check_file_exists(filepath, description):
            files_ok = False
    
    # Check Python modules
    modules_ok = check_python_modules()
    
    # Check data files
    data_ok = test_data_files()
    
    # Test database
    db_ok = test_database()
    
    # Test server capability
    server_ok = test_simple_server()
    
    print("\n======================================")
    print("DIAGNOSIS SUMMARY")
    print("======================================")
    
    if all([files_ok, modules_ok, data_ok, db_ok, server_ok]):
        print("✓ All checks passed! The issue is likely:")
        print("  - Service not running (systemctl start mepscore)")
        print("  - Port binding issues")
        print("  - Nginx configuration")
        print("\nTry running: python3 serve.py")
    else:
        print("✗ Issues found:")
        if not files_ok:
            print("  - Missing core files")
        if not modules_ok:
            print("  - Missing Python modules")
        if not data_ok:
            print("  - Data file issues")
        if not db_ok:
            print("  - Database problems")
        if not server_ok:
            print("  - Server startup issues")
    
    print("\nFor manual testing:")
    print("  cd /var/www/mepscore")
    print("  python3 serve.py")
    print("  # In another terminal:")
    print("  curl http://localhost:8000/api/health")

if __name__ == "__main__":
    main()