#!/usr/bin/env python3
"""
MEP Score Application Server with API Support
Mobile-responsive server with API endpoints for detailed MEP activity data
"""

import http.server
import socketserver
import subprocess
import os
import platform
import urllib.parse
import json
import sqlite3
import datetime as dt
from pathlib import Path

from backend.file_utils import load_json_auto, resolve_json_path

PORT = 8000
DIRECTORY = "public"

def kill_process_on_port(port):
    if platform.system() == "Windows":
        try:
            command = f"netstat -aon | findstr :{port}"
            result = subprocess.run(command, capture_output=True, text=True, shell=True, check=True)
            for line in result.stdout.strip().split('\n'):
                if "LISTENING" in line:
                    parts = line.split()
                    pid = parts[-1]
                    if pid.isdigit():
                        print(f"Attempting to kill process {pid} using port {port}")
                        subprocess.run(f"taskkill /PID {pid} /F", shell=True, check=True)
                        print(f"Process {pid} killed.")
                        return
        except subprocess.CalledProcessError as e:
            if "findstr" in str(e.cmd) and e.returncode == 1:
                 print(f"No process found using port {port}.")
            else:
                print(f"Failed to find or kill process on port {port}: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")

class MEPAPIHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def translate_path(self, path):
        """Override to serve files from project root for parltrack data directory and logos"""
        # If the path starts with /data/parltrack/, serve from project root
        if path.startswith('/data/parltrack/'):
            # Remove the leading slash and serve from project root
            return path[1:]  # This will be relative to the current working directory
        # If the path starts with /logos/, serve from project root
        if path.startswith('/logos/'):
            # Remove the leading slash and serve from project root
            return path[1:]  # This will be relative to the current working directory
        # Otherwise, use the default behavior (serve from public directory)
        return super().translate_path(path)

    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        query_params = urllib.parse.parse_qs(parsed_path.query)
        
        # Handle API endpoints
        if path.startswith('/api/'):
            self.handle_api_request(path, query_params)
        else:
            # Serve static files
            super().do_GET()
    
    def handle_api_request(self, path, query_params):
        """Handle API endpoints"""
        try:
            # MEP category details endpoint
            if path.startswith('/api/mep/') and '/category/' in path:
                parts = path.split('/')
                if len(parts) >= 5:
                    mep_id = int(parts[3])
                    category = parts[5]
                    term = int(query_params.get('term', [10])[0])
                    offset = int(query_params.get('offset', [0])[0])
                    limit = int(query_params.get('limit', [15])[0])
                    
                    print(f"API Request: MEP {mep_id}, Category: {category}, Term: {term}")
                    result = self.get_mep_category_data(mep_id, category, term, offset, limit)
                    self.send_json_response(result)
                    return
            
            # MEP activity details endpoint (alternative URL pattern)
            if path.startswith('/api/mep/') and '/activities/' in path:
                parts = path.split('/')
                if len(parts) >= 5:
                    mep_id = int(parts[3])
                    category = parts[5]
                    term = int(query_params.get('term', [10])[0])
                    offset = int(query_params.get('offset', [0])[0])
                    limit = int(query_params.get('limit', [15])[0])
                    
                    print(f"API Request (activities): MEP {mep_id}, Category: {category}, Term: {term}")
                    result = self.get_mep_category_data(mep_id, category, term, offset, limit)
                    self.send_json_response(result)
                    return
            
            # Health check endpoint
            if path == '/api/health':
                result = {'success': True, 'status': 'Mobile-responsive API server is running'}
                self.send_json_response(result)
                return
            
            # Default 404 for unknown API endpoints
            self.send_error(404, "API endpoint not found")
            
        except Exception as e:
            print(f"API Error: {e}")
            import traceback
            traceback.print_exc()
            error_response = {
                'success': False,
                'error': str(e)
            }
            self.send_json_response(error_response, status=500)
    
    def get_mep_category_data(self, mep_id, category, term, offset, limit):
        """Get data for a specific MEP category"""
        try:
            # First check database for activity counts
            conn = sqlite3.connect('data/meps.db')
            cursor = conn.cursor()
            
            # Map category names to database columns
            category_mapping = {
                'amendments': 'amendments',
                'speeches': 'speeches',
                'questions': 'questions_written',
                'questions_written': 'questions_written',
                'questions_oral': 'questions_oral',
                'motions': 'motions',
                'explanations': 'explanations',
                'reports_rapporteur': 'reports_rapporteur',
                'reports_shadow': 'reports_shadow',
                'opinions_rapporteur': 'opinions_rapporteur',
                'opinions_shadow': 'opinions_shadow'
            }

            if category not in category_mapping:
                return {
                    'success': False,
                    'error': f'Unknown category: {category}'
                }

            cursor.execute(f'SELECT {category_mapping[category]} FROM activities WHERE mep_id = ? AND term = ?', (mep_id, term))
            result = cursor.fetchone()
            conn.close()

            if not result:
                return {
                    'success': True,
                    'data': [],
                    'total_count': 0,
                    'category': category,
                    'offset': offset,
                    'limit': limit,
                    'has_more': False,
                    'mep_id': mep_id,
                    'term': term
                }

            total_count = result[0] or 0

            # For detailed data, load from appropriate source
            if category == 'amendments':
                return self.get_amendments_detailed(mep_id, term, offset, limit, total_count)
            elif category in ['speeches', 'questions', 'questions_written', 'questions_oral', 'motions', 'explanations', 'reports_rapporteur', 'reports_shadow', 'opinions_rapporteur', 'opinions_shadow']:
                return self.get_activities_detailed(mep_id, category, term, offset, limit, total_count)
            else:
                # Return summary data for other categories
                return {
                    'success': True,
                    'data': [{
                        'type': category.replace('_', ' ').title(),
                        'title': f'{category.replace("_", " ").title()} #{i+1}',
                        'date': f'Term {term}',
                        'note': f'Total count: {total_count}. Detailed breakdown not available in current dataset.'
                    } for i in range(min(total_count, limit))],
                    'total_count': total_count,
                    'category': category,
                    'offset': offset,
                    'limit': limit,
                    'has_more': total_count > offset + limit,
                    'mep_id': mep_id,
                    'term': term
                }

        except Exception as e:
            print(f"Error processing category {category}: {e}")
            return {
                'success': False,
                'error': f'Error reading data: {str(e)}'
            }
    
    def get_amendments_detailed(self, mep_id, term, offset, limit, total_count):
        """Get detailed amendments data"""
        amendments_file = resolve_json_path(Path(f"data/parltrack/ep_amendments_term{term}.json"))

        if not amendments_file.exists():
            return {
                'success': False,
                'error': f'Amendments data file not found for term {term}'
            }

        try:
            all_amendments = load_json_auto(amendments_file)

            # Find MEP's amendments (term-specific files are already filtered by term)
            mep_amendments = []
            for amend in all_amendments:
                if mep_id in amend.get('meps', []):
                    mep_amendments.append(amend)

            # Sort and paginate
            mep_amendments.sort(key=lambda x: x.get('date', ''), reverse=True)
            paginated_data = mep_amendments[offset:offset + limit]

            return {
                'success': True,
                'data': paginated_data,
                'total_count': len(mep_amendments),
                'category': 'amendments',
                'offset': offset,
                'limit': limit,
                'has_more': len(mep_amendments) > offset + limit,
                'mep_id': mep_id,
                'term': term
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to load amendments: {str(e)}'
            }

    def get_activities_detailed(self, mep_id, category, term, offset, limit, total_count):
        """Get detailed activities data from term-specific activities file"""
        # Use term-specific activities files
        activities_file = resolve_json_path(Path(f"data/parltrack/ep_mep_activities_term{term}.json"))

        if not activities_file.exists():
            return {
                'success': False,
                'error': f'Activities data file not found for term {term}: {activities_file}'
            }

        try:
            data = load_json_auto(activities_file)

            # Find MEP's activities
            mep_activities = None
            for mep_data in data:
                if mep_data.get('mep_id') == mep_id:
                    mep_activities = mep_data
                    break

            if not mep_activities:
                return {
                    'success': False,
                    'error': f'MEP {mep_id} not found'
                }

            # Get category data
            filtered_items = []
            if category == 'speeches':
                all_items = mep_activities.get('CRE', [])
                filtered_items = [
                    item for item in all_items
                    if 'Explanations of vote' not in item.get('title', '')
                    and 'One-minute speeches' not in item.get('title', '')
                ]
            elif category in ['questions', 'questions_written']:
                filtered_items = mep_activities.get('WQ', [])
            elif category == 'questions_oral':
                filtered_items = mep_activities.get('OQ', [])
            elif category == 'motions':
                filtered_items = mep_activities.get('MOTION', [])
            elif category == 'explanations':
                wexp = mep_activities.get('WEXP', [])
                cre_exp = [
                    item for item in mep_activities.get('CRE', [])
                    if 'Explanations of vote' in item.get('title', '')
                ]
                filtered_items = wexp + cre_exp
            elif category == 'reports_rapporteur':
                filtered_items = mep_activities.get('REPORT', [])
            elif category == 'reports_shadow':
                filtered_items = mep_activities.get('REPORT-SHADOW', [])
            elif category == 'opinions_rapporteur':
                filtered_items = mep_activities.get('COMPARL', [])
            elif category == 'opinions_shadow':
                filtered_items = mep_activities.get('COMPARL-SHADOW', [])

            # Sort and paginate
            filtered_items.sort(key=lambda x: x.get('date', ''), reverse=True)
            paginated_data = filtered_items[offset:offset + limit]

            return {
                'success': True,
                'data': paginated_data,
                'total_count': len(filtered_items),
                'category': category,
                'offset': offset,
                'limit': limit,
                'has_more': len(filtered_items) > offset + limit,
                'mep_id': mep_id,
                'term': term
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to load activities: {str(e)}'
            }
    
    def send_json_response(self, data, status=200):
        """Send JSON response"""
        response_data = json.dumps(data, ensure_ascii=False, indent=2)

        try:
            self.send_response(status)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(response_data.encode('utf-8'))))
            self.end_headers()

            # Write body safely; guard against client aborts (WinError 10053)
            try:
                self.wfile.write(response_data.encode('utf-8'))
            except (ConnectionAbortedError, BrokenPipeError):
                # Client went away; nothing else to do
                pass
        except (ConnectionAbortedError, BrokenPipeError):
            # Client closed connection during headers; ignore
            pass

# Set server to allow address reuse and kill existing processes
socketserver.TCPServer.allow_reuse_address = True
kill_process_on_port(PORT)

print("=" * 60)
print("MEP Score Mobile-Responsive Server")
print("=" * 60)
print(f"Starting server on port {PORT}...")
print(f"Application URL: http://localhost:{PORT}")
print(f"Profile URL: http://localhost:{PORT}/profile.html?mep_id=257011&term=10")
print(f"API Health Check: http://localhost:{PORT}/api/health")
print("\nPress Ctrl+C to stop the server...")
print("=" * 60)

try:
    with socketserver.TCPServer(("", PORT), MEPAPIHandler) as httpd:
        httpd.serve_forever()
except KeyboardInterrupt:
    print("\nServer stopped.")
except Exception as e:
    print(f"Error: {e}")
    input("Press Enter to exit...") 
