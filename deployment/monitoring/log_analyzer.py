#!/usr/bin/env python3
"""
MEP Score Log Analyzer
Analyzes access logs and generates insights and alerts
"""

import re
import geoip2.database
import geoip2.errors
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from pathlib import Path
import json
import logging
import sqlite3
import os
import subprocess

# Configuration
ACCESS_LOG = "/var/log/nginx/mepscore_access.log"
ERROR_LOG = "/var/log/nginx/mepscore_error.log"
ANALYSIS_DB = "/var/log/mepscore/log_analysis.db"
GEOIP_DB = "/usr/share/GeoIP/GeoLite2-City.mmdb"

# Alert thresholds
THRESHOLDS = {
    'high_error_rate': 5.0,  # % of 4xx/5xx responses
    'high_bandwidth': 1000,  # MB per hour
    'suspicious_requests': 50,  # requests per minute from single IP
    'bot_requests': 1000,  # requests per hour from bots
}

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('log_analyzer')

class LogAnalyzer:
    def __init__(self):
        self.setup_database()
        self.geoip_reader = self.setup_geoip()
        
        # Regex patterns for log parsing
        self.access_pattern = re.compile(
            r'(?P<ip>\S+) - (?P<user>\S+) \[(?P<timestamp>[^\]]+)\] '
            r'"(?P<method>\S+) (?P<url>\S+) (?P<protocol>\S+)" '
            r'(?P<status>\d+) (?P<bytes>\d+) "(?P<referer>[^"]*)" '
            r'"(?P<user_agent>[^"]*)" "(?P<forwarded_for>[^"]*)" '
            r'rt=(?P<request_time>\S+) uct="(?P<upstream_connect>[^"]*)" '
            r'uht="(?P<upstream_header>[^"]*)" urt="(?P<upstream_response>[^"]*)"'
        )
        
        self.bot_patterns = [
            r'bot', r'spider', r'crawler', r'scraper', r'facebookexternalhit',
            r'twitterbot', r'linkedinbot', r'whatsapp', r'telegrambot',
            r'googlebot', r'bingbot', r'yandexbot', r'baiduspider'
        ]
        self.bot_regex = re.compile('|'.join(self.bot_patterns), re.IGNORECASE)
    
    def setup_database(self):
        """Initialize analysis database"""
        os.makedirs(os.path.dirname(ANALYSIS_DB), exist_ok=True)
        
        conn = sqlite3.connect(ANALYSIS_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS access_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hour_timestamp DATETIME,
                total_requests INTEGER,
                unique_ips INTEGER,
                status_2xx INTEGER,
                status_3xx INTEGER,
                status_4xx INTEGER,
                status_5xx INTEGER,
                total_bytes INTEGER,
                avg_response_time REAL,
                top_pages TEXT,
                top_referers TEXT,
                top_user_agents TEXT,
                bot_requests INTEGER,
                suspicious_ips TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS geo_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE,
                country_code TEXT,
                country_name TEXT,
                city TEXT,
                requests INTEGER,
                bytes INTEGER
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS security_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT,
                ip_address TEXT,
                details TEXT,
                severity TEXT
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_access_hour ON access_summary(hour_timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_geo_date ON geo_summary(date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_security_timestamp ON security_events(timestamp)')
        
        conn.commit()
        conn.close()
    
    def setup_geoip(self):
        """Setup GeoIP database reader"""
        try:
            if Path(GEOIP_DB).exists():
                return geoip2.database.Reader(GEOIP_DB)
            else:
                logger.warning("GeoIP database not found")
                return None
        except Exception as e:
            logger.error(f"Error setting up GeoIP: {e}")
            return None
    
    def get_country_info(self, ip):
        """Get country information for IP address"""
        if not self.geoip_reader:
            return None, None, None
        
        try:
            response = self.geoip_reader.city(ip)
            return (
                response.country.iso_code,
                response.country.name,
                response.city.name
            )
        except geoip2.errors.AddressNotFoundError:
            return None, None, None
        except Exception as e:
            logger.debug(f"GeoIP lookup failed for {ip}: {e}")
            return None, None, None
    
    def parse_access_logs(self, hours_back=1):
        """Parse access logs for the specified time period"""
        if not Path(ACCESS_LOG).exists():
            logger.error(f"Access log file not found: {ACCESS_LOG}")
            return []
        
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        entries = []
        
        try:
            with open(ACCESS_LOG, 'r') as f:
                for line in f:
                    match = self.access_pattern.match(line.strip())
                    if match:
                        data = match.groupdict()
                        
                        # Parse timestamp
                        try:
                            timestamp = datetime.strptime(data['timestamp'], '%d/%b/%Y:%H:%M:%S %z')
                            # Convert to naive datetime (remove timezone info for comparison)
                            timestamp = timestamp.replace(tzinfo=None)
                        except ValueError:
                            continue
                        
                        # Filter by time
                        if timestamp < cutoff_time:
                            continue
                        
                        # Clean and convert data types
                        try:
                            data['status'] = int(data['status'])
                            data['bytes'] = int(data['bytes']) if data['bytes'] != '-' else 0
                            data['request_time'] = float(data['request_time']) if data['request_time'] != '-' else 0
                            data['timestamp'] = timestamp
                            
                            entries.append(data)
                        except (ValueError, TypeError):
                            continue
            
        except Exception as e:
            logger.error(f"Error parsing access logs: {e}")
        
        return entries
    
    def analyze_entries(self, entries):
        """Analyze parsed log entries"""
        if not entries:
            return {}
        
        # Basic statistics
        total_requests = len(entries)
        unique_ips = len(set(entry['ip'] for entry in entries))
        
        # Status code analysis
        status_counts = Counter(entry['status'] // 100 * 100 for entry in entries)
        
        # Bandwidth analysis
        total_bytes = sum(entry['bytes'] for entry in entries)
        
        # Response time analysis
        response_times = [entry['request_time'] for entry in entries if entry['request_time'] > 0]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Top pages
        page_counts = Counter(entry['url'] for entry in entries)
        top_pages = dict(page_counts.most_common(10))
        
        # Top referers
        referer_counts = Counter(entry['referer'] for entry in entries if entry['referer'] != '-')
        top_referers = dict(referer_counts.most_common(10))
        
        # Top user agents
        ua_counts = Counter(entry['user_agent'] for entry in entries)
        top_user_agents = dict(ua_counts.most_common(10))
        
        # Bot detection
        bot_requests = sum(1 for entry in entries if self.bot_regex.search(entry['user_agent']))
        
        # Suspicious activity detection
        ip_request_counts = Counter(entry['ip'] for entry in entries)
        suspicious_ips = {ip: count for ip, count in ip_request_counts.items() 
                         if count > THRESHOLDS['suspicious_requests']}
        
        # Geographic analysis
        geo_data = defaultdict(lambda: {'requests': 0, 'bytes': 0})
        for entry in entries:
            country_code, country_name, city = self.get_country_info(entry['ip'])
            if country_code:
                key = f"{country_code}|{country_name}|{city or 'Unknown'}"
                geo_data[key]['requests'] += 1
                geo_data[key]['bytes'] += entry['bytes']
        
        return {
            'total_requests': total_requests,
            'unique_ips': unique_ips,
            'status_2xx': status_counts.get(200, 0),
            'status_3xx': status_counts.get(300, 0),
            'status_4xx': status_counts.get(400, 0),
            'status_5xx': status_counts.get(500, 0),
            'total_bytes': total_bytes,
            'avg_response_time': avg_response_time,
            'top_pages': top_pages,
            'top_referers': top_referers,
            'top_user_agents': top_user_agents,
            'bot_requests': bot_requests,
            'suspicious_ips': suspicious_ips,
            'geo_data': dict(geo_data)
        }
    
    def store_analysis(self, analysis, hour_timestamp):
        """Store analysis results in database"""
        try:
            conn = sqlite3.connect(ANALYSIS_DB)
            cursor = conn.cursor()
            
            # Store hourly summary
            cursor.execute('''
                INSERT OR REPLACE INTO access_summary (
                    hour_timestamp, total_requests, unique_ips,
                    status_2xx, status_3xx, status_4xx, status_5xx,
                    total_bytes, avg_response_time, top_pages,
                    top_referers, top_user_agents, bot_requests, suspicious_ips
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                hour_timestamp,
                analysis['total_requests'],
                analysis['unique_ips'],
                analysis['status_2xx'],
                analysis['status_3xx'],
                analysis['status_4xx'],
                analysis['status_5xx'],
                analysis['total_bytes'],
                analysis['avg_response_time'],
                json.dumps(analysis['top_pages']),
                json.dumps(analysis['top_referers']),
                json.dumps(analysis['top_user_agents']),
                analysis['bot_requests'],
                json.dumps(analysis['suspicious_ips'])
            ))
            
            # Store geographic data
            date_str = hour_timestamp.date()
            for geo_key, geo_stats in analysis['geo_data'].items():
                parts = geo_key.split('|')
                country_code, country_name, city = parts[0], parts[1], parts[2]
                
                cursor.execute('''
                    INSERT OR IGNORE INTO geo_summary (
                        date, country_code, country_name, city, requests, bytes
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (date_str, country_code, country_name, city, 
                      geo_stats['requests'], geo_stats['bytes']))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error storing analysis: {e}")
    
    def check_security_events(self, analysis):
        """Check for security events and alerts"""
        events = []
        
        # High error rate
        total_requests = analysis['total_requests']
        if total_requests > 0:
            error_rate = (analysis['status_4xx'] + analysis['status_5xx']) / total_requests * 100
            if error_rate > THRESHOLDS['high_error_rate']:
                events.append({
                    'type': 'high_error_rate',
                    'severity': 'warning',
                    'details': f"Error rate: {error_rate:.1f}% ({analysis['status_4xx'] + analysis['status_5xx']} errors in {total_requests} requests)"
                })
        
        # High bandwidth usage
        bandwidth_mb = analysis['total_bytes'] / (1024 * 1024)
        if bandwidth_mb > THRESHOLDS['high_bandwidth']:
            events.append({
                'type': 'high_bandwidth',
                'severity': 'info',
                'details': f"High bandwidth usage: {bandwidth_mb:.1f} MB in last hour"
            })
        
        # Suspicious IPs
        for ip, count in analysis['suspicious_ips'].items():
            events.append({
                'type': 'suspicious_activity',
                'severity': 'warning',
                'ip_address': ip,
                'details': f"High request rate: {count} requests in last hour"
            })
        
        # High bot traffic
        if analysis['bot_requests'] > THRESHOLDS['bot_requests']:
            events.append({
                'type': 'high_bot_traffic',
                'severity': 'info',
                'details': f"High bot traffic: {analysis['bot_requests']} bot requests in last hour"
            })
        
        return events
    
    def store_security_events(self, events):
        """Store security events in database"""
        try:
            conn = sqlite3.connect(ANALYSIS_DB)
            cursor = conn.cursor()
            
            for event in events:
                cursor.execute('''
                    INSERT INTO security_events (event_type, ip_address, details, severity)
                    VALUES (?, ?, ?, ?)
                ''', (
                    event['type'],
                    event.get('ip_address'),
                    event['details'],
                    event['severity']
                ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error storing security events: {e}")
    
    def generate_report(self, analysis):
        """Generate human-readable report"""
        total_mb = analysis['total_bytes'] / (1024 * 1024)
        error_rate = 0
        
        if analysis['total_requests'] > 0:
            error_rate = (analysis['status_4xx'] + analysis['status_5xx']) / analysis['total_requests'] * 100
        
        report = f"""
MEP Score Access Log Analysis - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
================================================================

Traffic Summary (Last Hour):
- Total Requests: {analysis['total_requests']:,}
- Unique Visitors: {analysis['unique_ips']:,}
- Data Transfer: {total_mb:.2f} MB
- Avg Response Time: {analysis['avg_response_time']:.3f}s
- Error Rate: {error_rate:.2f}%

Status Code Breakdown:
- 2xx (Success): {analysis['status_2xx']:,} ({analysis['status_2xx']/analysis['total_requests']*100:.1f}%)
- 3xx (Redirect): {analysis['status_3xx']:,} ({analysis['status_3xx']/analysis['total_requests']*100:.1f}%)
- 4xx (Client Error): {analysis['status_4xx']:,} ({analysis['status_4xx']/analysis['total_requests']*100:.1f}%)
- 5xx (Server Error): {analysis['status_5xx']:,} ({analysis['status_5xx']/analysis['total_requests']*100:.1f}%)

Bot Traffic:
- Bot Requests: {analysis['bot_requests']:,} ({analysis['bot_requests']/analysis['total_requests']*100:.1f}%)

Top Pages:
"""
        
        for page, count in list(analysis['top_pages'].items())[:5]:
            report += f"- {page}: {count:,} requests\n"
        
        if analysis['suspicious_ips']:
            report += "\nSuspicious Activity:\n"
            for ip, count in analysis['suspicious_ips'].items():
                report += f"- {ip}: {count:,} requests\n"
        
        return report
    
    def run_analysis(self):
        """Run complete log analysis"""
        logger.info("Starting log analysis")
        
        # Parse logs for last hour
        entries = self.parse_access_logs(hours_back=1)
        
        if not entries:
            logger.warning("No log entries found for analysis")
            return
        
        # Analyze entries
        analysis = self.analyze_entries(entries)
        
        # Store results
        hour_timestamp = datetime.now().replace(minute=0, second=0, microsecond=0)
        self.store_analysis(analysis, hour_timestamp)
        
        # Check for security events
        security_events = self.check_security_events(analysis)
        if security_events:
            self.store_security_events(security_events)
            logger.warning(f"Found {len(security_events)} security events")
        
        # Generate and log report
        report = self.generate_report(analysis)
        logger.info(f"Analysis complete: {analysis['total_requests']} requests, {analysis['unique_ips']} unique IPs")
        
        return {
            'analysis': analysis,
            'security_events': security_events,
            'report': report
        }

def main():
    """Main analysis function"""
    analyzer = LogAnalyzer()
    results = analyzer.run_analysis()
    
    if results and results['security_events']:
        # Exit with warning code if security events found
        sys.exit(1)
    
    sys.exit(0)

if __name__ == "__main__":
    import sys
    main()