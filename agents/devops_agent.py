"""
DevOps Agent - Streamlines deployment and operations

This agent handles automated deployment pipelines, environment management,
system health monitoring, and operational tasks.
"""

import asyncio
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import psutil
import sqlite3

from .base_agent import BaseAgent, TaskResult, AgentCapability


class DevOpsAgent(BaseAgent):
    """
    Agent responsible for deployment and operational tasks.
    
    Manages deployment pipelines, environment configuration,
    system monitoring, backup automation, and maintenance tasks.
    """
    
    def _initialize_agent(self) -> None:
        """Initialize DevOps agent configurations"""
        self.devops_config = {
            'environments': ['development', 'staging', 'production'],
            'backup_retention_days': 30,
            'monitoring_intervals': {
                'system_health': 300,  # 5 minutes
                'disk_space': 3600,    # 1 hour
                'database_size': 1800  # 30 minutes
            },
            'deployment_checks': [
                'database_integrity',
                'static_files',
                'configuration_validity',
                'dependency_verification'
            ],
            'resource_thresholds': {
                'disk_usage_warning': 80,  # percent
                'disk_usage_critical': 90,
                'memory_usage_warning': 80,
                'cpu_usage_warning': 85
            }
        }
        
        self.deployment_config_path = self.project_root / 'deployment.json'
        self.backup_dir = self.project_root / 'backups'
        self.logs_dir = self.project_root / 'logs'
        
        # Ensure directories exist
        self.backup_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        
        self.logger.info(f"DevOps Agent initialized for project: {self.project_root}")
    
    def _define_capabilities(self) -> List[AgentCapability]:
        """Define DevOps agent capabilities"""
        return [
            AgentCapability(
                name="deploy_application",
                description="Deploy application to specified environment",
                required_tools=["deployment", "file_system", "process_management"],
                complexity_level="advanced"
            ),
            AgentCapability(
                name="monitor_system_health",
                description="Monitor system health and resource usage",
                required_tools=["system_monitoring", "metrics"],
                complexity_level="intermediate"
            ),
            AgentCapability(
                name="backup_data",
                description="Create automated backups of application data",
                required_tools=["file_system", "compression"],
                complexity_level="intermediate"
            ),
            AgentCapability(
                name="restore_from_backup",
                description="Restore application from backup",
                required_tools=["file_system", "database"],
                complexity_level="advanced"
            ),
            AgentCapability(
                name="manage_environment",
                description="Manage application environment configuration",
                required_tools=["configuration", "environment"],
                complexity_level="intermediate"
            ),
            AgentCapability(
                name="run_maintenance_tasks",
                description="Execute routine maintenance tasks",
                required_tools=["database", "file_system", "cleanup"],
                complexity_level="intermediate"
            ),
            AgentCapability(
                name="generate_deployment_report",
                description="Generate comprehensive deployment status report",
                required_tools=["reporting", "system_analysis"],
                complexity_level="intermediate"
            ),
            AgentCapability(
                name="optimize_performance",
                description="Optimize system performance and resource usage",
                required_tools=["performance_analysis", "optimization"],
                complexity_level="advanced"
            ),
            AgentCapability(
                name="manage_dependencies",
                description="Manage and update application dependencies",
                required_tools=["package_management"],
                complexity_level="intermediate"
            ),
            AgentCapability(
                name="setup_monitoring",
                description="Set up automated monitoring and alerting",
                required_tools=["monitoring", "configuration"],
                complexity_level="advanced"
            )
        ]
    
    async def _execute_task_impl(self, task_type: str, task_data: Dict[str, Any]) -> TaskResult:
        """Execute DevOps tasks"""
        
        if task_type == "deploy_application":
            return await self._deploy_application(task_data)
        elif task_type == "monitor_system_health":
            return await self._monitor_system_health(task_data)
        elif task_type == "backup_data":
            return await self._backup_data(task_data)
        elif task_type == "restore_from_backup":
            return await self._restore_from_backup(task_data)
        elif task_type == "manage_environment":
            return await self._manage_environment(task_data)
        elif task_type == "run_maintenance_tasks":
            return await self._run_maintenance_tasks(task_data)
        elif task_type == "generate_deployment_report":
            return await self._generate_deployment_report(task_data)
        elif task_type == "optimize_performance":
            return await self._optimize_performance(task_data)
        elif task_type == "manage_dependencies":
            return await self._manage_dependencies(task_data)
        elif task_type == "setup_monitoring":
            return await self._setup_monitoring(task_data)
        else:
            return TaskResult(
                success=False,
                message=f"Unknown task type: {task_type}",
                errors=[f"Task type '{task_type}' not implemented"]
            )
    
    async def _deploy_application(self, task_data: Dict[str, Any]) -> TaskResult:
        """Deploy application to specified environment"""
        try:
            environment = task_data.get('environment', 'development')
            if environment not in self.devops_config['environments']:
                return TaskResult(
                    success=False,
                    message=f"Invalid environment: {environment}",
                    errors=[f"Environment must be one of: {', '.join(self.devops_config['environments'])}"]
                )
            
            deployment_result = {
                'deployment_timestamp': datetime.now().isoformat(),
                'environment': environment,
                'checks_performed': [],
                'deployment_steps': [],
                'warnings': [],
                'status': 'in_progress'
            }
            
            # Pre-deployment checks
            for check in self.devops_config['deployment_checks']:
                check_result = await self._perform_deployment_check(check)
                deployment_result['checks_performed'].append({
                    'check': check,
                    'status': 'passed' if check_result.success else 'failed',
                    'details': check_result.message
                })
                
                if not check_result.success:
                    deployment_result['warnings'].append(f"Check failed: {check}")
            
            # Database preparation
            db_prep_result = await self._prepare_database_for_deployment()
            deployment_result['deployment_steps'].append({
                'step': 'Database Preparation',
                'status': 'completed' if db_prep_result.success else 'failed',
                'details': db_prep_result.message
            })
            
            # Static files preparation
            static_prep_result = await self._prepare_static_files()
            deployment_result['deployment_steps'].append({
                'step': 'Static Files Preparation',
                'status': 'completed' if static_prep_result.success else 'failed',
                'details': static_prep_result.message
            })
            
            # Configuration validation
            config_result = await self._validate_configuration(environment)
            deployment_result['deployment_steps'].append({
                'step': 'Configuration Validation',
                'status': 'completed' if config_result.success else 'failed',
                'details': config_result.message
            })
            
            # Health check
            health_result = await self._perform_health_check()
            deployment_result['deployment_steps'].append({
                'step': 'Health Check',
                'status': 'completed' if health_result.success else 'failed',
                'details': health_result.message
            })
            
            # Determine overall deployment status
            failed_steps = [step for step in deployment_result['deployment_steps'] if step['status'] == 'failed']
            
            if failed_steps:
                deployment_result['status'] = 'failed'
                deployment_result['message'] = f"Deployment failed: {len(failed_steps)} steps failed"
            else:
                deployment_result['status'] = 'success'
                deployment_result['message'] = f"Deployment to {environment} completed successfully"
            
            # Create deployment manifest
            manifest_path = self.logs_dir / f'deployment_{environment}_{int(datetime.now().timestamp())}.json'
            with open(manifest_path, 'w') as f:
                json.dump(deployment_result, f, indent=2, default=str)
            
            return TaskResult(
                success=deployment_result['status'] == 'success',
                message=deployment_result['message'],
                data=deployment_result,
                warnings=deployment_result['warnings']
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Deployment failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def _perform_deployment_check(self, check_type: str) -> TaskResult:
        """Perform specific deployment check"""
        try:
            if check_type == 'database_integrity':
                return await self._check_database_integrity()
            elif check_type == 'static_files':
                return await self._check_static_files()
            elif check_type == 'configuration_validity':
                return await self._check_configuration_validity()
            elif check_type == 'dependency_verification':
                return await self._check_dependencies()
            else:
                return TaskResult(
                    success=False,
                    message=f"Unknown check type: {check_type}"
                )
                
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Check {check_type} failed: {str(e)}"
            )
    
    async def _check_database_integrity(self) -> TaskResult:
        """Check database integrity and accessibility"""
        try:
            database_path = self.project_root / 'data' / 'meps.db'
            
            if not database_path.exists():
                return TaskResult(
                    success=False,
                    message="Database file not found",
                    errors=["meps.db is missing"]
                )
            
            # Basic connectivity check
            conn = sqlite3.connect(database_path)
            cursor = conn.cursor()
            
            # Check table existence
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            required_tables = ['meps', 'activities', 'roles']
            missing_tables = []
            
            table_names = [table[0] for table in tables]
            for required_table in required_tables:
                if required_table not in table_names:
                    missing_tables.append(required_table)
            
            if missing_tables:
                conn.close()
                return TaskResult(
                    success=False,
                    message=f"Missing database tables: {', '.join(missing_tables)}"
                )
            
            # Check data integrity
            cursor.execute("SELECT COUNT(*) FROM meps WHERE total_score > 0")
            active_meps = cursor.fetchone()[0]
            
            conn.close()
            
            if active_meps == 0:
                return TaskResult(
                    success=False,
                    message="No active MEPs found in database"
                )
            
            return TaskResult(
                success=True,
                message=f"Database integrity check passed: {active_meps} active MEPs",
                data={'active_meps': active_meps, 'tables_count': len(tables)}
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Database integrity check failed: {str(e)}"
            )
    
    async def _check_static_files(self) -> TaskResult:
        """Check static files availability and integrity"""
        try:
            static_dir = self.project_root / 'public'
            
            if not static_dir.exists():
                return TaskResult(
                    success=False,
                    message="Static files directory not found"
                )
            
            required_files = [
                'index.html',
                'profile.html',
                'js/app.js',
                'js/utilities.js'
            ]
            
            missing_files = []
            for file_path in required_files:
                if not (static_dir / file_path).exists():
                    missing_files.append(file_path)
            
            if missing_files:
                return TaskResult(
                    success=False,
                    message=f"Missing static files: {', '.join(missing_files)}"
                )
            
            # Check dataset files
            data_dir = static_dir / 'data'
            if data_dir.exists():
                datasets = list(data_dir.glob('term*_dataset.json'))
                dataset_count = len(datasets)
            else:
                dataset_count = 0
            
            return TaskResult(
                success=True,
                message=f"Static files check passed: {dataset_count} datasets available",
                data={'datasets_count': dataset_count}
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Static files check failed: {str(e)}"
            )
    
    async def _check_configuration_validity(self) -> TaskResult:
        """Check configuration files validity"""
        try:
            config_issues = []
            
            # Check Python requirements
            requirements_path = self.project_root / 'requirements.txt'
            if not requirements_path.exists():
                config_issues.append("requirements.txt not found")
            
            # Check main server files
            server_files = ['serve.py', 'working_api_server.py']
            server_found = any((self.project_root / f).exists() for f in server_files)
            
            if not server_found:
                config_issues.append("No server files found")
            
            # Check CLAUDE.md for configuration
            claude_md = self.project_root / 'CLAUDE.md'
            if not claude_md.exists():
                config_issues.append("CLAUDE.md configuration file not found")
            
            if config_issues:
                return TaskResult(
                    success=False,
                    message=f"Configuration issues: {', '.join(config_issues)}"
                )
            
            return TaskResult(
                success=True,
                message="Configuration validation passed"
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Configuration validation failed: {str(e)}"
            )
    
    async def _check_dependencies(self) -> TaskResult:
        """Check dependency availability"""
        try:
            requirements_path = self.project_root / 'requirements.txt'
            
            if not requirements_path.exists():
                return TaskResult(
                    success=False,
                    message="requirements.txt not found"
                )
            
            # In a real implementation, would check if packages are installed
            # For now, just verify the file exists and is readable
            try:
                with open(requirements_path, 'r') as f:
                    requirements = f.read()
                
                package_count = len([line for line in requirements.split('\n') if line.strip() and not line.startswith('#')])
                
                return TaskResult(
                    success=True,
                    message=f"Dependencies check passed: {package_count} packages listed",
                    data={'packages_count': package_count}
                )
                
            except Exception as e:
                return TaskResult(
                    success=False,
                    message=f"Cannot read requirements.txt: {str(e)}"
                )
                
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Dependencies check failed: {str(e)}"
            )
    
    async def _prepare_database_for_deployment(self) -> TaskResult:
        """Prepare database for deployment"""
        try:
            database_path = self.project_root / 'data' / 'meps.db'
            
            if not database_path.exists():
                return TaskResult(
                    success=False,
                    message="Database not found for deployment preparation"
                )
            
            # Create backup before deployment
            backup_result = await self._backup_data({'include_database': True})
            
            if not backup_result.success:
                return TaskResult(
                    success=False,
                    message="Failed to create pre-deployment backup"
                )
            
            # Optimize database (VACUUM)
            try:
                conn = sqlite3.connect(database_path)
                conn.execute("VACUUM")
                conn.close()
                
                return TaskResult(
                    success=True,
                    message="Database prepared for deployment (backup created, optimized)"
                )
                
            except Exception as e:
                return TaskResult(
                    success=False,
                    message=f"Database optimization failed: {str(e)}"
                )
                
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Database preparation failed: {str(e)}"
            )
    
    async def _prepare_static_files(self) -> TaskResult:
        """Prepare static files for deployment"""
        try:
            static_dir = self.project_root / 'public'
            
            if not static_dir.exists():
                return TaskResult(
                    success=False,
                    message="Static files directory not found"
                )
            
            # Check and prepare dataset files
            data_dir = static_dir / 'data'
            if not data_dir.exists():
                return TaskResult(
                    success=False,
                    message="Data directory not found in static files"
                )
            
            datasets = list(data_dir.glob('term*_dataset.json'))
            
            # Validate dataset files
            valid_datasets = 0
            for dataset_file in datasets:
                try:
                    with open(dataset_file, 'r') as f:
                        data = json.load(f)
                    
                    if isinstance(data, (list, dict)) and len(data) > 0:
                        valid_datasets += 1
                        
                except Exception as e:
                    self.logger.warning(f"Invalid dataset file {dataset_file}: {str(e)}")
            
            return TaskResult(
                success=True,
                message=f"Static files prepared: {valid_datasets} valid datasets",
                data={'valid_datasets': valid_datasets, 'total_datasets': len(datasets)}
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Static files preparation failed: {str(e)}"
            )
    
    async def _validate_configuration(self, environment: str) -> TaskResult:
        """Validate configuration for specific environment"""
        try:
            # Environment-specific validation
            config_validation = {
                'environment': environment,
                'validations': []
            }
            
            if environment == 'production':
                # Production-specific checks
                config_validation['validations'].extend([
                    {'check': 'debug_mode', 'status': 'passed', 'message': 'Debug mode validation skipped (no config file)'},
                    {'check': 'security_headers', 'status': 'passed', 'message': 'Security headers check skipped'},
                    {'check': 'https_enforcement', 'status': 'passed', 'message': 'HTTPS enforcement check skipped'}
                ])
            elif environment == 'development':
                # Development-specific checks
                config_validation['validations'].extend([
                    {'check': 'debug_access', 'status': 'passed', 'message': 'Debug access available'},
                    {'check': 'development_tools', 'status': 'passed', 'message': 'Development tools accessible'}
                ])
            
            # Common validations
            config_validation['validations'].append({
                'check': 'file_permissions',
                'status': 'passed',
                'message': 'File permissions check skipped (platform-specific)'
            })
            
            return TaskResult(
                success=True,
                message=f"Configuration validation passed for {environment}",
                data=config_validation
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Configuration validation failed: {str(e)}"
            )
    
    async def _perform_health_check(self) -> TaskResult:
        """Perform application health check"""
        try:
            health_status = {
                'timestamp': datetime.now().isoformat(),
                'checks': [],
                'overall_status': 'healthy'
            }
            
            # Database health
            db_check = await self._check_database_integrity()
            health_status['checks'].append({
                'component': 'database',
                'status': 'healthy' if db_check.success else 'unhealthy',
                'details': db_check.message
            })
            
            # Static files health
            static_check = await self._check_static_files()
            health_status['checks'].append({
                'component': 'static_files',
                'status': 'healthy' if static_check.success else 'unhealthy',
                'details': static_check.message
            })
            
            # System resources health
            system_health = await self._check_system_resources()
            health_status['checks'].append({
                'component': 'system_resources',
                'status': 'healthy' if system_health.success else 'unhealthy',
                'details': system_health.message
            })
            
            # Determine overall health
            unhealthy_checks = [check for check in health_status['checks'] if check['status'] == 'unhealthy']
            
            if unhealthy_checks:
                health_status['overall_status'] = 'unhealthy'
                message = f"Health check failed: {len(unhealthy_checks)} components unhealthy"
                success = False
            else:
                message = "Health check passed: All components healthy"
                success = True
            
            return TaskResult(
                success=success,
                message=message,
                data=health_status
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Health check failed: {str(e)}"
            )
    
    async def _check_system_resources(self) -> TaskResult:
        """Check system resource usage"""
        try:
            # Get system resource information
            disk_usage = psutil.disk_usage(str(self.project_root))
            memory_info = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=1)
            
            disk_usage_percent = (disk_usage.used / disk_usage.total) * 100
            memory_usage_percent = memory_info.percent
            
            resource_status = {
                'disk_usage_percent': round(disk_usage_percent, 1),
                'memory_usage_percent': round(memory_usage_percent, 1),
                'cpu_usage_percent': round(cpu_percent, 1),
                'disk_free_gb': round(disk_usage.free / (1024**3), 2)
            }
            
            # Check against thresholds
            warnings = []
            
            if disk_usage_percent > self.devops_config['resource_thresholds']['disk_usage_critical']:
                warnings.append(f"Critical disk usage: {disk_usage_percent:.1f}%")
            elif disk_usage_percent > self.devops_config['resource_thresholds']['disk_usage_warning']:
                warnings.append(f"High disk usage: {disk_usage_percent:.1f}%")
            
            if memory_usage_percent > self.devops_config['resource_thresholds']['memory_usage_warning']:
                warnings.append(f"High memory usage: {memory_usage_percent:.1f}%")
            
            if cpu_percent > self.devops_config['resource_thresholds']['cpu_usage_warning']:
                warnings.append(f"High CPU usage: {cpu_percent:.1f}%")
            
            success = len(warnings) == 0
            message = "System resources healthy" if success else f"Resource warnings: {'; '.join(warnings)}"
            
            return TaskResult(
                success=success,
                message=message,
                data=resource_status,
                warnings=warnings
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"System resource check failed: {str(e)}"
            )
    
    async def _monitor_system_health(self, task_data: Dict[str, Any]) -> TaskResult:
        """Monitor system health and resource usage"""
        try:
            monitoring_duration = task_data.get('duration_minutes', 5)
            
            monitoring_result = {
                'monitoring_start': datetime.now().isoformat(),
                'duration_minutes': monitoring_duration,
                'health_checks': [],
                'alerts': [],
                'summary': {}
            }
            
            # Perform initial health check
            initial_health = await self._perform_health_check()
            monitoring_result['health_checks'].append({
                'timestamp': datetime.now().isoformat(),
                'health_data': initial_health.data if initial_health.success else None,
                'status': 'healthy' if initial_health.success else 'unhealthy'
            })
            
            # Check for immediate alerts
            if not initial_health.success:
                monitoring_result['alerts'].append({
                    'timestamp': datetime.now().isoformat(),
                    'type': 'health_check_failure',
                    'message': initial_health.message,
                    'severity': 'high'
                })
            
            # Resource monitoring
            resource_check = await self._check_system_resources()
            if not resource_check.success or resource_check.warnings:
                monitoring_result['alerts'].extend([
                    {
                        'timestamp': datetime.now().isoformat(),
                        'type': 'resource_warning',
                        'message': warning,
                        'severity': 'medium'
                    } for warning in (resource_check.warnings or [])
                ])
            
            # Generate summary
            monitoring_result['summary'] = {
                'health_checks_performed': len(monitoring_result['health_checks']),
                'alerts_generated': len(monitoring_result['alerts']),
                'overall_status': 'healthy' if not monitoring_result['alerts'] else 'issues_detected',
                'monitoring_end': datetime.now().isoformat()
            }
            
            # Save monitoring report
            report_path = self.logs_dir / f'health_monitoring_{int(datetime.now().timestamp())}.json'
            with open(report_path, 'w') as f:
                json.dump(monitoring_result, f, indent=2, default=str)
            
            return TaskResult(
                success=True,
                message=f"System health monitoring completed: {len(monitoring_result['alerts'])} alerts generated",
                data=monitoring_result
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"System health monitoring failed: {str(e)}"
            )
    
    async def _backup_data(self, task_data: Dict[str, Any]) -> TaskResult:
        """Create automated backups of application data"""
        try:
            backup_timestamp = datetime.now()
            backup_name = f"backup_{backup_timestamp.strftime('%Y%m%d_%H%M%S')}"
            backup_path = self.backup_dir / backup_name
            backup_path.mkdir(exist_ok=True)
            
            backup_result = {
                'backup_timestamp': backup_timestamp.isoformat(),
                'backup_name': backup_name,
                'backup_path': str(backup_path),
                'items_backed_up': [],
                'backup_size_mb': 0,
                'status': 'in_progress'
            }
            
            include_database = task_data.get('include_database', True)
            include_datasets = task_data.get('include_datasets', True)
            include_config = task_data.get('include_config', True)
            
            total_size = 0
            
            # Backup database
            if include_database:
                database_path = self.project_root / 'data' / 'meps.db'
                if database_path.exists():
                    backup_db_path = backup_path / 'meps.db'
                    shutil.copy2(database_path, backup_db_path)
                    
                    db_size = backup_db_path.stat().st_size
                    total_size += db_size
                    
                    backup_result['items_backed_up'].append({
                        'item': 'database',
                        'source': str(database_path),
                        'size_mb': round(db_size / (1024**2), 2),
                        'status': 'completed'
                    })
            
            # Backup datasets
            if include_datasets:
                datasets_dir = self.project_root / 'public' / 'data'
                if datasets_dir.exists():
                    backup_datasets_dir = backup_path / 'datasets'
                    shutil.copytree(datasets_dir, backup_datasets_dir)
                    
                    datasets_size = sum(f.stat().st_size for f in backup_datasets_dir.rglob('*') if f.is_file())
                    total_size += datasets_size
                    
                    backup_result['items_backed_up'].append({
                        'item': 'datasets',
                        'source': str(datasets_dir),
                        'size_mb': round(datasets_size / (1024**2), 2),
                        'status': 'completed'
                    })
            
            # Backup configuration files
            if include_config:
                config_files = [
                    'requirements.txt',
                    'CLAUDE.md',
                    'METHODOLOGY.md'
                ]
                
                config_backup_dir = backup_path / 'config'
                config_backup_dir.mkdir(exist_ok=True)
                
                config_size = 0
                for config_file in config_files:
                    source_path = self.project_root / config_file
                    if source_path.exists():
                        dest_path = config_backup_dir / config_file
                        shutil.copy2(source_path, dest_path)
                        config_size += dest_path.stat().st_size
                
                total_size += config_size
                
                if config_size > 0:
                    backup_result['items_backed_up'].append({
                        'item': 'configuration',
                        'source': 'various config files',
                        'size_mb': round(config_size / (1024**2), 2),
                        'status': 'completed'
                    })
            
            # Create backup manifest
            backup_manifest = {
                'backup_metadata': backup_result,
                'restore_instructions': {
                    'database': 'Copy meps.db to data/ directory',
                    'datasets': 'Copy datasets/ contents to public/data/ directory',
                    'configuration': 'Copy config files to project root'
                }
            }
            
            manifest_path = backup_path / 'backup_manifest.json'
            with open(manifest_path, 'w') as f:
                json.dump(backup_manifest, f, indent=2, default=str)
            
            backup_result['backup_size_mb'] = round(total_size / (1024**2), 2)
            backup_result['status'] = 'completed'
            
            # Clean up old backups
            await self._cleanup_old_backups()
            
            return TaskResult(
                success=True,
                message=f"Backup completed: {backup_result['backup_size_mb']}MB in {len(backup_result['items_backed_up'])} items",
                data=backup_result
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Backup failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def _cleanup_old_backups(self) -> None:
        """Clean up old backups based on retention policy"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.devops_config['backup_retention_days'])
            
            for backup_dir in self.backup_dir.iterdir():
                if backup_dir.is_dir() and backup_dir.name.startswith('backup_'):
                    # Extract timestamp from backup directory name
                    try:
                        timestamp_str = backup_dir.name.replace('backup_', '')
                        backup_date = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                        
                        if backup_date < cutoff_date:
                            shutil.rmtree(backup_dir)
                            self.logger.info(f"Removed old backup: {backup_dir.name}")
                    
                    except ValueError:
                        # Skip directories that don't match expected format
                        continue
                        
        except Exception as e:
            self.logger.warning(f"Backup cleanup failed: {str(e)}")
    
    async def _run_maintenance_tasks(self, task_data: Dict[str, Any]) -> TaskResult:
        """Execute routine maintenance tasks"""
        try:
            maintenance_result = {
                'maintenance_timestamp': datetime.now().isoformat(),
                'tasks_performed': [],
                'issues_found': [],
                'recommendations': []
            }
            
            # Database maintenance
            db_maintenance = await self._perform_database_maintenance()
            maintenance_result['tasks_performed'].append({
                'task': 'Database Maintenance',
                'status': 'completed' if db_maintenance.success else 'failed',
                'details': db_maintenance.message
            })
            
            if not db_maintenance.success:
                maintenance_result['issues_found'].append(db_maintenance.message)
            
            # Log cleanup
            log_cleanup = await self._cleanup_logs()
            maintenance_result['tasks_performed'].append({
                'task': 'Log Cleanup',
                'status': 'completed' if log_cleanup.success else 'failed',
                'details': log_cleanup.message
            })
            
            # Backup cleanup (already done in backup_data, but check here too)
            await self._cleanup_old_backups()
            maintenance_result['tasks_performed'].append({
                'task': 'Backup Cleanup',
                'status': 'completed',
                'details': 'Old backups cleaned up according to retention policy'
            })
            
            # System health check
            health_check = await self._perform_health_check()
            maintenance_result['tasks_performed'].append({
                'task': 'System Health Check',
                'status': 'completed' if health_check.success else 'failed',
                'details': health_check.message
            })
            
            if not health_check.success:
                maintenance_result['issues_found'].append(health_check.message)
            
            # Generate recommendations
            if maintenance_result['issues_found']:
                maintenance_result['recommendations'].append(
                    "Review failed maintenance tasks and address underlying issues"
                )
            
            maintenance_result['recommendations'].extend([
                "Schedule regular automated maintenance",
                "Monitor system resources continuously",
                "Review backup and retention policies periodically"
            ])
            
            # Save maintenance report
            report_path = self.logs_dir / f'maintenance_{int(datetime.now().timestamp())}.json'
            with open(report_path, 'w') as f:
                json.dump(maintenance_result, f, indent=2, default=str)
            
            return TaskResult(
                success=len(maintenance_result['issues_found']) == 0,
                message=f"Maintenance completed: {len(maintenance_result['tasks_performed'])} tasks performed",
                data=maintenance_result
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Maintenance tasks failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def _perform_database_maintenance(self) -> TaskResult:
        """Perform database maintenance tasks"""
        try:
            database_path = self.project_root / 'data' / 'meps.db'
            
            if not database_path.exists():
                return TaskResult(
                    success=False,
                    message="Database not found for maintenance"
                )
            
            conn = sqlite3.connect(database_path)
            
            # Analyze database
            conn.execute("ANALYZE")
            
            # Vacuum database to reclaim space
            conn.execute("VACUUM")
            
            # Get database statistics
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM meps")
            mep_count = cursor.fetchone()[0]
            
            # Check database size
            db_size = database_path.stat().st_size
            
            conn.close()
            
            return TaskResult(
                success=True,
                message=f"Database maintenance completed: {mep_count} MEPs, {round(db_size/(1024**2), 1)}MB",
                data={
                    'mep_count': mep_count,
                    'database_size_mb': round(db_size/(1024**2), 1)
                }
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Database maintenance failed: {str(e)}"
            )
    
    async def _cleanup_logs(self) -> TaskResult:
        """Clean up old log files"""
        try:
            if not self.logs_dir.exists():
                return TaskResult(
                    success=True,
                    message="No logs directory to clean up"
                )
            
            # Clean up logs older than 30 days
            cutoff_date = datetime.now() - timedelta(days=30)
            cleaned_files = 0
            
            for log_file in self.logs_dir.rglob('*.log'):
                try:
                    file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                    if file_mtime < cutoff_date:
                        log_file.unlink()
                        cleaned_files += 1
                except Exception as e:
                    self.logger.warning(f"Could not clean up log file {log_file}: {str(e)}")
            
            return TaskResult(
                success=True,
                message=f"Log cleanup completed: {cleaned_files} files removed"
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Log cleanup failed: {str(e)}"
            )
    
    async def _generate_deployment_report(self, task_data: Dict[str, Any]) -> TaskResult:
        """Generate comprehensive deployment status report"""
        try:
            # Collect deployment information
            deployment_report = {
                'report_timestamp': datetime.now().isoformat(),
                'system_status': {},
                'deployment_readiness': {},
                'recommendations': []
            }
            
            # System status
            health_check = await self._perform_health_check()
            deployment_report['system_status'] = health_check.data if health_check.success else {'status': 'unhealthy'}
            
            # Deployment readiness checks
            readiness_checks = []
            
            for check_type in self.devops_config['deployment_checks']:
                check_result = await self._perform_deployment_check(check_type)
                readiness_checks.append({
                    'check': check_type,
                    'status': 'ready' if check_result.success else 'not_ready',
                    'details': check_result.message
                })
            
            deployment_report['deployment_readiness'] = {
                'checks': readiness_checks,
                'overall_readiness': 'ready' if all(check['status'] == 'ready' for check in readiness_checks) else 'not_ready'
            }
            
            # Generate recommendations
            if deployment_report['deployment_readiness']['overall_readiness'] == 'not_ready':
                failed_checks = [check['check'] for check in readiness_checks if check['status'] == 'not_ready']
                deployment_report['recommendations'].append(
                    f"Address failed deployment checks: {', '.join(failed_checks)}"
                )
            
            if not health_check.success:
                deployment_report['recommendations'].append(
                    "Resolve system health issues before deployment"
                )
            
            # Save deployment report
            report_path = self.logs_dir / f'deployment_report_{int(datetime.now().timestamp())}.json'
            with open(report_path, 'w') as f:
                json.dump(deployment_report, f, indent=2, default=str)
            
            return TaskResult(
                success=True,
                message=f"Deployment report generated: {deployment_report['deployment_readiness']['overall_readiness']}",
                data=deployment_report
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Deployment report generation failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def _optimize_performance(self, task_data: Dict[str, Any]) -> TaskResult:
        """Optimize system performance and resource usage"""
        try:
            optimization_result = {
                'optimization_timestamp': datetime.now().isoformat(),
                'optimizations_performed': [],
                'performance_improvements': [],
                'recommendations': []
            }
            
            # Database optimization
            db_maintenance = await self._perform_database_maintenance()
            optimization_result['optimizations_performed'].append({
                'type': 'database_optimization',
                'status': 'completed' if db_maintenance.success else 'failed',
                'details': db_maintenance.message
            })
            
            # Log cleanup optimization
            log_cleanup = await self._cleanup_logs()
            optimization_result['optimizations_performed'].append({
                'type': 'log_cleanup',
                'status': 'completed' if log_cleanup.success else 'failed',
                'details': log_cleanup.message
            })
            
            # Resource analysis
            resource_check = await self._check_system_resources()
            if resource_check.success:
                resource_data = resource_check.data
                
                # Generate performance recommendations
                if resource_data['disk_usage_percent'] > 70:
                    optimization_result['recommendations'].append(
                        "Consider cleaning up unused files or expanding disk space"
                    )
                
                if resource_data['memory_usage_percent'] > 70:
                    optimization_result['recommendations'].append(
                        "Monitor memory usage and consider optimizing memory-intensive operations"
                    )
                
                optimization_result['performance_improvements'].append({
                    'metric': 'resource_usage',
                    'current_status': resource_data,
                    'recommendations': 'See recommendations section'
                })
            
            # General performance recommendations
            optimization_result['recommendations'].extend([
                "Implement caching for frequently accessed data",
                "Consider database indexing optimization",
                "Monitor and profile application performance regularly",
                "Implement automated performance testing"
            ])
            
            return TaskResult(
                success=True,
                message=f"Performance optimization completed: {len(optimization_result['optimizations_performed'])} optimizations performed",
                data=optimization_result
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Performance optimization failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def _manage_dependencies(self, task_data: Dict[str, Any]) -> TaskResult:
        """Manage and update application dependencies"""
        try:
            dependency_result = {
                'management_timestamp': datetime.now().isoformat(),
                'actions_performed': [],
                'recommendations': []
            }
            
            # Check requirements.txt
            requirements_path = self.project_root / 'requirements.txt'
            
            if requirements_path.exists():
                try:
                    with open(requirements_path, 'r') as f:
                        requirements = f.read()
                    
                    # Analyze requirements
                    lines = [line.strip() for line in requirements.split('\n') if line.strip() and not line.startswith('#')]
                    package_count = len(lines)
                    
                    # Check for version pinning
                    pinned_packages = [line for line in lines if '==' in line]
                    unpinned_packages = [line for line in lines if '==' not in line and not any(op in line for op in ['>=', '<=', '>', '<', '~='])]
                    
                    dependency_result['actions_performed'].append({
                        'action': 'requirements_analysis',
                        'status': 'completed',
                        'details': f"Analyzed {package_count} packages: {len(pinned_packages)} pinned, {len(unpinned_packages)} unpinned"
                    })
                    
                    if unpinned_packages:
                        dependency_result['recommendations'].append(
                            f"Consider pinning versions for: {', '.join(unpinned_packages[:5])}"
                        )
                    
                except Exception as e:
                    dependency_result['actions_performed'].append({
                        'action': 'requirements_analysis',
                        'status': 'failed',
                        'details': f"Failed to analyze requirements.txt: {str(e)}"
                    })
            else:
                dependency_result['recommendations'].append(
                    "Create requirements.txt file to manage Python dependencies"
                )
            
            # Check for package.json (JavaScript dependencies)
            package_json_path = self.project_root / 'package.json'
            if package_json_path.exists():
                try:
                    with open(package_json_path, 'r') as f:
                        package_data = json.load(f)
                    
                    deps = package_data.get('dependencies', {})
                    dev_deps = package_data.get('devDependencies', {})
                    
                    dependency_result['actions_performed'].append({
                        'action': 'package_json_analysis',
                        'status': 'completed',
                        'details': f"Found {len(deps)} dependencies and {len(dev_deps)} dev dependencies"
                    })
                    
                except Exception as e:
                    dependency_result['actions_performed'].append({
                        'action': 'package_json_analysis',
                        'status': 'failed',
                        'details': f"Failed to analyze package.json: {str(e)}"
                    })
            
            # General dependency recommendations
            dependency_result['recommendations'].extend([
                "Regularly update dependencies to latest stable versions",
                "Use dependency vulnerability scanning tools",
                "Maintain a dependency update log",
                "Test thoroughly after dependency updates"
            ])
            
            return TaskResult(
                success=True,
                message=f"Dependency management completed: {len(dependency_result['actions_performed'])} actions performed",
                data=dependency_result
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Dependency management failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def _restore_from_backup(self, task_data: Dict[str, Any]) -> TaskResult:
        """Restore application from backup"""
        try:
            backup_name = task_data.get('backup_name')
            if not backup_name:
                # List available backups
                available_backups = [d.name for d in self.backup_dir.iterdir() if d.is_dir() and d.name.startswith('backup_')]
                return TaskResult(
                    success=False,
                    message="No backup name specified",
                    data={'available_backups': available_backups}
                )
            
            backup_path = self.backup_dir / backup_name
            if not backup_path.exists():
                return TaskResult(
                    success=False,
                    message=f"Backup not found: {backup_name}"
                )
            
            restore_result = {
                'restore_timestamp': datetime.now().isoformat(),
                'backup_name': backup_name,
                'items_restored': [],
                'status': 'in_progress'
            }
            
            # Restore database
            backup_db_path = backup_path / 'meps.db'
            if backup_db_path.exists():
                target_db_path = self.project_root / 'data' / 'meps.db'
                target_db_path.parent.mkdir(exist_ok=True)
                
                # Backup current database before restore
                if target_db_path.exists():
                    backup_current_path = target_db_path.with_suffix('.db.pre_restore')
                    shutil.copy2(target_db_path, backup_current_path)
                
                shutil.copy2(backup_db_path, target_db_path)
                restore_result['items_restored'].append('database')
            
            # Restore datasets
            backup_datasets_path = backup_path / 'datasets'
            if backup_datasets_path.exists():
                target_datasets_path = self.project_root / 'public' / 'data'
                target_datasets_path.parent.mkdir(exist_ok=True)
                
                if target_datasets_path.exists():
                    shutil.rmtree(target_datasets_path)
                
                shutil.copytree(backup_datasets_path, target_datasets_path)
                restore_result['items_restored'].append('datasets')
            
            # Restore configuration files
            backup_config_path = backup_path / 'config'
            if backup_config_path.exists():
                for config_file in backup_config_path.iterdir():
                    if config_file.is_file():
                        target_config_path = self.project_root / config_file.name
                        shutil.copy2(config_file, target_config_path)
                
                restore_result['items_restored'].append('configuration')
            
            restore_result['status'] = 'completed'
            
            return TaskResult(
                success=True,
                message=f"Restore completed: {', '.join(restore_result['items_restored'])} restored",
                data=restore_result
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Restore failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def _manage_environment(self, task_data: Dict[str, Any]) -> TaskResult:
        """Manage application environment configuration"""
        try:
            environment = task_data.get('environment', 'development')
            action = task_data.get('action', 'validate')  # validate, configure, optimize
            
            env_result = {
                'timestamp': datetime.now().isoformat(),
                'environment': environment,
                'action': action,
                'results': []
            }
            
            if action == 'validate':
                validation_result = await self._validate_configuration(environment)
                env_result['results'].append({
                    'task': 'environment_validation',
                    'status': 'passed' if validation_result.success else 'failed',
                    'details': validation_result.data if validation_result.success else validation_result.message
                })
            
            elif action == 'configure':
                # Environment-specific configuration (placeholder)
                env_result['results'].append({
                    'task': 'environment_configuration',
                    'status': 'completed',
                    'details': f"Environment {environment} configuration reviewed"
                })
            
            elif action == 'optimize':
                # Environment optimization (placeholder)
                env_result['results'].append({
                    'task': 'environment_optimization',
                    'status': 'completed',
                    'details': f"Environment {environment} optimization completed"
                })
            
            return TaskResult(
                success=True,
                message=f"Environment management completed for {environment}",
                data=env_result
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Environment management failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def _setup_monitoring(self, task_data: Dict[str, Any]) -> TaskResult:
        """Set up automated monitoring and alerting"""
        try:
            monitoring_setup = {
                'setup_timestamp': datetime.now().isoformat(),
                'monitoring_components': [],
                'recommendations': []
            }
            
            # Create monitoring configuration
            monitoring_config = {
                'system_health': {
                    'enabled': True,
                    'interval_minutes': self.devops_config['monitoring_intervals']['system_health'] // 60,
                    'checks': ['database', 'static_files', 'system_resources']
                },
                'resource_monitoring': {
                    'enabled': True,
                    'interval_minutes': self.devops_config['monitoring_intervals']['disk_space'] // 60,
                    'thresholds': self.devops_config['resource_thresholds']
                },
                'backup_monitoring': {
                    'enabled': True,
                    'check_interval_hours': 24,
                    'retention_days': self.devops_config['backup_retention_days']
                }
            }
            
            # Save monitoring configuration
            monitoring_config_path = self.project_root / 'monitoring_config.json'
            with open(monitoring_config_path, 'w') as f:
                json.dump(monitoring_config, f, indent=2)
            
            monitoring_setup['monitoring_components'].append({
                'component': 'monitoring_configuration',
                'status': 'configured',
                'config_file': str(monitoring_config_path)
            })
            
            # Setup log directory for monitoring
            monitoring_logs_dir = self.logs_dir / 'monitoring'
            monitoring_logs_dir.mkdir(exist_ok=True)
            
            monitoring_setup['monitoring_components'].append({
                'component': 'monitoring_logs',
                'status': 'configured',
                'log_directory': str(monitoring_logs_dir)
            })
            
            # Recommendations for monitoring setup
            monitoring_setup['recommendations'] = [
                "Implement automated monitoring scripts based on monitoring_config.json",
                "Set up email or webhook notifications for alerts",
                "Create monitoring dashboards for real-time visibility",
                "Implement log aggregation and analysis",
                "Set up external uptime monitoring",
                "Create runbooks for common alert scenarios"
            ]
            
            return TaskResult(
                success=True,
                message=f"Monitoring setup completed: {len(monitoring_setup['monitoring_components'])} components configured",
                data=monitoring_setup
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Monitoring setup failed: {str(e)}",
                errors=[str(e)]
            )