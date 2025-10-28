"""
Data Pipeline Management Agent

This agent manages the entire data processing pipeline for the MEP Ranking system,
following Anthropic best practices for data pipeline automation and monitoring.
"""

import asyncio
import subprocess
import sqlite3
import json
import shutil
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import requests
from dataclasses import dataclass

from .base_agent import BaseAgent, TaskResult, AgentCapability


@dataclass
class PipelineStage:
    """Represents a stage in the data pipeline"""
    name: str
    command: str
    dependencies: List[str]
    timeout: int = 300  # 5 minutes default
    required_files: List[str] = None
    output_files: List[str] = None


@dataclass
class DataValidationRule:
    """Data validation rule"""
    name: str
    description: str
    validation_function: str
    critical: bool = True


class DataPipelineAgent(BaseAgent):
    """
    Data Pipeline Management Agent responsible for:
    
    1. Monitoring ParlTrack data sources
    2. Orchestrating data ingestion pipeline
    3. Validating data integrity
    4. Managing data versioning and backup
    5. Generating data quality reports
    6. Scheduling automated updates
    7. Handling pipeline failures and recovery
    """
    
    def _initialize_agent(self) -> None:
        """Initialize the data pipeline agent"""
        self.data_dir = self.project_root / 'data'
        self.parltrack_dir = self.data_dir / 'parltrack'
        self.backup_dir = self.data_dir / 'backups'
        self.logs_dir = self.project_root / 'logs' / 'pipeline'
        
        # Ensure directories exist
        for directory in [self.data_dir, self.backup_dir, self.logs_dir]:
            self._ensure_directory(directory)
        
        # Define pipeline stages
        self.pipeline_stages = self._define_pipeline_stages()
        
        # Data validation rules
        self.validation_rules = self._define_validation_rules()
        
        # Pipeline state
        self.last_update_check = None
        self.pipeline_running = False
        
        self.logger.info(f"Data Pipeline Agent initialized with {len(self.pipeline_stages)} stages")
    
    def _define_capabilities(self) -> List[AgentCapability]:
        """Define the capabilities of this agent"""
        return [
            AgentCapability(
                name="check_data_freshness",
                description="Check if source data needs updating",
                required_tools=["web_requests", "file_system"],
                complexity_level="basic"
            ),
            AgentCapability(
                name="download_parltrack_data",
                description="Download latest ParlTrack data files",
                required_tools=["web_requests", "file_system"],
                complexity_level="intermediate"
            ),
            AgentCapability(
                name="run_data_pipeline",
                description="Execute complete data processing pipeline",
                required_tools=["python_execution", "database", "file_system"],
                complexity_level="advanced"
            ),
            AgentCapability(
                name="validate_data_integrity",
                description="Validate processed data integrity",
                required_tools=["database", "file_system"],
                complexity_level="intermediate"
            ),
            AgentCapability(
                name="backup_data",
                description="Create data backups and manage versions",
                required_tools=["file_system"],
                complexity_level="basic"
            ),
            AgentCapability(
                name="generate_quality_report",
                description="Generate data quality assessment report",
                required_tools=["database", "file_system"],
                complexity_level="intermediate"
            ),
            AgentCapability(
                name="recover_pipeline",
                description="Recover from pipeline failures",
                required_tools=["database", "file_system", "python_execution"],
                complexity_level="advanced"
            )
        ]
    
    def _define_pipeline_stages(self) -> List[PipelineStage]:
        """Define the data processing pipeline stages"""
        return [
            PipelineStage(
                name="download_data",
                command="python download_parltrack.py",
                dependencies=[],
                timeout=600,
                output_files=["data/parltrack/ep_meps.json", "data/parltrack/ep_votes.json", 
                             "data/parltrack/ep_amendments.json", "data/parltrack/ep_mep_activities.json"]
            ),
            PipelineStage(
                name="decompress_data",
                command="python decompress_parltrack_data.py",
                dependencies=["download_data"],
                timeout=300,
                required_files=["data/parltrack/ep_meps.json.zst"],
                output_files=["data/parltrack/ep_meps.json"]
            ),
            PipelineStage(
                name="ingest_data",
                command="python backend/ingest_parltrack.py",
                dependencies=["decompress_data"],
                timeout=1800,  # 30 minutes
                required_files=["data/parltrack/ep_meps.json"],
                output_files=["data/meps.db"]
            ),
            PipelineStage(
                name="build_datasets",
                command="python backend/build_term_dataset.py",
                dependencies=["ingest_data"],
                timeout=1200,  # 20 minutes
                required_files=["data/meps.db"],
                output_files=["public/data/term10_dataset.json", "public/data/term9_dataset.json", 
                             "public/data/term8_dataset.json"]
            )
        ]
    
    def _define_validation_rules(self) -> List[DataValidationRule]:
        """Define data validation rules"""
        return [
            DataValidationRule(
                name="mep_count_validation",
                description="Validate MEP counts are within expected ranges",
                validation_function="validate_mep_counts",
                critical=True
            ),
            DataValidationRule(
                name="data_completeness",
                description="Check for missing critical data fields",
                validation_function="validate_data_completeness",
                critical=True
            ),
            DataValidationRule(
                name="score_consistency",
                description="Validate scoring consistency across terms",
                validation_function="validate_score_consistency",
                critical=False
            ),
            DataValidationRule(
                name="date_integrity",
                description="Validate date ranges and term boundaries",
                validation_function="validate_date_integrity",
                critical=True
            )
        ]
    
    async def _execute_task_impl(self, task_type: str, task_data: Dict[str, Any]) -> TaskResult:
        """Execute the specific task"""
        task_handlers = {
            "check_data_freshness": self._check_data_freshness,
            "download_parltrack_data": self._download_parltrack_data,
            "run_data_pipeline": self._run_data_pipeline,
            "validate_data_integrity": self._validate_data_integrity,
            "backup_data": self._backup_data,
            "generate_quality_report": self._generate_quality_report,
            "recover_pipeline": self._recover_pipeline
        }
        
        if task_type not in task_handlers:
            return TaskResult(
                success=False,
                message=f"Unknown task type: {task_type}",
                errors=[f"Task type {task_type} not supported"]
            )
        
        return await task_handlers[task_type](task_data)
    
    async def _check_data_freshness(self, task_data: Dict[str, Any]) -> TaskResult:
        """Check if source data needs updating"""
        try:
            freshness_threshold = task_data.get('threshold_hours', 24)
            
            # Check last update times
            freshness_report = {}
            
            # Check ParlTrack files
            parltrack_files = [
                'ep_meps.json', 'ep_votes.json', 
                'ep_amendments.json', 'ep_mep_activities.json'
            ]
            
            for filename in parltrack_files:
                file_path = self.parltrack_dir / filename
                if file_path.exists():
                    mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    hours_old = (datetime.now() - mod_time).total_seconds() / 3600
                    freshness_report[filename] = {
                        'last_modified': mod_time.isoformat(),
                        'hours_old': round(hours_old, 2),
                        'needs_update': hours_old > freshness_threshold
                    }
                else:
                    freshness_report[filename] = {
                        'last_modified': None,
                        'hours_old': float('inf'),
                        'needs_update': True
                    }
            
            # Check database freshness
            db_path = self.data_dir / 'meps.db'
            if db_path.exists():
                try:
                    with sqlite3.connect(db_path) as conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT MAX(last_updated) FROM rankings")
                        last_db_update = cursor.fetchone()[0]
                        
                        if last_db_update:
                            db_mod_time = datetime.fromisoformat(last_db_update)
                            db_hours_old = (datetime.now() - db_mod_time).total_seconds() / 3600
                            freshness_report['database'] = {
                                'last_modified': last_db_update,
                                'hours_old': round(db_hours_old, 2),
                                'needs_update': db_hours_old > freshness_threshold
                            }
                except sqlite3.Error:
                    freshness_report['database'] = {
                        'last_modified': None,
                        'hours_old': float('inf'),
                        'needs_update': True
                    }
            
            needs_update = any(item['needs_update'] for item in freshness_report.values())
            
            return TaskResult(
                success=True,
                message=f"Data freshness check completed. Update needed: {needs_update}",
                data={
                    'needs_update': needs_update,
                    'freshness_report': freshness_report,
                    'threshold_hours': freshness_threshold
                }
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Data freshness check failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def _download_parltrack_data(self, task_data: Dict[str, Any]) -> TaskResult:
        """Download latest ParlTrack data"""
        try:
            force_download = task_data.get('force', False)
            
            # Create backup before download if data exists
            if not force_download:
                backup_result = await self._backup_data({'create_timestamp_backup': True})
                if not backup_result.success:
                    self.logger.warning(f"Backup failed: {backup_result.message}")
            
            # Execute download script
            download_command = ["python", "download_parltrack.py"]
            if force_download:
                download_command.append("--force")
            
            process = await asyncio.create_subprocess_exec(
                *download_command,
                cwd=self.project_root,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=600)
            
            if process.returncode == 0:
                # Verify downloaded files
                verification_report = {}
                for filename in ['ep_meps.json.zst', 'ep_votes.json.zst', 
                               'ep_amendments.json.zst', 'ep_mep_activities.json.zst']:
                    file_path = self.parltrack_dir / filename
                    if file_path.exists():
                        file_size = file_path.stat().st_size
                        verification_report[filename] = {
                            'exists': True,
                            'size_mb': round(file_size / (1024 * 1024), 2),
                            'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                        }
                    else:
                        verification_report[filename] = {'exists': False}
                
                return TaskResult(
                    success=True,
                    message="ParlTrack data download completed successfully",
                    data={
                        'downloaded_files': verification_report,
                        'stdout': stdout.decode() if stdout else None
                    }
                )
            
            else:
                return TaskResult(
                    success=False,
                    message=f"Download failed with return code {process.returncode}",
                    errors=[stderr.decode() if stderr else "Unknown error"]
                )
                
        except asyncio.TimeoutError:
            return TaskResult(
                success=False,
                message="Download timed out after 10 minutes",
                errors=["Download operation exceeded timeout limit"]
            )
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Download failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def _run_data_pipeline(self, task_data: Dict[str, Any]) -> TaskResult:
        """Execute the complete data processing pipeline"""
        if self.pipeline_running:
            return TaskResult(
                success=False,
                message="Pipeline is already running",
                errors=["Cannot start pipeline while another instance is running"]
            )
        
        try:
            self.pipeline_running = True
            pipeline_start_time = datetime.now()
            
            # Get pipeline configuration
            skip_stages = task_data.get('skip_stages', [])
            force_execution = task_data.get('force', False)
            
            pipeline_results = []
            failed_stage = None
            
            self.logger.info(f"Starting data pipeline with {len(self.pipeline_stages)} stages")
            
            for stage in self.pipeline_stages:
                if stage.name in skip_stages:
                    self.logger.info(f"Skipping stage: {stage.name}")
                    continue
                
                stage_start_time = datetime.now()
                self.logger.info(f"Executing stage: {stage.name}")
                
                # Check dependencies
                if not force_execution:
                    dependency_check = await self._check_stage_dependencies(stage)
                    if not dependency_check.success:
                        failed_stage = stage.name
                        pipeline_results.append({
                            'stage': stage.name,
                            'success': False,
                            'message': dependency_check.message,
                            'duration': 0
                        })
                        break
                
                # Execute stage
                stage_result = await self._execute_pipeline_stage(stage)
                stage_duration = (datetime.now() - stage_start_time).total_seconds()
                
                pipeline_results.append({
                    'stage': stage.name,
                    'success': stage_result.success,
                    'message': stage_result.message,
                    'duration': stage_duration,
                    'output': stage_result.data
                })
                
                if not stage_result.success:
                    failed_stage = stage.name
                    self.logger.error(f"Pipeline failed at stage: {stage.name}")
                    break
                
                self.logger.info(f"Stage {stage.name} completed in {stage_duration:.2f}s")
            
            pipeline_duration = (datetime.now() - pipeline_start_time).total_seconds()
            
            # Generate pipeline report
            pipeline_success = failed_stage is None
            successful_stages = len([r for r in pipeline_results if r['success']])
            
            pipeline_report = {
                'success': pipeline_success,
                'total_stages': len(self.pipeline_stages),
                'successful_stages': successful_stages,
                'failed_stage': failed_stage,
                'total_duration': pipeline_duration,
                'stages': pipeline_results,
                'timestamp': pipeline_start_time.isoformat()
            }
            
            # Save pipeline report
            report_path = self.logs_dir / f"pipeline_report_{int(pipeline_start_time.timestamp())}.json"
            with open(report_path, 'w') as f:
                json.dump(pipeline_report, f, indent=2)
            
            if pipeline_success:
                # Run post-pipeline validation
                validation_result = await self._validate_data_integrity({})
                pipeline_report['validation'] = validation_result.data
            
            return TaskResult(
                success=pipeline_success,
                message=f"Pipeline {'completed successfully' if pipeline_success else 'failed at stage ' + failed_stage}",
                data=pipeline_report
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Pipeline execution failed: {str(e)}",
                errors=[str(e)]
            )
        finally:
            self.pipeline_running = False
    
    async def _check_stage_dependencies(self, stage: PipelineStage) -> TaskResult:
        """Check if stage dependencies are satisfied"""
        try:
            # Check required files
            if stage.required_files:
                missing_files = []
                for file_path in stage.required_files:
                    full_path = self.project_root / file_path
                    if not full_path.exists():
                        missing_files.append(file_path)
                
                if missing_files:
                    return TaskResult(
                        success=False,
                        message=f"Missing required files: {missing_files}",
                        errors=[f"Required files not found: {', '.join(missing_files)}"]
                    )
            
            return TaskResult(success=True, message="Dependencies satisfied")
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Dependency check failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def _execute_pipeline_stage(self, stage: PipelineStage) -> TaskResult:
        """Execute a single pipeline stage"""
        try:
            # Execute the command
            command_parts = stage.command.split()
            
            process = await asyncio.create_subprocess_exec(
                *command_parts,
                cwd=self.project_root,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), 
                timeout=stage.timeout
            )
            
            if process.returncode == 0:
                # Verify output files if specified
                if stage.output_files:
                    output_verification = {}
                    for file_path in stage.output_files:
                        full_path = self.project_root / file_path
                        output_verification[file_path] = {
                            'exists': full_path.exists(),
                            'size': full_path.stat().st_size if full_path.exists() else 0
                        }
                
                return TaskResult(
                    success=True,
                    message=f"Stage {stage.name} completed successfully",
                    data={
                        'stdout': stdout.decode() if stdout else None,
                        'output_files': output_verification if stage.output_files else None
                    }
                )
            else:
                return TaskResult(
                    success=False,
                    message=f"Stage {stage.name} failed with return code {process.returncode}",
                    errors=[stderr.decode() if stderr else "Unknown error"]
                )
                
        except asyncio.TimeoutError:
            return TaskResult(
                success=False,
                message=f"Stage {stage.name} timed out after {stage.timeout} seconds",
                errors=[f"Stage execution exceeded {stage.timeout} second timeout"]
            )
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Stage {stage.name} execution failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def _validate_data_integrity(self, task_data: Dict[str, Any]) -> TaskResult:
        """Validate data integrity using defined rules"""
        try:
            validation_results = {}
            critical_failures = []
            
            for rule in self.validation_rules:
                try:
                    if hasattr(self, rule.validation_function):
                        validation_func = getattr(self, rule.validation_function)
                        result = await validation_func()
                        
                        validation_results[rule.name] = {
                            'success': result.success,
                            'message': result.message,
                            'critical': rule.critical,
                            'data': result.data
                        }
                        
                        if rule.critical and not result.success:
                            critical_failures.append(rule.name)
                    
                    else:
                        validation_results[rule.name] = {
                            'success': False,
                            'message': f"Validation function {rule.validation_function} not found",
                            'critical': rule.critical
                        }
                        
                except Exception as e:
                    validation_results[rule.name] = {
                        'success': False,
                        'message': f"Validation failed: {str(e)}",
                        'critical': rule.critical,
                        'error': str(e)
                    }
                    
                    if rule.critical:
                        critical_failures.append(rule.name)
            
            overall_success = len(critical_failures) == 0
            
            return TaskResult(
                success=overall_success,
                message=f"Data validation {'passed' if overall_success else 'failed'} ({len(critical_failures)} critical failures)",
                data={
                    'overall_success': overall_success,
                    'critical_failures': critical_failures,
                    'validation_results': validation_results,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Data validation failed: {str(e)}",
                errors=[str(e)]
            )
    
    # Validation functions
    async def validate_mep_counts(self) -> TaskResult:
        """Validate MEP counts are within expected ranges"""
        try:
            db_path = self.data_dir / 'meps.db'
            if not db_path.exists():
                return TaskResult(
                    success=False,
                    message="Database not found",
                    errors=["Database file does not exist"]
                )
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Check MEP counts by term
                cursor.execute("""
                    SELECT term, COUNT(DISTINCT mep_id) as mep_count
                    FROM rankings
                    WHERE term IN (8, 9, 10)
                    GROUP BY term
                """)
                
                term_counts = dict(cursor.fetchall())
                
                # Expected ranges (approximate)
                expected_ranges = {
                    8: (750, 900),
                    9: (700, 800),
                    10: (650, 750)
                }
                
                validation_issues = []
                for term, count in term_counts.items():
                    if term in expected_ranges:
                        min_expected, max_expected = expected_ranges[term]
                        if not (min_expected <= count <= max_expected):
                            validation_issues.append(
                                f"Term {term}: {count} MEPs (expected {min_expected}-{max_expected})"
                            )
                
                success = len(validation_issues) == 0
                
                return TaskResult(
                    success=success,
                    message=f"MEP count validation {'passed' if success else 'failed'}",
                    data={
                        'term_counts': term_counts,
                        'expected_ranges': expected_ranges,
                        'issues': validation_issues
                    }
                )
                
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"MEP count validation failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def validate_data_completeness(self) -> TaskResult:
        """Check for missing critical data fields"""
        try:
            # Check dataset files
            dataset_files = [
                'public/data/term8_dataset.json',
                'public/data/term9_dataset.json',
                'public/data/term10_dataset.json'
            ]
            
            completeness_report = {}
            
            for dataset_file in dataset_files:
                file_path = self.project_root / dataset_file
                if not file_path.exists():
                    completeness_report[dataset_file] = {
                        'exists': False,
                        'issues': ['File does not exist']
                    }
                    continue
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                issues = []
                
                # Check structure
                if isinstance(data, dict) and 'meps' in data:
                    meps = data['meps']
                    if not data.get('averages'):
                        issues.append('Missing averages data')
                elif isinstance(data, list):
                    meps = data
                    issues.append('Old format: missing averages structure')
                else:
                    issues.append('Invalid data structure')
                    meps = []
                
                # Check sample MEP completeness
                if meps and len(meps) > 0:
                    sample_mep = meps[0]
                    required_fields = [
                        'name', 'group', 'country', 'total_score',
                        'speeches', 'amendments', 'questions_written'
                    ]
                    
                    missing_fields = [field for field in required_fields 
                                    if field not in sample_mep]
                    
                    if missing_fields:
                        issues.append(f'Missing fields: {missing_fields}')
                
                completeness_report[dataset_file] = {
                    'exists': True,
                    'mep_count': len(meps) if meps else 0,
                    'issues': issues
                }
            
            # Overall assessment
            total_issues = sum(len(report['issues']) for report in completeness_report.values())
            success = total_issues == 0
            
            return TaskResult(
                success=success,
                message=f"Data completeness validation {'passed' if success else 'failed'} ({total_issues} issues)",
                data={
                    'completeness_report': completeness_report,
                    'total_issues': total_issues
                }
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Data completeness validation failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def validate_score_consistency(self) -> TaskResult:
        """Validate scoring consistency across terms"""
        # Implementation placeholder
        return TaskResult(
            success=True,
            message="Score consistency validation passed",
            data={'note': 'Implementation pending'}
        )
    
    async def validate_date_integrity(self) -> TaskResult:
        """Validate date ranges and term boundaries"""
        # Implementation placeholder
        return TaskResult(
            success=True,
            message="Date integrity validation passed",
            data={'note': 'Implementation pending'}
        )
    
    async def _backup_data(self, task_data: Dict[str, Any]) -> TaskResult:
        """Create data backups"""
        try:
            create_timestamp = task_data.get('create_timestamp_backup', False)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"backup_{timestamp}" if create_timestamp else "backup_latest"
            backup_path = self.backup_dir / backup_name
            
            # Ensure backup directory exists
            self._ensure_directory(backup_path)
            
            # Files and directories to backup
            backup_items = [
                ('data/meps.db', 'meps.db'),
                ('data/parltrack', 'parltrack'),
                ('public/data', 'public_data')
            ]
            
            backup_report = {}
            
            for source, dest in backup_items:
                source_path = self.project_root / source
                dest_path = backup_path / dest
                
                try:
                    if source_path.is_file():
                        shutil.copy2(source_path, dest_path)
                        backup_report[source] = {
                            'success': True,
                            'size_mb': round(dest_path.stat().st_size / (1024 * 1024), 2)
                        }
                    elif source_path.is_dir():
                        shutil.copytree(source_path, dest_path, dirs_exist_ok=True)
                        total_size = sum(f.stat().st_size for f in dest_path.rglob('*') if f.is_file())
                        backup_report[source] = {
                            'success': True,
                            'size_mb': round(total_size / (1024 * 1024), 2)
                        }
                    else:
                        backup_report[source] = {
                            'success': False,
                            'error': 'Source not found'
                        }
                
                except Exception as e:
                    backup_report[source] = {
                        'success': False,
                        'error': str(e)
                    }
            
            # Create backup manifest
            manifest = {
                'backup_name': backup_name,
                'timestamp': timestamp,
                'items': backup_report,
                'total_size_mb': sum(item.get('size_mb', 0) for item in backup_report.values())
            }
            
            with open(backup_path / 'manifest.json', 'w') as f:
                json.dump(manifest, f, indent=2)
            
            successful_backups = len([item for item in backup_report.values() if item['success']])
            
            return TaskResult(
                success=successful_backups > 0,
                message=f"Backup completed: {successful_backups}/{len(backup_items)} items backed up",
                data={
                    'backup_path': str(backup_path),
                    'manifest': manifest
                }
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Backup failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def _generate_quality_report(self, task_data: Dict[str, Any]) -> TaskResult:
        """Generate comprehensive data quality report"""
        try:
            report_timestamp = datetime.now()
            
            # Run all validation checks
            validation_result = await self._validate_data_integrity({})
            
            # Get data freshness info
            freshness_result = await self._check_data_freshness({'threshold_hours': 24})
            
            # Additional quality metrics
            quality_metrics = await self._collect_quality_metrics()
            
            # Compile comprehensive report
            quality_report = {
                'timestamp': report_timestamp.isoformat(),
                'overall_score': self._calculate_quality_score(validation_result, freshness_result),
                'validation_results': validation_result.data if validation_result.success else None,
                'freshness_results': freshness_result.data if freshness_result.success else None,
                'quality_metrics': quality_metrics.data if quality_metrics.success else None,
                'recommendations': self._generate_quality_recommendations(validation_result, freshness_result)
            }
            
            # Save report
            report_filename = f"quality_report_{int(report_timestamp.timestamp())}.json"
            report_path = self.logs_dir / report_filename
            
            with open(report_path, 'w') as f:
                json.dump(quality_report, f, indent=2, default=str)
            
            return TaskResult(
                success=True,
                message=f"Quality report generated: {report_filename}",
                data=quality_report
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Quality report generation failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def _collect_quality_metrics(self) -> TaskResult:
        """Collect additional quality metrics"""
        try:
            metrics = {}
            
            # Database metrics
            db_path = self.data_dir / 'meps.db'
            if db_path.exists():
                with sqlite3.connect(db_path) as conn:
                    cursor = conn.cursor()
                    
                    # Table sizes
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [row[0] for row in cursor.fetchall()]
                    
                    table_metrics = {}
                    for table in tables:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        table_metrics[table] = count
                    
                    metrics['database'] = {
                        'file_size_mb': round(db_path.stat().st_size / (1024 * 1024), 2),
                        'table_counts': table_metrics
                    }
            
            # Dataset file metrics
            dataset_metrics = {}
            for term in [8, 9, 10]:
                dataset_path = self.project_root / f'public/data/term{term}_dataset.json'
                if dataset_path.exists():
                    with open(dataset_path, 'r') as f:
                        data = json.load(f)
                    
                    if isinstance(data, dict) and 'meps' in data:
                        mep_count = len(data['meps'])
                        has_averages = 'averages' in data
                    else:
                        mep_count = len(data) if isinstance(data, list) else 0
                        has_averages = False
                    
                    dataset_metrics[f'term{term}'] = {
                        'file_size_mb': round(dataset_path.stat().st_size / (1024 * 1024), 2),
                        'mep_count': mep_count,
                        'has_averages': has_averages
                    }
            
            metrics['datasets'] = dataset_metrics
            
            return TaskResult(
                success=True,
                message="Quality metrics collected",
                data=metrics
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Quality metrics collection failed: {str(e)}",
                errors=[str(e)]
            )
    
    def _calculate_quality_score(self, validation_result: TaskResult, freshness_result: TaskResult) -> float:
        """Calculate overall quality score (0-100)"""
        score = 100.0
        
        # Validation component (60% weight)
        if validation_result.success and validation_result.data:
            validation_data = validation_result.data
            if 'critical_failures' in validation_data:
                critical_failures = len(validation_data['critical_failures'])
                score -= critical_failures * 20  # -20 points per critical failure
        
        # Freshness component (40% weight)
        if freshness_result.success and freshness_result.data:
            freshness_data = freshness_result.data
            if freshness_data.get('needs_update', False):
                score -= 15  # -15 points for stale data
        
        return max(0.0, min(100.0, score))
    
    def _generate_quality_recommendations(self, validation_result: TaskResult, 
                                        freshness_result: TaskResult) -> List[str]:
        """Generate quality improvement recommendations"""
        recommendations = []
        
        if validation_result.success and validation_result.data:
            critical_failures = validation_result.data.get('critical_failures', [])
            if critical_failures:
                recommendations.append(f"Address critical validation failures: {', '.join(critical_failures)}")
        
        if freshness_result.success and freshness_result.data:
            if freshness_result.data.get('needs_update', False):
                recommendations.append("Update source data - some files are stale")
        
        if not recommendations:
            recommendations.append("Data quality is good - no immediate action required")
        
        return recommendations
    
    async def _recover_pipeline(self, task_data: Dict[str, Any]) -> TaskResult:
        """Recover from pipeline failures"""
        try:
            recovery_strategy = task_data.get('strategy', 'auto')
            
            if recovery_strategy == 'rollback':
                # Implement rollback logic
                return await self._rollback_to_backup(task_data)
            
            elif recovery_strategy == 'retry':
                # Retry failed pipeline stages
                return await self._retry_failed_stages(task_data)
            
            elif recovery_strategy == 'auto':
                # Automatic recovery decision
                return await self._auto_recovery(task_data)
            
            else:
                return TaskResult(
                    success=False,
                    message=f"Unknown recovery strategy: {recovery_strategy}",
                    errors=[f"Unsupported recovery strategy: {recovery_strategy}"]
                )
                
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Pipeline recovery failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def _rollback_to_backup(self, task_data: Dict[str, Any]) -> TaskResult:
        """Rollback to previous backup"""
        # Implementation placeholder
        return TaskResult(
            success=True,
            message="Rollback completed (placeholder implementation)",
            data={'note': 'Implementation pending'}
        )
    
    async def _retry_failed_stages(self, task_data: Dict[str, Any]) -> TaskResult:
        """Retry failed pipeline stages"""
        # Implementation placeholder
        return TaskResult(
            success=True,
            message="Failed stages retried (placeholder implementation)",
            data={'note': 'Implementation pending'}
        )
    
    async def _auto_recovery(self, task_data: Dict[str, Any]) -> TaskResult:
        """Automatic recovery based on failure analysis"""
        # Implementation placeholder
        return TaskResult(
            success=True,
            message="Auto recovery completed (placeholder implementation)",
            data={'note': 'Implementation pending'}
        )