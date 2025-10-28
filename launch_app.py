#!/usr/bin/env python3
"""
Combined launcher for MEP Ranking application
Kills existing processes on port 8000, starts the Flask API server, and opens the browser
"""

import subprocess
import platform
import time
import webbrowser
import os
import sys
from pathlib import Path

from file_utils import resolve_json_path

def kill_process_on_port(port):
    """Kill any existing process using the specified port"""
    print(f"Checking for existing processes on port {port}...")
    
    if platform.system() == "Windows":
        try:
            # Find processes using the port
            command = f"netstat -aon | findstr :{port}"
            result = subprocess.run(command, capture_output=True, text=True, shell=True, check=True)
            
            for line in result.stdout.strip().split('\n'):
                if "LISTENING" in line:
                    parts = line.split()
                    pid = parts[-1]
                    if pid.isdigit():
                        print(f"Killing process {pid} using port {port}")
                        subprocess.run(f"taskkill /PID {pid} /F", shell=True, check=True)
                        print(f"Process {pid} killed successfully")
                        time.sleep(1)  # Give it time to fully terminate
                        return True
        except subprocess.CalledProcessError as e:
            if "findstr" in e.cmd and e.returncode == 1:
                print(f"No process found using port {port}")
            else:
                print(f"Error checking for processes: {e}")
        except Exception as e:
            print(f"Error killing process: {e}")
    
    elif platform.system() == "Linux" or platform.system() == "Darwin":
        try:
            # Find processes using the port
            command = f"lsof -t -i:{port}"
            result = subprocess.run(command, capture_output=True, text=True, shell=True)
            
            if result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid.isdigit():
                        print(f"Killing process {pid} using port {port}")
                        subprocess.run(f"kill -9 {pid}", shell=True, check=True)
                        print(f"Process {pid} killed successfully")
                        time.sleep(1)  # Give it time to fully terminate
                        return True
            else:
                print(f"No process found using port {port}")
        except Exception as e:
            print(f"Error killing process: {e}")
    
    return False

def check_required_files():
    """Check if all required files exist"""
    required_files = [
        'serve.py',
        'public/index.html',
        'public/profile.html',
        'data/meps.db'
    ]
    parltrack_files = [
        Path('data/parltrack/ep_mep_activities.json'),
        Path('data/parltrack/ep_amendments.json'),
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    for file_path in parltrack_files:
        resolved = resolve_json_path(file_path)
        if not resolved.exists():
            missing_files.append(f"{file_path} (.json or .json.zst)")
    
    if missing_files:
        print("ERROR: Required files not found:")
        for file_path in missing_files:
            print(f"  - {file_path}")
        return False
    
    print("All required files found ✓")
    return True

def main():
    PORT = 8000
    BASE_URL = f"http://localhost:{PORT}"
    
    print("=" * 60)
    print("MEP Ranking Application Launcher")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not os.path.exists('serve.py'):
        print("ERROR: serve.py not found!")
        print("Please run this script from the project root directory.")
        return
    
    # Check required files
    if not check_required_files():
        return
    
    # Kill any existing processes on port 8000
    kill_process_on_port(PORT)
    
    print(f"\nStarting API server on port {PORT}...")
    print(f"Server will be available at: {BASE_URL}")
    
    try:
        # Start the API server in a subprocess
        server_process = subprocess.Popen([
            sys.executable, 'serve.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Wait a moment for the server to start
        print("Waiting for server to start...")
        time.sleep(3)
        
        # Check if the server started successfully
        if server_process.poll() is not None:
            # Server process ended
            stdout, stderr = server_process.communicate()
            print("ERROR: Server failed to start!")
            print("STDOUT:", stdout)
            print("STDERR:", stderr)
            return
        
        print("✓ API server started successfully!")
        print(f"✓ Server running at: {BASE_URL}")
        
        # Open the browser
        print("\nOpening browser...")
        webbrowser.open(BASE_URL)
        
        print("\n" + "=" * 60)
        print("APPLICATION LAUNCHED SUCCESSFULLY!")
        print("=" * 60)
        print(f"Frontend: {BASE_URL}")
        print(f"Profile page: {BASE_URL}/profile.html")
        print(f"API endpoints: {BASE_URL}/api/...")
        print("\nPress Ctrl+C to stop the server")
        print("=" * 60)
        
        # Keep the script running and monitor the server
        try:
            while True:
                if server_process.poll() is not None:
                    print("\nServer process ended unexpectedly!")
                    break
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\nStopping server...")
            server_process.terminate()
            server_process.wait()
            print("Server stopped successfully!")
    
    except Exception as e:
        print(f"ERROR: Failed to start server: {e}")
        if 'server_process' in locals():
            server_process.terminate()

if __name__ == "__main__":
    main() 
