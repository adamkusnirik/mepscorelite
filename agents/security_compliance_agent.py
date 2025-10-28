"""
Security & Compliance Agent - Maintains security and data protection standards

This agent handles security vulnerability scanning, GDPR compliance,
access control, and security best practices enforcement.
"""

import asyncio
import json
import hashlib
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import sqlite3

from .base_agent import BaseAgent, TaskResult, AgentCapability


class SecurityComplianceAgent(BaseAgent):
    """
    Agent responsible for maintaining security and compliance standards.
    
    Ensures the MEP Ranking application follows security best practices
    and complies with data protection regulations like GDPR.
    """
    
    def _initialize_agent(self) -> None:
        """Initialize security and compliance configurations"""
        self.security_config = {
            'allowed_file_extensions': ['.py', '.js', '.html', '.css', '.json', '.md', '.txt'],
            'sensitive_patterns': [
                r'(?i)(password|pwd|pass)\s*[=:]\s*["\'][^"\']+["\']',
                r'(?i)(api[_-]?key|apikey)\s*[=:]\s*["\'][^"\']+["\']',
                r'(?i)(secret|token)\s*[=:]\s*["\'][^"\']+["\']',
                r'(?i)(database[_-]?url|db[_-]?url)\s*[=:]\s*["\'][^"\']+["\']'
            ],
            'security_headers': [
                'Content-Security-Policy',
                'X-Frame-Options',
                'X-Content-Type-Options',
                'Strict-Transport-Security'
            ]
        }
        
        self.compliance_config = {
            'gdpr_data_fields': [
                'name', 'email', 'ip_address', 'user_agent', 'location'
            ],
            'data_retention_days': 365 * 2,  # 2 years for EP data
            'privacy_policy_required': True
        }
        
        self.logger.info(f"Security Compliance Agent initialized for project: {self.project_root}")
    
    def _define_capabilities(self) -> List[AgentCapability]:
        """Define security and compliance agent capabilities"""
        return [
            AgentCapability(
                name="scan_security_vulnerabilities",
                description="Scan codebase for security vulnerabilities",
                required_tools=["file_system", "pattern_matching"],
                complexity_level="intermediate"
            ),
            AgentCapability(
                name="audit_data_privacy",
                description="Audit data handling for GDPR compliance",
                required_tools=["database", "file_system"],
                complexity_level="advanced"
            ),
            AgentCapability(
                name="check_dependency_vulnerabilities",
                description="Check dependencies for known vulnerabilities",
                required_tools=["package_management"],
                complexity_level="intermediate"
            ),
            AgentCapability(
                name="validate_access_controls",
                description="Validate access control implementations",
                required_tools=["file_system", "configuration"],
                complexity_level="intermediate"
            ),
            AgentCapability(
                name="audit_security_headers",
                description="Audit HTTP security headers configuration",
                required_tools=["web_server", "configuration"],
                complexity_level="basic"
            ),
            AgentCapability(
                name="scan_sensitive_data_exposure",
                description="Scan for exposed sensitive data",
                required_tools=["file_system", "pattern_matching"],
                complexity_level="intermediate"
            ),
            AgentCapability(
                name="generate_security_report",
                description="Generate comprehensive security assessment report",
                required_tools=["reporting", "analysis"],
                complexity_level="advanced"
            ),
            AgentCapability(
                name="validate_data_backup_security",
                description="Validate backup data security measures",
                required_tools=["file_system", "encryption"],
                complexity_level="intermediate"
            ),
            AgentCapability(
                name="check_gdpr_compliance",
                description="Check GDPR compliance measures",
                required_tools=["database", "documentation"],
                complexity_level="advanced"
            )
        ]
    
    async def _execute_task_impl(self, task_type: str, task_data: Dict[str, Any]) -> TaskResult:
        """Execute security and compliance tasks"""
        
        if task_type == "scan_security_vulnerabilities":
            return await self._scan_security_vulnerabilities(task_data)
        elif task_type == "audit_data_privacy":
            return await self._audit_data_privacy(task_data)
        elif task_type == "check_dependency_vulnerabilities":
            return await self._check_dependency_vulnerabilities(task_data)
        elif task_type == "validate_access_controls":
            return await self._validate_access_controls(task_data)
        elif task_type == "audit_security_headers":
            return await self._audit_security_headers(task_data)
        elif task_type == "scan_sensitive_data_exposure":
            return await self._scan_sensitive_data_exposure(task_data)
        elif task_type == "generate_security_report":
            return await self._generate_security_report(task_data)
        elif task_type == "validate_data_backup_security":
            return await self._validate_data_backup_security(task_data)
        elif task_type == "check_gdpr_compliance":
            return await self._check_gdpr_compliance(task_data)
        else:
            return TaskResult(
                success=False,
                message=f"Unknown task type: {task_type}",
                errors=[f"Task type '{task_type}' not implemented"]
            )
    
    async def _scan_security_vulnerabilities(self, task_data: Dict[str, Any]) -> TaskResult:
        """Scan codebase for security vulnerabilities"""
        try:
            scan_dirs = task_data.get('directories', ['backend', 'public', 'agents'])
            vulnerabilities = []
            
            # Security patterns to check for
            security_checks = [
                {
                    'name': 'SQL Injection Risk',
                    'pattern': r'(?i)(execute|query)\s*\(\s*["\'][^"\']*\+[^"\']*["\']',
                    'severity': 'high',
                    'description': 'Potential SQL injection vulnerability'
                },
                {
                    'name': 'Hard-coded Secrets',
                    'pattern': r'(?i)(password|secret|key|token)\s*[=:]\s*["\'][a-zA-Z0-9]{8,}["\']',
                    'severity': 'high',
                    'description': 'Hard-coded credentials detected'
                },
                {
                    'name': 'Debug Mode Enabled',
                    'pattern': r'(?i)debug\s*[=:]\s*true',
                    'severity': 'medium',
                    'description': 'Debug mode enabled in production code'
                },
                {
                    'name': 'Insecure HTTP',
                    'pattern': r'http://(?!localhost|127\.0\.0\.1)',
                    'severity': 'low',
                    'description': 'Insecure HTTP URL detected'
                },
                {
                    'name': 'Eval Usage',
                    'pattern': r'\beval\s*\(',
                    'severity': 'high',
                    'description': 'Dangerous eval() function usage'
                }
            ]
            
            for scan_dir in scan_dirs:
                dir_path = self.project_root / scan_dir
                if not dir_path.exists():
                    continue
                
                # Scan all files in directory
                for file_path in dir_path.rglob('*'):
                    if not file_path.is_file():
                        continue
                    
                    if file_path.suffix not in self.security_config['allowed_file_extensions']:
                        continue
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        # Check each security pattern
                        for check in security_checks:
                            matches = re.finditer(check['pattern'], content, re.MULTILINE)
                            
                            for match in matches:
                                line_num = content[:match.start()].count('\n') + 1
                                
                                vulnerabilities.append({
                                    'type': check['name'],
                                    'severity': check['severity'],
                                    'description': check['description'],
                                    'file': str(file_path.relative_to(self.project_root)),
                                    'line': line_num,
                                    'matched_text': match.group()[:100],  # First 100 chars
                                    'pattern': check['pattern']
                                })
                    
                    except Exception as e:
                        self.logger.warning(f"Could not scan file {file_path}: {str(e)}")
            
            # Categorize vulnerabilities by severity
            severity_counts = {'high': 0, 'medium': 0, 'low': 0}
            for vuln in vulnerabilities:
                severity_counts[vuln['severity']] += 1
            
            scan_result = {
                'scan_timestamp': datetime.now().isoformat(),
                'directories_scanned': scan_dirs,
                'vulnerabilities_found': len(vulnerabilities),
                'severity_breakdown': severity_counts,
                'vulnerabilities': vulnerabilities,
                'risk_level': self._calculate_risk_level(severity_counts)
            }
            
            return TaskResult(
                success=True,
                message=f"Security scan completed. {len(vulnerabilities)} vulnerabilities found.",
                data=scan_result
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Security vulnerability scan failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def _audit_data_privacy(self, task_data: Dict[str, Any]) -> TaskResult:
        """Audit data handling for GDPR compliance"""
        try:
            audit_results = {
                'audit_timestamp': datetime.now().isoformat(),
                'gdpr_compliance_status': 'compliant',
                'findings': [],
                'recommendations': []
            }
            
            # Check database for personal data
            database_path = self.project_root / 'data' / 'meps.db'
            if database_path.exists():
                conn = sqlite3.connect(database_path)
                cursor = conn.cursor()
                
                # Get all table names
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                
                personal_data_found = []
                
                for table_name in tables:
                    table = table_name[0]
                    
                    # Get column names
                    cursor.execute(f"PRAGMA table_info({table})")
                    columns = cursor.fetchall()
                    
                    # Check for personal data fields
                    for column in columns:
                        column_name = column[1].lower()
                        
                        # Check if column contains personal data
                        personal_data_types = [
                            'email', 'phone', 'address', 'birth', 'nationality',
                            'personal_id', 'passport', 'social_security'
                        ]
                        
                        if any(pd_type in column_name for pd_type in personal_data_types):
                            personal_data_found.append({
                                'table': table,
                                'column': column[1],
                                'type': column[2]
                            })
                
                conn.close()
                
                if personal_data_found:
                    audit_results['findings'].append({
                        'category': 'Personal Data Storage',
                        'severity': 'medium',
                        'description': f"Personal data fields detected in database",
                        'details': personal_data_found
                    })
                    
                    audit_results['recommendations'].append(
                        "Ensure personal data processing has legal basis and data subjects' consent"
                    )
            
            # Check for privacy policy
            privacy_files = ['privacy_policy.md', 'PRIVACY.md', 'privacy.html']
            privacy_policy_exists = any(
                (self.project_root / filename).exists() for filename in privacy_files
            )
            
            if not privacy_policy_exists:
                audit_results['findings'].append({
                    'category': 'Privacy Policy',
                    'severity': 'high',
                    'description': 'No privacy policy found',
                    'details': 'GDPR requires a clear privacy policy'
                })
                
                audit_results['recommendations'].append(
                    "Create a comprehensive privacy policy explaining data processing"
                )
                audit_results['gdpr_compliance_status'] = 'non_compliant'
            
            # Check data retention
            audit_results['data_retention_policy'] = {
                'configured_retention_days': self.compliance_config['data_retention_days'],
                'status': 'policy_defined',
                'recommendation': 'Implement automated data cleanup after retention period'
            }
            
            # Check for data processing consent mechanisms
            consent_mechanisms = []
            
            # Scan frontend files for consent handling
            public_dir = self.project_root / 'public'
            if public_dir.exists():
                for file_path in public_dir.rglob('*.html'):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        if re.search(r'(?i)(consent|cookie|privacy|gdpr)', content):
                            consent_mechanisms.append(str(file_path.relative_to(self.project_root)))
                    except:
                        pass
            
            audit_results['consent_mechanisms'] = {
                'files_with_consent_handling': consent_mechanisms,
                'status': 'present' if consent_mechanisms else 'missing'
            }
            
            if not consent_mechanisms:
                audit_results['recommendations'].append(
                    "Implement user consent mechanisms for data processing and cookies"
                )
            
            # Overall compliance assessment
            high_severity_findings = [f for f in audit_results['findings'] if f['severity'] == 'high']
            if high_severity_findings:
                audit_results['gdpr_compliance_status'] = 'non_compliant'
            elif audit_results['findings']:
                audit_results['gdpr_compliance_status'] = 'partially_compliant'
            
            return TaskResult(
                success=True,
                message=f"Data privacy audit completed. Status: {audit_results['gdpr_compliance_status']}",
                data=audit_results
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Data privacy audit failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def _check_dependency_vulnerabilities(self, task_data: Dict[str, Any]) -> TaskResult:
        """Check dependencies for known vulnerabilities"""
        try:
            vulnerability_report = {
                'scan_timestamp': datetime.now().isoformat(),
                'dependency_files_found': [],
                'vulnerabilities': [],
                'recommendations': []
            }
            
            # Check for dependency files
            dependency_files = [
                'requirements.txt',
                'package.json',
                'Pipfile',
                'pyproject.toml'
            ]
            
            found_files = []
            for dep_file in dependency_files:
                file_path = self.project_root / dep_file
                if file_path.exists():
                    found_files.append(dep_file)
            
            vulnerability_report['dependency_files_found'] = found_files
            
            # Check Python requirements
            requirements_path = self.project_root / 'requirements.txt'
            if requirements_path.exists():
                try:
                    with open(requirements_path, 'r') as f:
                        requirements = f.read()
                    
                    # Basic checks for outdated/vulnerable packages
                    known_vulnerable_patterns = [
                        r'(?i)flask\s*==\s*[01]\.',  # Very old Flask versions
                        r'(?i)django\s*==\s*[12]\.',  # Very old Django versions
                        r'(?i)requests\s*==\s*2\.[0-9]\.', # Old requests versions
                    ]
                    
                    for pattern in known_vulnerable_patterns:
                        if re.search(pattern, requirements):
                            vulnerability_report['vulnerabilities'].append({
                                'type': 'Potentially Vulnerable Package',
                                'severity': 'medium',
                                'description': 'Package version may have known vulnerabilities',
                                'file': 'requirements.txt',
                                'pattern_matched': pattern
                            })
                    
                    # Check for pinned versions (security best practice)
                    unpinned_packages = re.findall(r'^([a-zA-Z0-9_-]+)(?!\s*[=<>])', requirements, re.MULTILINE)
                    
                    if unpinned_packages:
                        vulnerability_report['recommendations'].append(
                            f"Pin package versions for security: {', '.join(unpinned_packages[:5])}"
                        )
                
                except Exception as e:
                    self.logger.warning(f"Could not analyze requirements.txt: {str(e)}")
            
            # Check package.json if exists
            package_json_path = self.project_root / 'package.json'
            if package_json_path.exists():
                try:
                    with open(package_json_path, 'r') as f:
                        package_data = json.load(f)
                    
                    dependencies = package_data.get('dependencies', {})
                    dev_dependencies = package_data.get('devDependencies', {})
                    
                    # Check for common vulnerable packages
                    all_deps = {**dependencies, **dev_dependencies}
                    
                    for package, version in all_deps.items():
                        # Basic checks for known vulnerable packages
                        if package.lower() in ['lodash', 'moment', 'jquery'] and not version.startswith('^'):
                            vulnerability_report['vulnerabilities'].append({
                                'type': 'Potentially Outdated Package',
                                'severity': 'low',
                                'description': f'Package {package} may be outdated',
                                'file': 'package.json',
                                'package': package,
                                'version': version
                            })
                
                except Exception as e:
                    self.logger.warning(f"Could not analyze package.json: {str(e)}")
            
            # General recommendations
            if not found_files:
                vulnerability_report['recommendations'].append(
                    "No dependency files found. Consider using dependency management."
                )
            else:
                vulnerability_report['recommendations'].extend([
                    "Regularly update dependencies to latest secure versions",
                    "Consider using automated dependency vulnerability scanning",
                    "Implement dependency pinning for reproducible builds"
                ])
            
            vulnerability_count = len(vulnerability_report['vulnerabilities'])
            
            return TaskResult(
                success=True,
                message=f"Dependency vulnerability check completed. {vulnerability_count} potential issues found.",
                data=vulnerability_report
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Dependency vulnerability check failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def _scan_sensitive_data_exposure(self, task_data: Dict[str, Any]) -> TaskResult:
        """Scan for exposed sensitive data"""
        try:
            scan_dirs = task_data.get('directories', ['.'])
            exposures = []
            
            for scan_dir in scan_dirs:
                dir_path = self.project_root / scan_dir
                if not dir_path.exists():
                    continue
                
                # Scan files for sensitive data patterns
                for file_path in dir_path.rglob('*'):
                    if not file_path.is_file():
                        continue
                    
                    # Skip binary files and certain extensions
                    if file_path.suffix in ['.db', '.sqlite', '.pyc', '.png', '.jpg', '.gif']:
                        continue
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        # Check for sensitive patterns
                        for pattern in self.security_config['sensitive_patterns']:
                            matches = re.finditer(pattern, content, re.MULTILINE)
                            
                            for match in matches:
                                line_num = content[:match.start()].count('\n') + 1
                                
                                exposures.append({
                                    'type': 'Sensitive Data Exposure',
                                    'severity': 'high',
                                    'file': str(file_path.relative_to(self.project_root)),
                                    'line': line_num,
                                    'pattern': pattern,
                                    'matched_text': match.group()[:50] + '...' if len(match.group()) > 50 else match.group()
                                })
                    
                    except Exception as e:
                        self.logger.warning(f"Could not scan file {file_path}: {str(e)}")
            
            # Check for common sensitive files
            sensitive_files = [
                '.env',
                '.secret',
                'config.ini',
                'database.conf',
                'credentials.json'
            ]
            
            for sensitive_file in sensitive_files:
                file_path = self.project_root / sensitive_file
                if file_path.exists():
                    exposures.append({
                        'type': 'Sensitive File Present',
                        'severity': 'medium',
                        'file': sensitive_file,
                        'description': 'Sensitive configuration file detected'
                    })
            
            exposure_result = {
                'scan_timestamp': datetime.now().isoformat(),
                'directories_scanned': scan_dirs,
                'exposures_found': len(exposures),
                'exposures': exposures,
                'risk_assessment': 'high' if any(e['severity'] == 'high' for e in exposures) else 'low'
            }
            
            return TaskResult(
                success=True,
                message=f"Sensitive data exposure scan completed. {len(exposures)} exposures found.",
                data=exposure_result
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Sensitive data exposure scan failed: {str(e)}",
                errors=[str(e)]
            )
    
    def _calculate_risk_level(self, severity_counts: Dict[str, int]) -> str:
        """Calculate overall risk level based on vulnerability counts"""
        if severity_counts['high'] > 0:
            return 'high'
        elif severity_counts['medium'] > 2:
            return 'medium'
        elif severity_counts['low'] > 5:
            return 'medium'
        else:
            return 'low'
    
    async def _generate_security_report(self, task_data: Dict[str, Any]) -> TaskResult:
        """Generate comprehensive security assessment report"""
        try:
            # Run all security checks
            vuln_scan = await self._scan_security_vulnerabilities(task_data)
            privacy_audit = await self._audit_data_privacy(task_data)
            dependency_check = await self._check_dependency_vulnerabilities(task_data)
            sensitive_scan = await self._scan_sensitive_data_exposure(task_data)
            
            # Compile comprehensive report
            security_report = {
                'report_metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'report_version': '1.0',
                    'project_path': str(self.project_root)
                },
                'executive_summary': {
                    'overall_security_status': 'secure',
                    'critical_issues': 0,
                    'total_recommendations': 0
                },
                'vulnerability_assessment': vuln_scan.data if vuln_scan.success else {'error': vuln_scan.message},
                'privacy_compliance': privacy_audit.data if privacy_audit.success else {'error': privacy_audit.message},
                'dependency_security': dependency_check.data if dependency_check.success else {'error': dependency_check.message},
                'sensitive_data_exposure': sensitive_scan.data if sensitive_scan.success else {'error': sensitive_scan.message}
            }
            
            # Calculate overall status
            critical_issues = 0
            all_recommendations = []
            
            if vuln_scan.success:
                critical_issues += vuln_scan.data.get('severity_breakdown', {}).get('high', 0)
            
            if privacy_audit.success:
                privacy_findings = privacy_audit.data.get('findings', [])
                critical_issues += len([f for f in privacy_findings if f.get('severity') == 'high'])
                all_recommendations.extend(privacy_audit.data.get('recommendations', []))
            
            if sensitive_scan.success:
                sensitive_exposures = sensitive_scan.data.get('exposures', [])
                critical_issues += len([e for e in sensitive_exposures if e.get('severity') == 'high'])
            
            if dependency_check.success:
                dep_vulns = dependency_check.data.get('vulnerabilities', [])
                critical_issues += len([v for v in dep_vulns if v.get('severity') == 'high'])
                all_recommendations.extend(dependency_check.data.get('recommendations', []))
            
            # Update executive summary
            security_report['executive_summary'] = {
                'overall_security_status': 'critical' if critical_issues > 5 else 'needs_attention' if critical_issues > 0 else 'secure',
                'critical_issues': critical_issues,
                'total_recommendations': len(all_recommendations),
                'priority_actions': all_recommendations[:5]  # Top 5 recommendations
            }
            
            # Save report
            reports_dir = self.project_root / 'reports'
            reports_dir.mkdir(exist_ok=True)
            
            report_filename = f"security_assessment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            report_path = reports_dir / report_filename
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(security_report, f, indent=2, ensure_ascii=False)
            
            return TaskResult(
                success=True,
                message=f"Security report generated: {report_filename}",
                data={
                    'report_path': str(report_path),
                    'executive_summary': security_report['executive_summary'],
                    'full_report': security_report
                }
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Security report generation failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def _validate_access_controls(self, task_data: Dict[str, Any]) -> TaskResult:
        """Validate access control implementations"""
        try:
            access_control_findings = []
            
            # Check file permissions on sensitive files
            sensitive_paths = [
                'data/meps.db',
                'backend/',
                'agents/',
                'requirements.txt'
            ]
            
            for path_str in sensitive_paths:
                path = self.project_root / path_str
                if path.exists():
                    try:
                        # Check if file/directory is readable by others (basic check)
                        stat_info = path.stat()
                        permissions = oct(stat_info.st_mode)[-3:]
                        
                        # Check for overly permissive permissions
                        if permissions.endswith('7') or permissions.endswith('6'):
                            access_control_findings.append({
                                'type': 'File Permissions',
                                'severity': 'medium',
                                'path': str(path.relative_to(self.project_root)),
                                'permissions': permissions,
                                'issue': 'File is writable by others'
                            })
                    except Exception as e:
                        self.logger.warning(f"Could not check permissions for {path}: {str(e)}")
            
            # Check for authentication mechanisms in web server
            server_files = ['serve.py', 'working_api_server.py', 'run_api_server.py']
            auth_mechanisms_found = False
            
            for server_file in server_files:
                file_path = self.project_root / server_file
                if file_path.exists():
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Look for authentication patterns
                        auth_patterns = [
                            r'(?i)(auth|login|password|token|session)',
                            r'(?i)(authenticate|authorize)',
                            r'@login_required',
                            r'@auth\.required'
                        ]
                        
                        for pattern in auth_patterns:
                            if re.search(pattern, content):
                                auth_mechanisms_found = True
                                break
                        
                        if auth_mechanisms_found:
                            break
                    
                    except Exception as e:
                        self.logger.warning(f"Could not analyze {server_file}: {str(e)}")
            
            if not auth_mechanisms_found:
                access_control_findings.append({
                    'type': 'Authentication',
                    'severity': 'low',
                    'description': 'No authentication mechanisms detected in server files',
                    'recommendation': 'Consider adding authentication for admin features'
                })
            
            access_control_report = {
                'audit_timestamp': datetime.now().isoformat(),
                'findings': access_control_findings,
                'authentication_status': 'present' if auth_mechanisms_found else 'not_detected',
                'overall_status': 'secure' if not access_control_findings else 'needs_review'
            }
            
            return TaskResult(
                success=True,
                message=f"Access control validation completed. {len(access_control_findings)} findings.",
                data=access_control_report
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Access control validation failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def _audit_security_headers(self, task_data: Dict[str, Any]) -> TaskResult:
        """Audit HTTP security headers configuration"""
        try:
            # This is a basic check - in production, you'd test actual HTTP responses
            header_findings = []
            
            # Check server configuration files for security headers
            server_files = ['serve.py', 'working_api_server.py']
            
            for server_file in server_files:
                file_path = self.project_root / server_file
                if not file_path.exists():
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Check for security headers
                    for header in self.security_config['security_headers']:
                        if header not in content:
                            header_findings.append({
                                'type': 'Missing Security Header',
                                'severity': 'medium',
                                'file': server_file,
                                'missing_header': header,
                                'recommendation': f'Add {header} header for enhanced security'
                            })
                
                except Exception as e:
                    self.logger.warning(f"Could not analyze {server_file}: {str(e)}")
            
            # Check HTML files for CSP meta tags
            html_files = list((self.project_root / 'public').glob('*.html'))
            csp_found = False
            
            for html_file in html_files:
                try:
                    with open(html_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if 'Content-Security-Policy' in content:
                        csp_found = True
                        break
                
                except Exception as e:
                    self.logger.warning(f"Could not analyze {html_file}: {str(e)}")
            
            if not csp_found:
                header_findings.append({
                    'type': 'Missing CSP',
                    'severity': 'medium',
                    'description': 'No Content Security Policy found in HTML files',
                    'recommendation': 'Implement CSP to prevent XSS attacks'
                })
            
            headers_report = {
                'audit_timestamp': datetime.now().isoformat(),
                'findings': header_findings,
                'security_headers_status': 'complete' if not header_findings else 'incomplete',
                'recommendations': [f['recommendation'] for f in header_findings if 'recommendation' in f]
            }
            
            return TaskResult(
                success=True,
                message=f"Security headers audit completed. {len(header_findings)} findings.",
                data=headers_report
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Security headers audit failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def _validate_data_backup_security(self, task_data: Dict[str, Any]) -> TaskResult:
        """Validate backup data security measures"""
        try:
            backup_security_report = {
                'audit_timestamp': datetime.now().isoformat(),
                'backup_locations': [],
                'security_findings': [],
                'recommendations': []
            }
            
            # Look for backup files
            backup_patterns = ['*.backup', '*.bak', '*.db.backup', '*_backup.*']
            backup_files = []
            
            for pattern in backup_patterns:
                backup_files.extend(self.project_root.rglob(pattern))
            
            backup_security_report['backup_locations'] = [
                str(f.relative_to(self.project_root)) for f in backup_files
            ]
            
            # Check backup file permissions
            for backup_file in backup_files:
                try:
                    stat_info = backup_file.stat()
                    permissions = oct(stat_info.st_mode)[-3:]
                    
                    if permissions[1:] != '00':  # Not restricted to owner
                        backup_security_report['security_findings'].append({
                            'type': 'Backup File Permissions',
                            'severity': 'high',
                            'file': str(backup_file.relative_to(self.project_root)),
                            'permissions': permissions,
                            'issue': 'Backup file accessible by non-owners'
                        })
                
                except Exception as e:
                    self.logger.warning(f"Could not check backup file {backup_file}: {str(e)}")
            
            # General backup security recommendations
            if backup_files:
                backup_security_report['recommendations'].extend([
                    'Ensure backup files are encrypted at rest',
                    'Implement secure backup rotation policies',
                    'Store backups in secure, access-controlled locations',
                    'Regularly test backup restoration procedures'
                ])
            else:
                backup_security_report['recommendations'].append(
                    'Implement automated backup procedures for critical data'
                )
            
            findings_count = len(backup_security_report['security_findings'])
            
            return TaskResult(
                success=True,
                message=f"Backup security validation completed. {findings_count} security findings.",
                data=backup_security_report
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Backup security validation failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def _check_gdpr_compliance(self, task_data: Dict[str, Any]) -> TaskResult:
        """Check GDPR compliance measures"""
        try:
            # This is essentially the same as _audit_data_privacy but focused on GDPR
            return await self._audit_data_privacy(task_data)
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"GDPR compliance check failed: {str(e)}",
                errors=[str(e)]
            )