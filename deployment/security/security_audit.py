#!/usr/bin/env python3
"""
MEP Score Security Audit Tool
Comprehensive security assessment and vulnerability scanner
"""

import os
import pwd
import grp
import stat
import subprocess
import socket
import ssl
import requests
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import logging
import re
import hashlib
import warnings

# Suppress SSL warnings for self-signed certificates during testing
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

# Configuration
APP_DIR = "/var/www/mepscore"
LOG_FILE = "/var/log/mepscore/security_audit.log"
REPORT_FILE = "/var/log/mepscore/security_audit_report.json"

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('security_audit')

class SecurityAuditor:
    def __init__(self):
        self.findings = []
        self.audit_timestamp = datetime.now()
        
    def add_finding(self, category, severity, description, recommendation=None):
        """Add a security finding"""
        finding = {
            'timestamp': self.audit_timestamp.isoformat(),
            'category': category,
            'severity': severity,  # critical, high, medium, low, info
            'description': description,
            'recommendation': recommendation or "Review and remediate as appropriate"
        }
        self.findings.append(finding)
        
        # Log critical and high severity findings
        if severity in ['critical', 'high']:
            logger.warning(f"[{severity.upper()}] {category}: {description}")
        else:
            logger.info(f"[{severity.upper()}] {category}: {description}")
    
    def audit_file_permissions(self):
        """Audit file and directory permissions"""
        logger.info("Auditing file permissions...")
        
        critical_paths = {
            '/etc/passwd': (0o644, 'root', 'root'),
            '/etc/shadow': (0o640, 'root', 'shadow'),
            '/etc/ssh/sshd_config': (0o644, 'root', 'root'),
            '/var/www/mepscore/data/meps.db': (0o644, 'www-data', 'www-data'),
        }
        
        for path, (expected_mode, expected_owner, expected_group) in critical_paths.items():
            if not os.path.exists(path):
                continue
                
            try:
                st = os.stat(path)
                actual_mode = st.st_mode & 0o777
                actual_owner = pwd.getpwuid(st.st_uid).pw_name
                actual_group = grp.getgrgid(st.st_gid).gr_name
                
                if actual_mode != expected_mode:
                    self.add_finding(
                        'file_permissions',
                        'medium',
                        f"Incorrect permissions on {path}: {oct(actual_mode)} (expected {oct(expected_mode)})",
                        f"chmod {oct(expected_mode)[2:]} {path}"
                    )
                
                if actual_owner != expected_owner:
                    self.add_finding(
                        'file_ownership',
                        'medium',
                        f"Incorrect owner on {path}: {actual_owner} (expected {expected_owner})",
                        f"chown {expected_owner}:{actual_group} {path}"
                    )
                
                if actual_group != expected_group:
                    self.add_finding(
                        'file_ownership',
                        'medium',
                        f"Incorrect group on {path}: {actual_group} (expected {expected_group})",
                        f"chown {actual_owner}:{expected_group} {path}"
                    )
                    
            except (OSError, KeyError) as e:
                self.add_finding(
                    'file_permissions',
                    'low',
                    f"Could not check permissions for {path}: {e}"
                )
        
        # Check for world-writable files in application directory
        if os.path.exists(APP_DIR):
            for root, dirs, files in os.walk(APP_DIR):
                for file in files:
                    filepath = os.path.join(root, file)
                    try:
                        st = os.stat(filepath)
                        if st.st_mode & stat.S_IWOTH:
                            self.add_finding(
                                'file_permissions',
                                'high',
                                f"World-writable file found: {filepath}",
                                f"chmod o-w {filepath}"
                            )
                    except OSError:
                        continue
    
    def audit_services(self):
        """Audit running services and their configuration"""
        logger.info("Auditing services...")
        
        critical_services = ['nginx', 'mepscore', 'fail2ban', 'ufw']
        
        for service in critical_services:
            try:
                result = subprocess.run(
                    ['systemctl', 'is-active', service],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    self.add_finding(
                        'service_status',
                        'high' if service in ['nginx', 'mepscore'] else 'medium',
                        f"Critical service {service} is not running",
                        f"systemctl start {service}"
                    )
                else:
                    self.add_finding(
                        'service_status',
                        'info',
                        f"Service {service} is running normally"
                    )
                    
            except subprocess.SubprocessError as e:
                self.add_finding(
                    'service_status',
                    'low',
                    f"Could not check status of service {service}: {e}"
                )
    
    def audit_network_security(self):
        """Audit network security configuration"""
        logger.info("Auditing network security...")
        
        # Check open ports
        try:
            result = subprocess.run(
                ['netstat', '-tuln'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                open_ports = []
                
                for line in lines:
                    if 'LISTEN' in line:
                        parts = line.split()
                        if len(parts) >= 4:
                            addr_port = parts[3]
                            if ':' in addr_port:
                                port = addr_port.split(':')[-1]
                                open_ports.append(port)
                
                expected_ports = ['22', '80', '443', '8000']  # SSH, HTTP, HTTPS, App
                unexpected_ports = [p for p in open_ports if p not in expected_ports and p.isdigit()]
                
                if unexpected_ports:
                    self.add_finding(
                        'network_security',
                        'medium',
                        f"Unexpected open ports detected: {', '.join(unexpected_ports)}",
                        "Review and close unnecessary ports"
                    )
                
                # Check if dangerous ports are open
                dangerous_ports = ['21', '23', '25', '53', '110', '135', '139', '445', '993', '995']
                open_dangerous = [p for p in open_ports if p in dangerous_ports]
                
                if open_dangerous:
                    self.add_finding(
                        'network_security',
                        'high',
                        f"Potentially dangerous ports are open: {', '.join(open_dangerous)}",
                        "Close unnecessary services and ports"
                    )
                    
        except subprocess.SubprocessError as e:
            self.add_finding(
                'network_security',
                'low',
                f"Could not check open ports: {e}"
            )
        
        # Check firewall status
        try:
            result = subprocess.run(['ufw', 'status'], capture_output=True, text=True)
            if 'Status: active' not in result.stdout:
                self.add_finding(
                    'network_security',
                    'high',
                    "UFW firewall is not active",
                    "ufw --force enable"
                )
        except subprocess.SubprocessError:
            self.add_finding(
                'network_security',
                'medium',
                "Could not check UFW firewall status"
            )
    
    def audit_ssl_configuration(self):
        """Audit SSL/TLS configuration"""
        logger.info("Auditing SSL/TLS configuration...")
        
        domain = "mepscore.eu"
        
        try:
            # Check SSL certificate
            context = ssl.create_default_context()
            
            with socket.create_connection((domain, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    
                    # Check expiration
                    expiry_str = cert['notAfter']
                    expiry_date = datetime.strptime(expiry_str, '%b %d %H:%M:%S %Y %Z')
                    days_until_expiry = (expiry_date - datetime.now()).days
                    
                    if days_until_expiry < 30:
                        self.add_finding(
                            'ssl_security',
                            'high' if days_until_expiry < 7 else 'medium',
                            f"SSL certificate expires in {days_until_expiry} days",
                            "Renew SSL certificate: certbot renew"
                        )
                    else:
                        self.add_finding(
                            'ssl_security',
                            'info',
                            f"SSL certificate is valid for {days_until_expiry} more days"
                        )
                    
                    # Check cipher suites and protocol
                    cipher = ssock.cipher()
                    if cipher:
                        protocol_version = cipher[1]
                        if protocol_version not in ['TLSv1.2', 'TLSv1.3']:
                            self.add_finding(
                                'ssl_security',
                                'high',
                                f"Weak TLS protocol in use: {protocol_version}",
                                "Configure nginx to use only TLS 1.2 and 1.3"
                            )
                            
        except Exception as e:
            self.add_finding(
                'ssl_security',
                'medium',
                f"Could not verify SSL configuration: {e}",
                "Check SSL certificate and configuration manually"
            )
    
    def audit_application_security(self):
        """Audit application-specific security"""
        logger.info("Auditing application security...")
        
        # Check for sensitive files in web directory
        sensitive_patterns = [
            '*.env*', '*.key', '*.pem', '*.p12', '*.pfx',
            'config.*', 'settings.*', '*config*', '*password*'
        ]
        
        if os.path.exists(f"{APP_DIR}/public"):
            for root, dirs, files in os.walk(f"{APP_DIR}/public"):
                for file in files:
                    filepath = os.path.join(root, file)
                    
                    # Check for sensitive file patterns
                    for pattern in sensitive_patterns:
                        if any(p in file.lower() for p in pattern.replace('*', '').split()):
                            if not file.endswith(('.html', '.js', '.css', '.json', '.txt', '.md')):
                                self.add_finding(
                                    'application_security',
                                    'medium',
                                    f"Potentially sensitive file in web directory: {filepath}",
                                    f"Move {filepath} outside web directory or restrict access"
                                )
        
        # Check database file permissions
        db_file = f"{APP_DIR}/data/meps.db"
        if os.path.exists(db_file):
            st = os.stat(db_file)
            if st.st_mode & stat.S_IROTH:
                self.add_finding(
                    'application_security',
                    'high',
                    f"Database file is world-readable: {db_file}",
                    f"chmod 640 {db_file}"
                )
        
        # Check for debug/development settings in production
        config_files = [
            f"{APP_DIR}/serve.py",
            f"{APP_DIR}/deployment/production_serve.py"
        ]
        
        for config_file in config_files:
            if os.path.exists(config_file):
                try:
                    with open(config_file, 'r') as f:
                        content = f.read()
                        
                    if 'debug=True' in content.lower():
                        self.add_finding(
                            'application_security',
                            'high',
                            f"Debug mode enabled in production: {config_file}",
                            "Set debug=False in production configuration"
                        )
                        
                except Exception as e:
                    logger.debug(f"Could not read config file {config_file}: {e}")
    
    def audit_log_security(self):
        """Audit log file security and monitoring"""
        logger.info("Auditing log security...")
        
        log_dirs = ['/var/log/nginx', '/var/log/mepscore']
        
        for log_dir in log_dirs:
            if not os.path.exists(log_dir):
                self.add_finding(
                    'log_security',
                    'medium',
                    f"Log directory does not exist: {log_dir}",
                    f"Create log directory: mkdir -p {log_dir}"
                )
                continue
            
            # Check log directory permissions
            st = os.stat(log_dir)
            if st.st_mode & stat.S_IWOTH:
                self.add_finding(
                    'log_security',
                    'medium',
                    f"Log directory is world-writable: {log_dir}",
                    f"chmod 755 {log_dir}"
                )
            
            # Check for log files with incorrect permissions
            try:
                for log_file in os.listdir(log_dir):
                    log_path = os.path.join(log_dir, log_file)
                    if os.path.isfile(log_path):
                        st = os.stat(log_path)
                        if st.st_mode & stat.S_IROTH:
                            self.add_finding(
                                'log_security',
                                'low',
                                f"Log file is world-readable: {log_path}",
                                f"chmod 640 {log_path}"
                            )
            except OSError as e:
                logger.debug(f"Could not list log directory {log_dir}: {e}")
        
        # Check logrotate configuration
        logrotate_config = "/etc/logrotate.d/mepscore"
        if not os.path.exists(logrotate_config):
            self.add_finding(
                'log_security',
                'medium',
                "Logrotate configuration missing for MEP Score",
                "Configure log rotation to prevent disk space issues"
            )
    
    def audit_system_hardening(self):
        """Audit system hardening measures"""
        logger.info("Auditing system hardening...")
        
        # Check for security updates
        try:
            result = subprocess.run(
                ['apt', 'list', '--upgradable'],
                capture_output=True,
                text=True
            )
            
            if 'security' in result.stdout.lower():
                security_updates = len([line for line in result.stdout.split('\n') 
                                     if 'security' in line.lower()])
                if security_updates > 0:
                    self.add_finding(
                        'system_security',
                        'high',
                        f"{security_updates} security updates available",
                        "apt update && apt upgrade -y"
                    )
                    
        except subprocess.SubprocessError:
            self.add_finding(
                'system_security',
                'low',
                "Could not check for security updates"
            )
        
        # Check SSH configuration
        ssh_config = "/etc/ssh/sshd_config"
        if os.path.exists(ssh_config):
            try:
                with open(ssh_config, 'r') as f:
                    content = f.read()
                
                # Check for insecure SSH settings
                if 'PermitRootLogin yes' in content:
                    self.add_finding(
                        'ssh_security',
                        'critical',
                        "SSH root login is enabled",
                        "Set 'PermitRootLogin no' in sshd_config"
                    )
                
                if 'PasswordAuthentication yes' in content:
                    self.add_finding(
                        'ssh_security',
                        'high',
                        "SSH password authentication is enabled",
                        "Set 'PasswordAuthentication no' in sshd_config"
                    )
                    
            except Exception as e:
                logger.debug(f"Could not read SSH config: {e}")
        
        # Check fail2ban status
        try:
            result = subprocess.run(['fail2ban-client', 'status'], capture_output=True, text=True)
            if result.returncode != 0:
                self.add_finding(
                    'intrusion_detection',
                    'high',
                    "Fail2ban is not running",
                    "systemctl start fail2ban"
                )
            else:
                # Check number of active jails
                jails = re.findall(r'Jail list:\s*(.*)', result.stdout)
                if jails and len(jails[0].split(',')) < 2:
                    self.add_finding(
                        'intrusion_detection',
                        'medium',
                        "Few fail2ban jails active",
                        "Review and enable additional fail2ban jails"
                    )
                    
        except subprocess.SubprocessError:
            self.add_finding(
                'intrusion_detection',
                'medium',
                "Could not check fail2ban status"
            )
    
    def audit_backup_security(self):
        """Audit backup security and availability"""
        logger.info("Auditing backup security...")
        
        backup_dir = "/var/backups/mepscore"
        
        if not os.path.exists(backup_dir):
            self.add_finding(
                'backup_security',
                'high',
                "Backup directory does not exist",
                f"Create backup directory: mkdir -p {backup_dir}"
            )
            return
        
        # Check backup files
        try:
            backups = [f for f in os.listdir(backup_dir) if f.endswith('.tar.gz')]
            if not backups:
                self.add_finding(
                    'backup_security',
                    'medium',
                    "No backup files found",
                    "Ensure backup scripts are running correctly"
                )
            else:
                # Check backup age
                latest_backup = max(backups, key=lambda x: os.path.getctime(os.path.join(backup_dir, x)))
                backup_path = os.path.join(backup_dir, latest_backup)
                backup_age = datetime.now() - datetime.fromtimestamp(os.path.getctime(backup_path))
                
                if backup_age.days > 1:
                    self.add_finding(
                        'backup_security',
                        'medium',
                        f"Latest backup is {backup_age.days} days old",
                        "Check backup automation and schedule"
                    )
                
                # Check backup file permissions
                st = os.stat(backup_path)
                if st.st_mode & stat.S_IROTH:
                    self.add_finding(
                        'backup_security',
                        'medium',
                        f"Backup file is world-readable: {backup_path}",
                        f"chmod 600 {backup_path}"
                    )
                    
        except OSError as e:
            self.add_finding(
                'backup_security',
                'low',
                f"Could not analyze backup files: {e}"
            )
    
    def audit_web_application(self):
        """Audit web application for common vulnerabilities"""
        logger.info("Auditing web application...")
        
        base_url = "https://mepscore.eu"
        
        # Test for common security headers
        try:
            response = requests.get(base_url, timeout=10, verify=False)
            headers = response.headers
            
            security_headers = {
                'Strict-Transport-Security': 'HSTS header missing',
                'X-Frame-Options': 'Clickjacking protection missing',
                'X-Content-Type-Options': 'MIME sniffing protection missing',
                'X-XSS-Protection': 'XSS protection header missing',
                'Content-Security-Policy': 'CSP header missing'
            }
            
            for header, message in security_headers.items():
                if header not in headers:
                    self.add_finding(
                        'web_security',
                        'medium',
                        message,
                        f"Add {header} header to nginx configuration"
                    )
            
            # Check for information disclosure in headers
            info_headers = ['Server', 'X-Powered-By', 'X-AspNet-Version']
            for header in info_headers:
                if header in headers:
                    self.add_finding(
                        'information_disclosure',
                        'low',
                        f"Information disclosure in {header} header: {headers[header]}",
                        f"Remove or obfuscate {header} header"
                    )
                    
        except requests.RequestException as e:
            self.add_finding(
                'web_security',
                'medium',
                f"Could not test web application headers: {e}"
            )
        
        # Test for directory traversal protection
        test_paths = [
            "/../../../etc/passwd",
            "/..\\..\\..\\etc\\passwd",
            "/api/../../../etc/passwd"
        ]
        
        for path in test_paths:
            try:
                response = requests.get(f"{base_url}{path}", timeout=5, verify=False)
                if response.status_code == 200 and 'root:' in response.text:
                    self.add_finding(
                        'web_security',
                        'critical',
                        f"Directory traversal vulnerability detected: {path}",
                        "Implement proper input validation and file access controls"
                    )
            except requests.RequestException:
                continue  # Expected for properly secured applications
    
    def run_audit(self):
        """Run complete security audit"""
        logger.info("Starting comprehensive security audit...")
        
        audit_methods = [
            self.audit_file_permissions,
            self.audit_services,
            self.audit_network_security,
            self.audit_ssl_configuration,
            self.audit_application_security,
            self.audit_log_security,
            self.audit_system_hardening,
            self.audit_backup_security,
            self.audit_web_application
        ]
        
        for method in audit_methods:
            try:
                method()
            except Exception as e:
                logger.error(f"Error in {method.__name__}: {e}")
                self.add_finding(
                    'audit_error',
                    'low',
                    f"Error during {method.__name__}: {e}"
                )
        
        return self.generate_report()
    
    def generate_report(self):
        """Generate security audit report"""
        logger.info("Generating security audit report...")
        
        # Categorize findings by severity
        severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'info': 0}
        for finding in self.findings:
            severity_counts[finding['severity']] += 1
        
        # Calculate security score (0-100, higher is better)
        total_issues = sum(severity_counts.values()) - severity_counts['info']
        if total_issues == 0:
            security_score = 100
        else:
            # Weight different severities
            weighted_score = (
                severity_counts['critical'] * 10 +
                severity_counts['high'] * 5 +
                severity_counts['medium'] * 2 +
                severity_counts['low'] * 1
            )
            security_score = max(0, 100 - weighted_score)
        
        report = {
            'audit_timestamp': self.audit_timestamp.isoformat(),
            'security_score': security_score,
            'severity_counts': severity_counts,
            'findings': self.findings,
            'summary': {
                'total_findings': len(self.findings),
                'critical_issues': severity_counts['critical'],
                'high_issues': severity_counts['high'],
                'medium_issues': severity_counts['medium'],
                'low_issues': severity_counts['low'],
                'info_items': severity_counts['info']
            }
        }
        
        # Save report to file
        try:
            os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)
            with open(REPORT_FILE, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Security audit report saved to {REPORT_FILE}")
        except Exception as e:
            logger.error(f"Could not save report: {e}")
        
        return report

def main():
    """Main audit function"""
    print("MEP Score Security Audit Tool")
    print("=" * 50)
    
    auditor = SecurityAuditor()
    report = auditor.run_audit()
    
    # Print summary
    print(f"\nSecurity Audit Complete")
    print(f"Security Score: {report['security_score']}/100")
    print(f"Total Findings: {report['summary']['total_findings']}")
    print(f"Critical Issues: {report['summary']['critical_issues']}")
    print(f"High Issues: {report['summary']['high_issues']}")
    print(f"Medium Issues: {report['summary']['medium_issues']}")
    print(f"Low Issues: {report['summary']['low_issues']}")
    
    # Print critical and high issues
    critical_high = [f for f in report['findings'] 
                    if f['severity'] in ['critical', 'high']]
    
    if critical_high:
        print(f"\nCritical and High Priority Issues:")
        print("-" * 40)
        for finding in critical_high:
            print(f"[{finding['severity'].upper()}] {finding['category']}")
            print(f"  {finding['description']}")
            if finding['recommendation']:
                print(f"  → {finding['recommendation']}")
            print()
    
    print(f"\nFull report available at: {REPORT_FILE}")
    
    # Exit with error code if critical issues found
    if report['summary']['critical_issues'] > 0:
        return 2
    elif report['summary']['high_issues'] > 0:
        return 1
    else:
        return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())