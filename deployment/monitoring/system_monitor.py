#!/usr/bin/env python3
"""
MEP Score System Monitoring Script
Comprehensive monitoring with alerts and metrics collection
"""

import psutil
import requests
import json
import time
import sqlite3
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from pathlib import Path
import subprocess
import sys
import os

# Configuration
MONITORING_DB = "/var/log/mepscore/monitoring.db"
LOG_FILE = "/var/log/mepscore/monitoring.log"
ALERT_THRESHOLDS = {
    'cpu_percent': 80,
    'memory_percent': 85,
    'disk_percent': 90,
    'response_time_ms': 2000,
    'error_rate_percent': 5
}

# Email configuration (set via environment variables)
SMTP_SERVER = os.getenv('SMTP_SERVER', 'localhost')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
SMTP_USERNAME = os.getenv('SMTP_USERNAME')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
ALERT_EMAIL = os.getenv('ALERT_EMAIL', 'admin@mepscore.eu')

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('system_monitor')

class SystemMonitor:
    def __init__(self):
        self.setup_database()
        self.last_alert_times = {}
        self.alert_cooldown = timedelta(minutes=30)  # Don't spam alerts
        
    def setup_database(self):
        """Initialize monitoring database"""
        os.makedirs(os.path.dirname(MONITORING_DB), exist_ok=True)
        
        conn = sqlite3.connect(MONITORING_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                cpu_percent REAL,
                memory_percent REAL,
                disk_percent REAL,
                network_sent_mb REAL,
                network_recv_mb REAL,
                response_time_ms REAL,
                api_status INTEGER,
                site_status INTEGER,
                process_count INTEGER,
                load_average REAL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                alert_type TEXT,
                severity TEXT,
                message TEXT,
                resolved BOOLEAN DEFAULT FALSE
            )
        ''')
        
        # Create index for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp)')
        
        conn.commit()
        conn.close()
    
    def collect_system_metrics(self):
        """Collect system performance metrics"""
        try:
            # CPU and memory
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Network
            network = psutil.net_io_counters()
            network_sent_mb = network.bytes_sent / (1024 * 1024)
            network_recv_mb = network.bytes_recv / (1024 * 1024)
            
            # Load average (if available)
            try:
                load_avg = os.getloadavg()[0] if hasattr(os, 'getloadavg') else None
            except:
                load_avg = None
            
            # Process count
            process_count = len(psutil.pids())
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'disk_percent': disk.percent,
                'network_sent_mb': network_sent_mb,
                'network_recv_mb': network_recv_mb,
                'process_count': process_count,
                'load_average': load_avg
            }
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return {}
    
    def check_application_health(self):
        """Check application health endpoints"""
        api_status = 0
        site_status = 0
        response_time = 0
        
        try:
            # Check API health
            start_time = time.time()
            api_response = requests.get('http://localhost:8000/api/health', timeout=10)
            response_time = (time.time() - start_time) * 1000
            
            if api_response.status_code == 200:
                api_status = 1
                api_data = api_response.json()
                if not api_data.get('success', False):
                    api_status = 0
            
        except Exception as e:
            logger.warning(f"API health check failed: {e}")
            api_status = 0
            response_time = 10000  # Timeout
        
        try:
            # Check main site
            site_response = requests.get('https://mepscore.eu/', timeout=10)
            if site_response.status_code == 200:
                site_status = 1
                
        except Exception as e:
            logger.warning(f"Site health check failed: {e}")
            site_status = 0
        
        return {
            'api_status': api_status,
            'site_status': site_status,
            'response_time_ms': response_time
        }
    
    def store_metrics(self, system_metrics, app_metrics):
        """Store metrics in database"""
        try:
            conn = sqlite3.connect(MONITORING_DB)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO metrics (
                    cpu_percent, memory_percent, disk_percent,
                    network_sent_mb, network_recv_mb, response_time_ms,
                    api_status, site_status, process_count, load_average
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                system_metrics.get('cpu_percent'),
                system_metrics.get('memory_percent'),
                system_metrics.get('disk_percent'),
                system_metrics.get('network_sent_mb'),
                system_metrics.get('network_recv_mb'),
                app_metrics.get('response_time_ms'),
                app_metrics.get('api_status'),
                app_metrics.get('site_status'),
                system_metrics.get('process_count'),
                system_metrics.get('load_average')
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error storing metrics: {e}")
    
    def check_alerts(self, system_metrics, app_metrics):
        """Check for alert conditions"""
        alerts = []
        
        # CPU alert
        if system_metrics.get('cpu_percent', 0) > ALERT_THRESHOLDS['cpu_percent']:
            alerts.append({
                'type': 'cpu_high',
                'severity': 'warning',
                'message': f"High CPU usage: {system_metrics['cpu_percent']:.1f}%"
            })
        
        # Memory alert
        if system_metrics.get('memory_percent', 0) > ALERT_THRESHOLDS['memory_percent']:
            alerts.append({
                'type': 'memory_high',
                'severity': 'warning',
                'message': f"High memory usage: {system_metrics['memory_percent']:.1f}%"
            })
        
        # Disk alert
        if system_metrics.get('disk_percent', 0) > ALERT_THRESHOLDS['disk_percent']:
            alerts.append({
                'type': 'disk_high',
                'severity': 'critical',
                'message': f"High disk usage: {system_metrics['disk_percent']:.1f}%"
            })
        
        # API down alert
        if app_metrics.get('api_status', 1) == 0:
            alerts.append({
                'type': 'api_down',
                'severity': 'critical',
                'message': "API is not responding"
            })
        
        # Site down alert
        if app_metrics.get('site_status', 1) == 0:
            alerts.append({
                'type': 'site_down',
                'severity': 'critical',
                'message': "Main site is not responding"
            })
        
        # Response time alert
        if app_metrics.get('response_time_ms', 0) > ALERT_THRESHOLDS['response_time_ms']:
            alerts.append({
                'type': 'slow_response',
                'severity': 'warning',
                'message': f"Slow API response: {app_metrics['response_time_ms']:.0f}ms"
            })
        
        return alerts
    
    def send_alert(self, alert):
        """Send alert via email"""
        if not SMTP_USERNAME or not SMTP_PASSWORD:
            logger.warning("SMTP credentials not configured, skipping email alert")
            return False
        
        # Check cooldown
        alert_key = alert['type']
        now = datetime.now()
        
        if alert_key in self.last_alert_times:
            if now - self.last_alert_times[alert_key] < self.alert_cooldown:
                return False  # Skip due to cooldown
        
        try:
            msg = MIMEMultipart()
            msg['From'] = SMTP_USERNAME
            msg['To'] = ALERT_EMAIL
            msg['Subject'] = f"MEP Score Alert: {alert['severity'].upper()} - {alert['type']}"
            
            body = f"""
MEP Score System Alert

Severity: {alert['severity'].upper()}
Type: {alert['type']}
Time: {now.isoformat()}
Message: {alert['message']}

Please investigate and take appropriate action.

--
MEP Score Monitoring System
"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            text = msg.as_string()
            server.sendmail(SMTP_USERNAME, ALERT_EMAIL, text)
            server.quit()
            
            self.last_alert_times[alert_key] = now
            logger.info(f"Alert sent: {alert['message']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send alert email: {e}")
            return False
    
    def store_alert(self, alert):
        """Store alert in database"""
        try:
            conn = sqlite3.connect(MONITORING_DB)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO alerts (alert_type, severity, message)
                VALUES (?, ?, ?)
            ''', (alert['type'], alert['severity'], alert['message']))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error storing alert: {e}")
    
    def cleanup_old_data(self):
        """Clean up old monitoring data"""
        try:
            conn = sqlite3.connect(MONITORING_DB)
            cursor = conn.cursor()
            
            # Keep only last 30 days of metrics
            cutoff_date = datetime.now() - timedelta(days=30)
            cursor.execute('DELETE FROM metrics WHERE timestamp < ?', (cutoff_date,))
            
            # Keep only last 90 days of alerts
            cutoff_date = datetime.now() - timedelta(days=90)
            cursor.execute('DELETE FROM alerts WHERE timestamp < ?', (cutoff_date,))
            
            conn.commit()
            conn.close()
            
            logger.info("Old monitoring data cleaned up")
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
    
    def get_summary_stats(self):
        """Get summary statistics for the last hour"""
        try:
            conn = sqlite3.connect(MONITORING_DB)
            cursor = conn.cursor()
            
            # Get stats from last hour
            one_hour_ago = datetime.now() - timedelta(hours=1)
            cursor.execute('''
                SELECT 
                    AVG(cpu_percent) as avg_cpu,
                    AVG(memory_percent) as avg_memory,
                    AVG(disk_percent) as avg_disk,
                    AVG(response_time_ms) as avg_response_time,
                    SUM(CASE WHEN api_status = 0 THEN 1 ELSE 0 END) as api_failures,
                    SUM(CASE WHEN site_status = 0 THEN 1 ELSE 0 END) as site_failures,
                    COUNT(*) as total_checks
                FROM metrics 
                WHERE timestamp > ?
            ''', (one_hour_ago,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                api_uptime = ((row[6] - row[4]) / row[6] * 100) if row[6] > 0 else 0
                site_uptime = ((row[6] - row[5]) / row[6] * 100) if row[6] > 0 else 0
                
                return {
                    'avg_cpu': row[0] or 0,
                    'avg_memory': row[1] or 0,
                    'avg_disk': row[2] or 0,
                    'avg_response_time': row[3] or 0,
                    'api_uptime_percent': api_uptime,
                    'site_uptime_percent': site_uptime,
                    'total_checks': row[6] or 0
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Error getting summary stats: {e}")
            return {}
    
    def run_monitoring_cycle(self):
        """Run one complete monitoring cycle"""
        logger.info("Starting monitoring cycle")
        
        # Collect metrics
        system_metrics = self.collect_system_metrics()
        app_metrics = self.check_application_health()
        
        # Store metrics
        self.store_metrics(system_metrics, app_metrics)
        
        # Check for alerts
        alerts = self.check_alerts(system_metrics, app_metrics)
        
        # Process alerts
        for alert in alerts:
            self.store_alert(alert)
            if alert['severity'] == 'critical':
                self.send_alert(alert)
        
        # Log summary
        summary = self.get_summary_stats()
        logger.info(f"Monitoring cycle complete. "
                   f"CPU: {system_metrics.get('cpu_percent', 0):.1f}%, "
                   f"Memory: {system_metrics.get('memory_percent', 0):.1f}%, "
                   f"Disk: {system_metrics.get('disk_percent', 0):.1f}%, "
                   f"API Response: {app_metrics.get('response_time_ms', 0):.0f}ms, "
                   f"Alerts: {len(alerts)}")
        
        return {
            'system_metrics': system_metrics,
            'app_metrics': app_metrics,
            'alerts': alerts,
            'summary': summary
        }

def main():
    """Main monitoring function"""
    monitor = SystemMonitor()
    
    # Run cleanup once per day (check if we should run it)
    if datetime.now().hour == 2 and datetime.now().minute < 5:
        monitor.cleanup_old_data()
    
    # Run monitoring cycle
    results = monitor.run_monitoring_cycle()
    
    # Exit with error code if critical alerts
    critical_alerts = [a for a in results['alerts'] if a['severity'] == 'critical']
    if critical_alerts:
        sys.exit(1)
    
    sys.exit(0)

if __name__ == "__main__":
    main()