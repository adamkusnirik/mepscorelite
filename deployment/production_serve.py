#!/usr/bin/env python3
"""
MEP Score Professional Production Server
High-performance, monitoring-enabled production server with logging and health checks
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
import logging
import signal
import sys
import time
import threading
from pathlib import Path
from logging.handlers import RotatingFileHandler
import psutil
from functools import lru_cache

# Configuration
PORT = 8000
DIRECTORY = "public"
LOG_DIR = "/var/log/mepscore"
HEALTH_CHECK_INTERVAL = 60  # seconds

# Data caching configuration
DATA_CACHE = {}
CACHE_LOCK = threading.Lock()
CACHE_TTL = 3600  # 1 hour cache TTL
LAST_CACHE_CLEANUP = time.time()

# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

# Configure logging
class ColoredFormatter(logging.Formatter):
    """Colored log formatter for console output"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, '')
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)

# Set up logging
logger = logging.getLogger('mepscore')
logger.setLevel(logging.INFO)

# File handler with rotation
file_handler = RotatingFileHandler(
    os.path.join(LOG_DIR, 'application.log'),
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
file_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
file_handler.setFormatter(file_formatter)

# Console handler with colors
console_handler = logging.StreamHandler()
console_formatter = ColoredFormatter(
    '%(asctime)s - %(levelname)s - %(message)s'
)
console_handler.setFormatter(console_formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Performance monitoring
class PerformanceMonitor:
    def __init__(self):
        self.request_count = 0
        self.start_time = time.time()
        self.response_times = []
        self.error_count = 0
        
    def log_request(self, response_time, status_code):
        self.request_count += 1
        self.response_times.append(response_time)
        if status_code >= 400:
            self.error_count += 1
            
        # Keep only last 1000 response times
        if len(self.response_times) > 1000:
            self.response_times = self.response_times[-1000:]
    
    def get_stats(self):
        uptime = time.time() - self.start_time
        avg_response_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0
        
        return {
            'uptime_seconds': uptime,
            'total_requests': self.request_count,
            'error_count': self.error_count,
            'error_rate': (self.error_count / self.request_count * 100) if self.request_count > 0 else 0,
            'avg_response_time_ms': avg_response_time * 1000,
            'requests_per_second': self.request_count / uptime if uptime > 0 else 0
        }

performance_monitor = PerformanceMonitor()

class OptimizedDataLoader:
    """Optimized data loader for split JSON files with caching and production monitoring"""
    
    @staticmethod
    def get_cache_key(file_type: str, term: int) -> str:
        """Generate cache key for data"""
        return f"{file_type}_term{term}"
    
    @staticmethod
    def cleanup_cache():
        """Remove expired cache entries"""
        global LAST_CACHE_CLEANUP
        current_time = time.time()
        
        if current_time - LAST_CACHE_CLEANUP < 300:  # Cleanup every 5 minutes
            return
        
        with CACHE_LOCK:
            expired_keys = []
            for key, (data, timestamp) in DATA_CACHE.items():
                if current_time - timestamp > CACHE_TTL:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del DATA_CACHE[key]
            
            LAST_CACHE_CLEANUP = current_time
            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    @staticmethod
    def load_json_data(file_path: Path) -> dict:
        """Load JSON data with caching and monitoring"""
        cache_key = f"file_{file_path.name}_{file_path.stat().st_mtime}"
        current_time = time.time()
        
        # Check cache first
        with CACHE_LOCK:
            if cache_key in DATA_CACHE:
                data, timestamp = DATA_CACHE[cache_key]
                if current_time - timestamp < CACHE_TTL:
                    logger.debug(f"Cache hit for {file_path.name}")
                    return data
        
        # Load from file
        load_start = time.time()
        logger.info(f"Loading data from {file_path.name}...")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            load_time = time.time() - load_start
            data_size = len(data) if isinstance(data, list) else 'N/A'
            
            # Cache the data
            with CACHE_LOCK:
                DATA_CACHE[cache_key] = (data, current_time)
                
            logger.info(f"Loaded {file_path.name} - {data_size} records in {load_time:.2f}s")
            return data
            
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            raise
    
    @staticmethod
    def get_optimized_file_path(file_type: str, term: int) -> Path:
        """Get the path to optimized split file with fallback logic"""
        base_dir = Path("data/parltrack")
        
        # Try optimized term-specific file first
        optimized_path = base_dir / f"ep_{file_type}_term{term}.json"
        if optimized_path.exists():
            logger.debug(f"Using optimized file: {optimized_path.name}")
            return optimized_path
        
        # Fallback to legacy term-specific files
        if file_type == "mep_activities":
            if term == 8:
                legacy_path = base_dir / "8th term" / "ep_mep_activities-2019-07-03.json(2)"
                if legacy_path.exists():
                    logger.warning(f"Using legacy file: {legacy_path}")
                    return legacy_path
                legacy_path = base_dir / "8th term" / "ep_mep_activities-2019-07-03.json"
                if legacy_path.exists():
                    logger.warning(f"Using legacy file: {legacy_path}")
                    return legacy_path
            elif term == 9:
                legacy_path = base_dir / "9th term" / "ep_mep_activities-2024-07-02.json"
                if legacy_path.exists():
                    logger.warning(f"Using legacy file: {legacy_path}")
                    return legacy_path
        
        # Final fallback to original files (requires term filtering)
        original_path = base_dir / f"ep_{file_type}.json"
        if original_path.exists():
            logger.warning(f"Using original unoptimized file: {original_path.name} (requires term filtering)")
            return original_path
        
        raise FileNotFoundError(f"No data file found for {file_type} term {term}")

def kill_process_on_port(port):
    """Kill any process using the specified port"""
    if platform.system() == "Windows":
        try:
            command = f"netstat -aon | findstr :{port}"
            result = subprocess.run(command, capture_output=True, text=True, shell=True, check=True)
            for line in result.stdout.strip().split('\n'):
                if "LISTENING" in line:
                    parts = line.split()
                    pid = parts[-1]
                    if pid.isdigit():
                        logger.info(f"Killing process {pid} using port {port}")
                        subprocess.run(f"taskkill /PID {pid} /F", shell=True, check=True)
                        return
        except subprocess.CalledProcessError as e:
            if "findstr" not in str(e.cmd) or e.returncode != 1:
                logger.warning(f"Failed to kill process on port {port}: {e}")
    else:
        try:
            # Linux/Unix
            result = subprocess.run(['lsof', '-ti', f':{port}'], capture_output=True, text=True)
            if result.stdout:
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid:
                        logger.info(f"Killing process {pid} using port {port}")
                        os.kill(int(pid), signal.SIGTERM)
        except Exception as e:
            logger.warning(f"Failed to kill process on port {port}: {e}")

class MEPProductionAPIHandler(http.server.SimpleHTTPRequestHandler):
    """Enhanced production API handler with monitoring and logging"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def log_message(self, format, *args):
        """Override default logging to use our logger"""
        logger.info(f"{self.client_address[0]} - {format % args}")
    
    def translate_path(self, path):
        """Override to serve files from project root for parltrack data and logos"""
        if path.startswith('/data/parltrack/'):
            return path[1:]
        if path.startswith('/logos/'):
            return path[1:]
        return super().translate_path(path)

    def do_GET(self):
        """Handle GET requests with timing and monitoring"""
        start_time = time.time()
        
        try:
            parsed_path = urllib.parse.urlparse(self.path)
            path = parsed_path.path
            query_params = urllib.parse.parse_qs(parsed_path.query)
            
            # Handle API endpoints
            if path.startswith('/api/'):
                self.handle_api_request(path, query_params)
            else:
                # Serve static files
                super().do_GET()
                
        except Exception as e:
            logger.error(f"Error handling GET request for {self.path}: {e}")
            self.send_error(500, f"Internal server error: {str(e)}")
        finally:
            response_time = time.time() - start_time
            # Get status code from the response if available
            status_code = getattr(self, '_status_code', 200)
            performance_monitor.log_request(response_time, status_code)
    
    def send_error(self, code, message=None, explain=None):
        """Override to track status codes"""
        self._status_code = code
        super().send_error(code, message, explain)
    
    def send_response(self, code, message=None):
        """Override to track status codes"""
        self._status_code = code
        super().send_response(code, message)
    
    def handle_api_request(self, path, query_params):
        """Handle API endpoints with enhanced monitoring"""
        try:
            # Health check endpoint with system metrics
            if path == '/api/health':
                system_stats = {
                    'cpu_percent': psutil.cpu_percent(interval=1),
                    'memory_percent': psutil.virtual_memory().percent,
                    'disk_percent': psutil.disk_usage('/').percent,
                    'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else None
                }
                
                result = {
                    'success': True,
                    'status': 'Production server is running',
                    'timestamp': dt.datetime.now().isoformat(),
                    'system': system_stats,
                    'performance': performance_monitor.get_stats(),
                    'version': '2.0.0'
                }
                self.send_json_response(result)
                return
            
            # Performance metrics endpoint
            if path == '/api/metrics':
                result = {
                    'success': True,
                    'metrics': performance_monitor.get_stats(),
                    'timestamp': dt.datetime.now().isoformat()
                }
                self.send_json_response(result)
                return
            
            # MEP category details endpoint
            if path.startswith('/api/mep/') and '/category/' in path:
                parts = path.split('/')
                if len(parts) >= 5:
                    mep_id = int(parts[3])
                    category = parts[5]
                    term = int(query_params.get('term', [10])[0])
                    offset = int(query_params.get('offset', [0])[0])
                    limit = int(query_params.get('limit', [15])[0])
                    
                    logger.info(f"API Request: MEP {mep_id}, Category: {category}, Term: {term}")
                    result = self.get_mep_category_data(mep_id, category, term, offset, limit)
                    self.send_json_response(result)
                    return
            
            # Default 404 for unknown API endpoints
            self.send_error(404, "API endpoint not found")
            
        except Exception as e:
            logger.error(f"API Error for {path}: {e}", exc_info=True)
            error_response = {
                'success': False,
                'error': str(e),
                'timestamp': dt.datetime.now().isoformat()
            }
            self.send_json_response(error_response, status=500)
    
    def get_mep_category_data(self, mep_id, category, term, offset, limit):
        """Get data for a specific MEP category - same as original but with enhanced error handling"""
        try:
            # Database connection with timeout
            conn = sqlite3.connect('data/meps.db', timeout=10.0)
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
                conn.close()
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
            logger.error(f"Error processing category {category} for MEP {mep_id}: {e}")
            return {
                'success': False,
                'error': f'Error reading data: {str(e)}'
            }
    
    def get_amendments_detailed(self, mep_id, term, offset, limit, total_count):
        """Get detailed amendments data using optimized loading"""
        try:
            # Cleanup expired cache entries
            OptimizedDataLoader.cleanup_cache()
            
            # Get optimized file path with fallback
            amendments_file = OptimizedDataLoader.get_optimized_file_path("amendments", term)
            
            # Load data with caching
            all_amendments = OptimizedDataLoader.load_json_data(amendments_file)

            # Find MEP's amendments
            mep_amendments = []
            is_optimized_file = amendments_file.name.startswith('ep_amendments_term')
            
            for amend in all_amendments:
                if mep_id in amend.get('meps', []):
                    if is_optimized_file:
                        # Optimized files are already filtered by term
                        mep_amendments.append(amend)
                    else:
                        # Original file needs term filtering
                        amend_date = amend.get('date', '')
                        if amend_date:
                            try:
                                if 'T' in amend_date:
                                    date_obj = dt.datetime.fromisoformat(amend_date.replace('T', ' ').replace('Z', ''))
                                else:
                                    date_obj = dt.datetime.fromisoformat(amend_date)

                                # Filter by term dates
                                if term == 8:
                                    if dt.datetime(2014, 7, 1) <= date_obj < dt.datetime(2019, 7, 2):
                                        mep_amendments.append(amend)
                                elif term == 9:
                                    if dt.datetime(2019, 7, 2) <= date_obj < dt.datetime(2024, 7, 16):
                                        mep_amendments.append(amend)
                                elif term == 10:
                                    if dt.datetime(2024, 7, 16) <= date_obj:
                                        mep_amendments.append(amend)
                            except (ValueError, TypeError) as e:
                                logger.debug(f"Invalid date format in amendment: {amend_date}: {e}")
                                continue

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
                'term': term,
                'data_source': amendments_file.name
            }

        except FileNotFoundError as e:
            logger.error(f"Amendments data file not found for term {term}: {e}")
            return {
                'success': False,
                'error': f'Amendments data file not found for term {term}'
            }
        except Exception as e:
            logger.error(f"Failed to load amendments for MEP {mep_id}: {e}", exc_info=True)
            return {
                'success': False,
                'error': f'Failed to load amendments: {str(e)}'
            }

    def get_activities_detailed(self, mep_id, category, term, offset, limit, total_count):
        """Get detailed activities data using optimized loading"""
        try:
            # Cleanup expired cache entries
            OptimizedDataLoader.cleanup_cache()
            
            # Get optimized file path with fallback
            activities_file = OptimizedDataLoader.get_optimized_file_path("mep_activities", term)
            
            # Load data with caching
            data = OptimizedDataLoader.load_json_data(activities_file)

            # Find MEP's activities
            mep_activities = None
            for mep_data in data:
                if mep_data.get('mep_id') == mep_id:
                    mep_activities = mep_data
                    break

            if not mep_activities:
                return {
                    'success': False,
                    'error': f'MEP {mep_id} not found in activities data'
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
                'term': term,
                'data_source': activities_file.name
            }

        except FileNotFoundError as e:
            logger.error(f"Activities data file not found for term {term}: {e}")
            return {
                'success': False,
                'error': f'Activities data file not found for term {term}'
            }
        except Exception as e:
            logger.error(f"Failed to load activities for MEP {mep_id}, category {category}: {e}", exc_info=True)
            return {
                'success': False,
                'error': f'Failed to load activities: {str(e)}'
            }
    
    def send_json_response(self, data, status=200):
        """Send JSON response with proper error handling"""
        response_data = json.dumps(data, ensure_ascii=False, indent=2)

        try:
            self.send_response(status)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.send_header('Content-Length', str(len(response_data.encode('utf-8'))))
            
            # Security headers
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('X-Frame-Options', 'DENY')
            self.send_header('X-XSS-Protection', '1; mode=block')
            
            self.end_headers()

            # Write body safely
            try:
                self.wfile.write(response_data.encode('utf-8'))
            except (ConnectionAbortedError, BrokenPipeError):
                logger.debug("Client disconnected during response")
        except (ConnectionAbortedError, BrokenPipeError):
            logger.debug("Client disconnected during headers")

def signal_handler(signum, frame):
    """Graceful shutdown handler"""
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    sys.exit(0)

def health_monitor():
    """Background thread for health monitoring"""
    while True:
        try:
            # Log system stats every minute
            stats = performance_monitor.get_stats()
            logger.info(f"Performance: {stats['requests_per_second']:.2f} req/s, "
                       f"avg response: {stats['avg_response_time_ms']:.2f}ms, "
                       f"error rate: {stats['error_rate']:.2f}%")
            
            # Check system resources
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory().percent
            disk_percent = psutil.disk_usage('/').percent
            
            if cpu_percent > 80:
                logger.warning(f"High CPU usage: {cpu_percent}%")
            if memory_percent > 80:
                logger.warning(f"High memory usage: {memory_percent}%")
            if disk_percent > 80:
                logger.warning(f"High disk usage: {disk_percent}%")
            
        except Exception as e:
            logger.error(f"Health monitor error: {e}")
        
        time.sleep(HEALTH_CHECK_INTERVAL)

def main():
    """Main server function"""
    # Set up signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Kill existing processes
    kill_process_on_port(PORT)
    
    logger.info("=" * 60)
    logger.info("MEP Score Professional Production Server")
    logger.info("=" * 60)
    logger.info(f"Starting production server on port {PORT}...")
    logger.info(f"Log directory: {LOG_DIR}")
    logger.info(f"Health check interval: {HEALTH_CHECK_INTERVAL}s")
    logger.info(f"API Health Check: http://localhost:{PORT}/api/health")
    logger.info(f"Performance Metrics: http://localhost:{PORT}/api/metrics")
    logger.info("\nPress Ctrl+C to stop the server...")
    logger.info("=" * 60)
    
    # Start health monitoring thread
    health_thread = threading.Thread(target=health_monitor, daemon=True)
    health_thread.start()
    
    # Configure server
    socketserver.TCPServer.allow_reuse_address = True
    
    try:
        with socketserver.TCPServer(("", PORT), MEPProductionAPIHandler) as httpd:
            logger.info("Production server is ready and accepting connections")
            httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
    finally:
        logger.info("Server shutdown complete")

if __name__ == "__main__":
    main()