#!/usr/bin/env python3
import http.server
import socketserver
import json
import sqlite3
import urllib.parse
from pathlib import Path

PORT = 8001

class AveragesHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Parse URL
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        query_params = urllib.parse.parse_qs(parsed_path.query)
        
        # CORS headers
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        if path == '/api/averages':
            term = int(query_params.get('term', [10])[0])
            result = self.get_averages_from_db(term)
            response = json.dumps(result, ensure_ascii=False)
            self.wfile.write(response.encode('utf-8'))
        else:
            self.wfile.write(json.dumps({'error': 'Endpoint not found'}).encode('utf-8'))
    
    def get_averages_from_db(self, term):
        try:
            conn = sqlite3.connect('data/meps.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Activity fields to calculate averages for
            activity_fields = [
                'speeches', 'amendments', 'reports_rapporteur', 'reports_shadow',
                'questions_written', 'questions_oral', 'motions', 
                'opinions_rapporteur', 'opinions_shadow', 'explanations'
            ]
            
            # Calculate EP averages
            ep_averages = {}
            for field in activity_fields:
                cursor.execute(f'''
                    SELECT AVG(CAST({field} AS FLOAT)) as avg_value
                    FROM activities a 
                    JOIN meps m ON a.mep_id = m.mep_id
                    WHERE a.term = ?
                ''', (term,))
                result = cursor.fetchone()
                ep_averages[field] = result[0] if result[0] is not None else 0
            
            # Add questions total
            ep_averages['questions'] = ep_averages['questions_written']
            
            # Calculate group averages
            group_averages = {}
            cursor.execute('''
                SELECT DISTINCT m.current_party_group_id 
                FROM meps m 
                JOIN activities a ON m.mep_id = a.mep_id 
                WHERE a.term = ? AND m.current_party_group_id IS NOT NULL
            ''', (term,))
            groups = [row[0] for row in cursor.fetchall()]
            
            for group in groups:
                group_averages[group] = {}
                for field in activity_fields:
                    cursor.execute(f'''
                        SELECT AVG(CAST({field} AS FLOAT)) as avg_value
                        FROM activities a 
                        JOIN meps m ON a.mep_id = m.mep_id
                        WHERE a.term = ? AND m.current_party_group_id = ?
                    ''', (term, group))
                    result = cursor.fetchone()
                    group_averages[group][field] = result[0] if result[0] is not None else 0
                
                # Add questions total
                group_averages[group]['questions'] = group_averages[group]['questions_written']
            
            # Calculate country averages
            country_averages = {}
            cursor.execute('''
                SELECT DISTINCT m.country 
                FROM meps m 
                JOIN activities a ON m.mep_id = a.mep_id 
                WHERE a.term = ? AND m.country IS NOT NULL
            ''', (term,))
            countries = [row[0] for row in cursor.fetchall()]
            
            for country in countries:
                country_averages[country] = {}
                for field in activity_fields:
                    cursor.execute(f'''
                        SELECT AVG(CAST({field} AS FLOAT)) as avg_value
                        FROM activities a 
                        JOIN meps m ON a.mep_id = m.mep_id
                        WHERE a.term = ? AND m.country = ?
                    ''', (term, country))
                    result = cursor.fetchone()
                    country_averages[country][field] = result[0] if result[0] is not None else 0
                
                # Add questions total
                country_averages[country]['questions'] = country_averages[country]['questions_written']
            
            conn.close()
            
            return {
                'success': True,
                'data': {
                    'ep': ep_averages,
                    'groups': group_averages,
                    'countries': country_averages
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

if __name__ == '__main__':
    with socketserver.TCPServer(('', PORT), AveragesHandler) as httpd:
        print(f'Averages API server running on port {PORT}')
        httpd.serve_forever()
