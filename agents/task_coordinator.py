"""
Task Coordinator - Coordinates complex multi-agent tasks for application upgrades

This module handles task orchestration, agent selection, and upgrade workflow management
for the MEP Ranking application.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

from .base_agent import TaskResult


class TaskPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class UpgradeTask:
    """Represents an upgrade task for the MEP Ranking application"""
    task_id: str
    title: str
    description: str
    task_type: str
    priority: TaskPriority
    required_agents: List[str]
    dependencies: List[str]
    estimated_duration_minutes: int
    task_data: Dict[str, Any]
    status: TaskStatus = TaskStatus.PENDING
    assigned_agent: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[TaskResult] = None
    progress_notes: List[str] = None
    
    def __post_init__(self):
        if self.progress_notes is None:
            self.progress_notes = []


class TaskCoordinator:
    """
    Coordinates complex multi-agent tasks for MEP Ranking application upgrades.
    
    Handles task prioritization, agent selection, dependency management,
    and progress tracking for application enhancement requests.
    """
    
    def __init__(self, agent_launcher, project_root: Path, artifact_system=None):
        self.agent_launcher = agent_launcher
        self.project_root = Path(project_root)
        self.artifact_system = artifact_system
        self.tasks: Dict[str, UpgradeTask] = {}
        self.task_queue: List[str] = []
        self.active_tasks: Dict[str, str] = {}  # task_id -> agent_name
        self.parallel_tasks: Dict[str, List[str]] = {}  # group_id -> task_ids
        self.handoff_tokens: Dict[str, str] = {}  # token_id -> task_id
        self.logger = self._setup_logging()
        
        # Task templates for common upgrade scenarios
        self.task_templates = self._initialize_task_templates()
        
        self.logger.info("Task Coordinator initialized")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for task coordinator"""
        logger = logging.getLogger("mep_ranking.task_coordinator")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s | COORDINATOR | %(levelname)s | %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def _initialize_task_templates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize templates for common upgrade tasks"""
        return {
            "security_audit": {
                "title": "Security Audit and Remediation",
                "description": "Comprehensive security audit with vulnerability remediation",
                "task_type": "security_enhancement",
                "priority": TaskPriority.HIGH,
                "required_agents": ["security_compliance"],
                "estimated_duration_minutes": 45,
                "subtasks": [
                    "scan_security_vulnerabilities",
                    "audit_data_privacy",
                    "check_dependency_vulnerabilities",
                    "generate_security_report"
                ]
            },
            "performance_optimization": {
                "title": "Performance Analysis and Optimization",
                "description": "Analyze and optimize application performance",
                "task_type": "performance_enhancement",
                "priority": TaskPriority.MEDIUM,
                "required_agents": ["analytics_insights", "api_performance", "devops"],
                "estimated_duration_minutes": 60,
                "subtasks": [
                    "generate_performance_insights",
                    "optimize_performance",
                    "monitor_api_performance"
                ]
            },
            "data_pipeline_upgrade": {
                "title": "Data Pipeline Enhancement",
                "description": "Upgrade data ingestion and processing pipeline",
                "task_type": "data_enhancement",
                "priority": TaskPriority.HIGH,
                "required_agents": ["data_pipeline", "data_validation"],
                "estimated_duration_minutes": 90,
                "subtasks": [
                    "run_data_pipeline",
                    "run_comprehensive_validation",
                    "generate_data_quality_report"
                ]
            },
            "documentation_update": {
                "title": "Documentation Comprehensive Update",
                "description": "Update all project documentation and generate missing docs",
                "task_type": "documentation_enhancement",
                "priority": TaskPriority.MEDIUM,
                "required_agents": ["documentation"],
                "estimated_duration_minutes": 30,
                "subtasks": [
                    "analyze_documentation_completeness",
                    "generate_api_documentation",
                    "create_installation_guide",
                    "generate_user_guide"
                ]
            },
            "scoring_methodology_review": {
                "title": "Scoring Methodology Review and Optimization",
                "description": "Review and optimize MEP scoring methodology",
                "task_type": "methodology_enhancement",
                "priority": TaskPriority.MEDIUM,
                "required_agents": ["scoring_system", "analytics_insights"],
                "estimated_duration_minutes": 75,
                "subtasks": [
                    "validate_scoring_methodology",
                    "analyze_scoring_distribution",
                    "generate_scoring_transparency_report",
                    "analyze_mep_activity_trends"
                ]
            },
            "frontend_enhancement": {
                "title": "Frontend User Experience Enhancement",
                "description": "Improve frontend functionality and user experience",
                "task_type": "frontend_enhancement",
                "priority": TaskPriority.MEDIUM,
                "required_agents": ["frontend_enhancement"],
                "estimated_duration_minutes": 40,
                "subtasks": [
                    "check_accessibility",
                    "validate_components",
                    "suggest_ui_improvements"
                ]
            },
            "deployment_readiness": {
                "title": "Deployment Readiness Assessment",
                "description": "Assess and prepare application for deployment",
                "task_type": "deployment_preparation",
                "priority": TaskPriority.HIGH,
                "required_agents": ["devops", "qa"],
                "estimated_duration_minutes": 50,
                "subtasks": [
                    "deploy_application",
                    "run_maintenance_tasks",
                    "generate_deployment_report",
                    "run_unit_tests"
                ]
            },
            "comprehensive_system_upgrade": {
                "title": "Comprehensive System Upgrade",
                "description": "Full system upgrade including all enhancement areas",
                "task_type": "full_system_upgrade",
                "priority": TaskPriority.CRITICAL,
                "required_agents": [
                    "data_pipeline", "data_validation", "scoring_system",
                    "security_compliance", "documentation", "analytics_insights",
                    "devops", "qa", "frontend_enhancement", "api_performance"
                ],
                "estimated_duration_minutes": 180,
                "dependencies": [
                    "security_audit", "data_pipeline_upgrade", 
                    "performance_optimization", "documentation_update"
                ]
            }
        }
    
    async def create_task_from_request(self, request: str, priority: TaskPriority = TaskPriority.MEDIUM) -> str:
        """Create upgrade task from natural language request"""
        task_id = f"task_{int(datetime.now().timestamp())}"
        
        # Analyze request to determine task type and required agents
        task_analysis = self._analyze_upgrade_request(request)
        
        # Create task based on analysis
        task = UpgradeTask(
            task_id=task_id,
            title=task_analysis['title'],
            description=task_analysis['description'],
            task_type=task_analysis['task_type'],
            priority=priority,
            required_agents=task_analysis['required_agents'],
            dependencies=task_analysis.get('dependencies', []),
            estimated_duration_minutes=task_analysis['estimated_duration'],
            task_data=task_analysis['task_data'],
            progress_notes=[f"Task created from request: {request}"]
        )
        
        self.tasks[task_id] = task
        self.task_queue.append(task_id)
        
        self.logger.info(f"Created task {task_id}: {task.title}")
        return task_id
    
    def _analyze_upgrade_request(self, request: str) -> Dict[str, Any]:
        """Analyze natural language request to determine task parameters"""
        request_lower = request.lower()
        
        # Security-related requests
        if any(keyword in request_lower for keyword in ['security', 'vulnerability', 'audit', 'compliance', 'gdpr']):
            return {
                'title': 'Security Enhancement Request',
                'description': f'Security-related upgrade: {request}',
                'task_type': 'security_enhancement',
                'required_agents': ['security_compliance'],
                'estimated_duration': 45,
                'task_data': {'request_type': 'security', 'original_request': request}
            }
        
        # Performance-related requests
        elif any(keyword in request_lower for keyword in ['performance', 'speed', 'optimize', 'slow', 'faster']):
            return {
                'title': 'Performance Optimization Request',
                'description': f'Performance-related upgrade: {request}',
                'task_type': 'performance_enhancement',
                'required_agents': ['analytics_insights', 'api_performance', 'devops'],
                'estimated_duration': 60,
                'task_data': {'request_type': 'performance', 'original_request': request}
            }
        
        # Data-related requests
        elif any(keyword in request_lower for keyword in ['data', 'database', 'ingestion', 'pipeline', 'mep']):
            return {
                'title': 'Data System Enhancement Request',
                'description': f'Data-related upgrade: {request}',
                'task_type': 'data_enhancement',
                'required_agents': ['data_pipeline', 'data_validation'],
                'estimated_duration': 75,
                'task_data': {'request_type': 'data', 'original_request': request}
            }
        
        # Documentation requests
        elif any(keyword in request_lower for keyword in ['documentation', 'docs', 'guide', 'readme', 'manual']):
            return {
                'title': 'Documentation Enhancement Request',
                'description': f'Documentation-related upgrade: {request}',
                'task_type': 'documentation_enhancement',
                'required_agents': ['documentation'],
                'estimated_duration': 30,
                'task_data': {'request_type': 'documentation', 'original_request': request}
            }
        
        # Frontend/UI requests
        elif any(keyword in request_lower for keyword in ['frontend', 'ui', 'interface', 'user experience', 'accessibility']):
            return {
                'title': 'Frontend Enhancement Request',
                'description': f'Frontend-related upgrade: {request}',
                'task_type': 'frontend_enhancement',
                'required_agents': ['frontend_enhancement'],
                'estimated_duration': 40,
                'task_data': {'request_type': 'frontend', 'original_request': request}
            }
        
        # Scoring/methodology requests
        elif any(keyword in request_lower for keyword in ['scoring', 'methodology', 'ranking', 'calculation']):
            return {
                'title': 'Scoring System Enhancement Request',
                'description': f'Scoring-related upgrade: {request}',
                'task_type': 'methodology_enhancement',
                'required_agents': ['scoring_system', 'analytics_insights'],
                'estimated_duration': 60,
                'task_data': {'request_type': 'scoring', 'original_request': request}
            }
        
        # Deployment/DevOps requests
        elif any(keyword in request_lower for keyword in ['deploy', 'deployment', 'devops', 'maintenance', 'backup']):
            return {
                'title': 'Deployment Enhancement Request',
                'description': f'Deployment-related upgrade: {request}',
                'task_type': 'deployment_enhancement',
                'required_agents': ['devops'],
                'estimated_duration': 45,
                'task_data': {'request_type': 'deployment', 'original_request': request}
            }
        
        # General/comprehensive requests
        else:
            return {
                'title': 'General Enhancement Request',
                'description': f'General upgrade request: {request}',
                'task_type': 'general_enhancement',
                'required_agents': ['qa'],  # QA agent for general assessment
                'estimated_duration': 30,
                'task_data': {'request_type': 'general', 'original_request': request}
            }
    
    async def create_task_from_template(self, template_name: str, custom_data: Optional[Dict[str, Any]] = None) -> str:
        """Create task from predefined template"""
        if template_name not in self.task_templates:
            raise ValueError(f"Unknown task template: {template_name}")
        
        template = self.task_templates[template_name]
        task_id = f"template_{template_name}_{int(datetime.now().timestamp())}"
        
        task_data = template.get('task_data', {})
        if custom_data:
            task_data.update(custom_data)
        
        task = UpgradeTask(
            task_id=task_id,
            title=template['title'],
            description=template['description'],
            task_type=template['task_type'],
            priority=template['priority'],
            required_agents=template['required_agents'],
            dependencies=template.get('dependencies', []),
            estimated_duration_minutes=template['estimated_duration_minutes'],
            task_data=task_data,
            progress_notes=[f"Task created from template: {template_name}"]
        )
        
        self.tasks[task_id] = task
        self.task_queue.append(task_id)
        
        self.logger.info(f"Created task from template {template_name}: {task_id}")
        return task_id
    
    async def execute_task(self, task_id: str) -> TaskResult:
        """Execute a specific task"""
        if task_id not in self.tasks:
            return TaskResult(
                success=False,
                message=f"Task not found: {task_id}",
                errors=[f"Task ID {task_id} does not exist"]
            )
        
        task = self.tasks[task_id]
        
        if task.status != TaskStatus.PENDING:
            return TaskResult(
                success=False,
                message=f"Task {task_id} is not in pending status (current: {task.status.value})",
                errors=[f"Task status: {task.status.value}"]
            )
        
        # Check dependencies
        unmet_dependencies = []
        for dep_id in task.dependencies:
            if dep_id in self.tasks:
                dep_task = self.tasks[dep_id]
                if dep_task.status != TaskStatus.COMPLETED:
                    unmet_dependencies.append(dep_id)
        
        if unmet_dependencies:
            return TaskResult(
                success=False,
                message=f"Unmet dependencies: {', '.join(unmet_dependencies)}",
                errors=[f"Dependencies not completed: {unmet_dependencies}"]
            )
        
        # Start task execution
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.now()
        task.progress_notes.append(f"Task execution started at {task.started_at}")
        
        try:
            # Select best agent for the task
            selected_agent = await self._select_agent_for_task(task)
            if not selected_agent:
                task.status = TaskStatus.FAILED
                return TaskResult(
                    success=False,
                    message="No suitable agent available for task",
                    errors=["Agent selection failed"]
                )
            
            task.assigned_agent = selected_agent
            task.progress_notes.append(f"Task assigned to agent: {selected_agent}")
            self.active_tasks[task_id] = selected_agent
            
            # Execute task based on type
            if hasattr(self.task_templates.get(task.task_type.replace('_enhancement', ''), {}), 'subtasks'):
                # Multi-step task execution
                result = await self._execute_multi_step_task(task)
            else:
                # Single-step task execution
                result = await self._execute_single_step_task(task)
            
            # Update task status
            task.result = result
            task.completed_at = datetime.now()
            task.status = TaskStatus.COMPLETED if result.success else TaskStatus.FAILED
            task.progress_notes.append(f"Task completed at {task.completed_at} with status: {task.status.value}")
            
            # Remove from active tasks
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
            
            self.logger.info(f"Task {task_id} completed with status: {task.status.value}")
            return result
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            task.progress_notes.append(f"Task failed with error: {str(e)}")
            
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
            
            self.logger.error(f"Task {task_id} failed: {str(e)}")
            return TaskResult(
                success=False,
                message=f"Task execution failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def _select_agent_for_task(self, task: UpgradeTask) -> Optional[str]:
        """Select the best agent for executing a task"""
        # For now, use simple selection logic
        # In production, this could be more sophisticated based on agent load, capabilities, etc.
        
        for agent_type in task.required_agents:
            agent_name = f"{agent_type}_agent"
            
            # Check if agent is available and active
            if hasattr(self.agent_launcher, 'active_agents') and agent_name in self.agent_launcher.active_agents:
                return agent_name
        
        return None
    
    async def _execute_single_step_task(self, task: UpgradeTask) -> TaskResult:
        """Execute a single-step task"""
        agent_name = task.assigned_agent
        
        # Determine task type to execute based on task data
        task_type = self._determine_agent_task_type(task)
        
        return await self.agent_launcher.execute_task(agent_name, task_type, task.task_data)
    
    async def _execute_multi_step_task(self, task: UpgradeTask) -> TaskResult:
        """Execute a multi-step task with multiple subtasks"""
        agent_name = task.assigned_agent
        results = []
        overall_success = True
        
        # Get subtasks from template
        template_key = task.task_type.replace('_enhancement', '')
        if template_key in self.task_templates:
            subtasks = self.task_templates[template_key].get('subtasks', [])
        else:
            subtasks = [self._determine_agent_task_type(task)]
        
        for i, subtask_type in enumerate(subtasks):
            task.progress_notes.append(f"Executing subtask {i+1}/{len(subtasks)}: {subtask_type}")
            
            try:
                result = await self.agent_launcher.execute_task(agent_name, subtask_type, task.task_data)
                results.append({
                    'subtask': subtask_type,
                    'success': result.success,
                    'message': result.message,
                    'execution_time': result.execution_time
                })
                
                if not result.success:
                    overall_success = False
                    task.progress_notes.append(f"Subtask {subtask_type} failed: {result.message}")
                else:
                    task.progress_notes.append(f"Subtask {subtask_type} completed successfully")
                    
            except Exception as e:
                overall_success = False
                results.append({
                    'subtask': subtask_type,
                    'success': False,
                    'message': str(e),
                    'execution_time': 0
                })
                task.progress_notes.append(f"Subtask {subtask_type} failed with exception: {str(e)}")
        
        return TaskResult(
            success=overall_success,
            message=f"Multi-step task completed: {len([r for r in results if r['success']])}/{len(results)} subtasks successful",
            data={
                'subtask_results': results,
                'overall_success': overall_success
            }
        )
    
    def _determine_agent_task_type(self, task: UpgradeTask) -> str:
        """Determine specific agent task type based on upgrade task"""
        request_type = task.task_data.get('request_type', 'general')
        
        if request_type == 'security':
            return 'generate_security_report'
        elif request_type == 'performance':
            return 'generate_performance_insights'
        elif request_type == 'data':
            return 'run_data_pipeline'
        elif request_type == 'documentation':
            return 'analyze_documentation_completeness'
        elif request_type == 'frontend':
            return 'check_accessibility'
        elif request_type == 'scoring':
            return 'validate_scoring_methodology'
        elif request_type == 'deployment':
            return 'generate_deployment_report'
        else:
            return 'generate_test_report'  # Default QA task
    
    async def process_task_queue(self, max_concurrent: int = 3) -> Dict[str, Any]:
        """Process pending tasks in the queue"""
        processing_result = {
            'processing_start': datetime.now().isoformat(),
            'tasks_processed': [],
            'tasks_completed': 0,
            'tasks_failed': 0,
            'active_tasks': len(self.active_tasks)
        }
        
        # Process tasks up to max concurrent limit
        tasks_to_process = []
        
        for task_id in self.task_queue[:]:
            if len(self.active_tasks) >= max_concurrent:
                break
            
            if task_id in self.tasks and self.tasks[task_id].status == TaskStatus.PENDING:
                tasks_to_process.append(task_id)
                self.task_queue.remove(task_id)
        
        # Execute tasks concurrently
        if tasks_to_process:
            task_coroutines = [self.execute_task(task_id) for task_id in tasks_to_process]
            results = await asyncio.gather(*task_coroutines, return_exceptions=True)
            
            for task_id, result in zip(tasks_to_process, results):
                if isinstance(result, Exception):
                    processing_result['tasks_failed'] += 1
                    processing_result['tasks_processed'].append({
                        'task_id': task_id,
                        'status': 'failed',
                        'error': str(result)
                    })
                else:
                    if result.success:
                        processing_result['tasks_completed'] += 1
                        status = 'completed'
                    else:
                        processing_result['tasks_failed'] += 1
                        status = 'failed'
                    
                    processing_result['tasks_processed'].append({
                        'task_id': task_id,
                        'status': status,
                        'message': result.message
                    })
        
        processing_result['processing_end'] = datetime.now().isoformat()
        
        return processing_result
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed status of a specific task"""
        if task_id not in self.tasks:
            return None
        
        task = self.tasks[task_id]
        
        return {
            'task_id': task.task_id,
            'title': task.title,
            'description': task.description,
            'status': task.status.value,
            'priority': task.priority.name,
            'assigned_agent': task.assigned_agent,
            'progress': len(task.progress_notes),
            'started_at': task.started_at.isoformat() if task.started_at else None,
            'completed_at': task.completed_at.isoformat() if task.completed_at else None,
            'estimated_duration': task.estimated_duration_minutes,
            'dependencies': task.dependencies,
            'required_agents': task.required_agents,
            'latest_progress': task.progress_notes[-1] if task.progress_notes else None,
            'result_summary': {
                'success': task.result.success if task.result else None,
                'message': task.result.message if task.result else None
            } if task.result else None
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        total_tasks = len(self.tasks)
        pending_tasks = len([t for t in self.tasks.values() if t.status == TaskStatus.PENDING])
        active_tasks = len([t for t in self.tasks.values() if t.status == TaskStatus.IN_PROGRESS])
        completed_tasks = len([t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED])
        failed_tasks = len([t for t in self.tasks.values() if t.status == TaskStatus.FAILED])
        
        return {
            'system_status': {
                'total_tasks': total_tasks,
                'pending_tasks': pending_tasks,
                'active_tasks': active_tasks,
                'completed_tasks': completed_tasks,
                'failed_tasks': failed_tasks,
                'queue_length': len(self.task_queue)
            },
            'available_templates': list(self.task_templates.keys()),
            'system_initialized': hasattr(self.agent_launcher, 'system_initialized') and self.agent_launcher.system_initialized,
            'timestamp': datetime.now().isoformat()
        }
    
    # 2025 Best Practices: Parallel Execution and Handoff Token Methods
    
    async def execute_parallel_tasks(self, task_ids: List[str], group_name: str = None) -> Dict[str, TaskResult]:
        """
        Execute multiple independent tasks in parallel (2025 pattern)
        
        Args:
            task_ids: List of task IDs to execute in parallel
            group_name: Optional group name for tracking
            
        Returns:
            Dict mapping task_id to TaskResult
        """
        if not task_ids:
            return {}
        
        # Validate all tasks exist and are pending
        valid_task_ids = []
        for task_id in task_ids:
            if task_id in self.tasks and self.tasks[task_id].status == TaskStatus.PENDING:
                valid_task_ids.append(task_id)
            else:
                self.logger.warning(f"Skipping invalid task {task_id}")
        
        if not valid_task_ids:
            return {}
        
        group_id = group_name or f"parallel_group_{int(datetime.now().timestamp())}"
        self.parallel_tasks[group_id] = valid_task_ids
        
        self.logger.info(f"Starting parallel execution of {len(valid_task_ids)} tasks in group {group_id}")
        
        # Execute all tasks concurrently
        task_coroutines = [self.execute_task(task_id) for task_id in valid_task_ids]
        results = await asyncio.gather(*task_coroutines, return_exceptions=True)
        
        # Process results
        result_dict = {}
        for task_id, result in zip(valid_task_ids, results):
            if isinstance(result, Exception):
                result_dict[task_id] = TaskResult(
                    success=False,
                    message=f"Parallel execution failed: {str(result)}",
                    errors=[str(result)]
                )
                self.logger.error(f"Parallel task {task_id} failed with exception: {result}")
            else:
                result_dict[task_id] = result
                status = "completed" if result.success else "failed"
                self.logger.info(f"Parallel task {task_id} {status}")
        
        # Log summary
        successful = len([r for r in result_dict.values() if r.success])
        self.logger.info(f"Parallel group {group_id} completed: {successful}/{len(valid_task_ids)} successful")
        
        return result_dict
    
    async def create_workflow_with_handoffs(self, workflow_spec: Dict[str, Any]) -> str:
        """
        Create a workflow with agent handoffs using tokens (2025 pattern)
        
        Args:
            workflow_spec: Workflow specification with stages and handoffs
            
        Returns:
            Workflow ID
        """
        workflow_id = f"workflow_{int(datetime.now().timestamp())}"
        
        stages = workflow_spec.get('stages', [])
        if not stages:
            raise ValueError("Workflow must have at least one stage")
        
        self.logger.info(f"Creating workflow {workflow_id} with {len(stages)} stages")
        
        # Create tasks for each stage
        stage_task_ids = []
        for i, stage in enumerate(stages):
            stage_name = stage.get('name', f'stage_{i}')
            
            # Create task for this stage
            task_id = await self.create_task_from_spec({
                'title': f"Workflow {workflow_id} - {stage_name}",
                'description': stage.get('description', f'Stage {i+1} of workflow'),
                'task_type': stage.get('task_type', 'general'),
                'priority': TaskPriority.MEDIUM,
                'required_agents': stage.get('agents', []),
                'dependencies': stage_task_ids[-1:] if stage_task_ids else [],  # Depend on previous stage
                'estimated_duration_minutes': stage.get('duration', 30),
                'task_data': stage.get('data', {})
            })
            
            stage_task_ids.append(task_id)
        
        # Execute stages sequentially with handoff tokens
        workflow_results = []
        previous_artifacts = []
        
        for i, (stage, task_id) in enumerate(zip(stages, stage_task_ids)):
            stage_name = stage.get('name', f'stage_{i}')
            
            # If not first stage, create handoff token
            handoff_token = None
            if i > 0 and self.artifact_system:
                from_agent = workflow_results[-1].get('agent')
                to_agent = stage.get('agents', ['general'])[0]
                
                context_summary = f"Handoff from {stage_name} stage {i-1} to stage {i}"
                handoff_token = await self.artifact_system.create_handoff_token(
                    from_agent=from_agent,
                    to_agent=to_agent,
                    artifact_refs=previous_artifacts,
                    context_summary=context_summary
                )
                
                self.logger.info(f"Created handoff token {handoff_token} for workflow stage {i}")
            
            # Execute stage
            result = await self.execute_task(task_id)
            
            stage_result = {
                'stage': i,
                'stage_name': stage_name,
                'task_id': task_id,
                'success': result.success,
                'message': result.message,
                'handoff_token': handoff_token,
                'agent': stage.get('agents', ['general'])[0]
            }
            
            # If stage was successful and has artifact system, track artifacts
            if result.success and result.data and 'artifact_id' in result.data:
                artifact_id = result.data['artifact_id']
                previous_artifacts.append(artifact_id)
                stage_result['artifact_id'] = artifact_id
            
            workflow_results.append(stage_result)
            
            # If stage failed and workflow is not fault-tolerant, stop
            if not result.success and not workflow_spec.get('fault_tolerant', False):
                self.logger.error(f"Workflow {workflow_id} failed at stage {i}: {result.message}")
                break
        
        self.logger.info(f"Workflow {workflow_id} completed with {len(workflow_results)} stages")
        
        # Store workflow results
        workflow_data = {
            'workflow_id': workflow_id,
            'spec': workflow_spec,
            'results': workflow_results,
            'created_at': datetime.now().isoformat(),
            'status': 'completed' if all(r.get('success', False) for r in workflow_results) else 'failed'
        }
        
        # Save workflow data to artifact system if available
        if self.artifact_system:
            from .artifact_system import ArtifactType
            await self.artifact_system.create_artifact(
                artifact_type=ArtifactType.TASK_RESULT,
                title=f"Workflow Results: {workflow_id}",
                description=f"Results from workflow execution with {len(stages)} stages",
                content=workflow_data,
                created_by="task_coordinator"
            )
        
        return workflow_id
    
    async def validate_task_handoff(self, task_id: str, handoff_token_id: str, receiving_agent: str) -> bool:
        """
        Validate a handoff token for task execution (2025 pattern)
        
        Args:
            task_id: Task being handed off
            handoff_token_id: Token ID to validate
            receiving_agent: Agent receiving the handoff
            
        Returns:
            True if handoff is valid
        """
        if not self.artifact_system:
            self.logger.warning("Cannot validate handoff token - artifact system not available")
            return True  # Allow execution without validation
        
        try:
            token = await self.artifact_system.validate_handoff_token(handoff_token_id, receiving_agent)
            if not token:
                return False
            
            # Store token mapping for audit
            self.handoff_tokens[handoff_token_id] = task_id
            
            self.logger.info(f"Validated handoff token {handoff_token_id} for task {task_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Handoff token validation failed: {e}")
            return False
    
    async def create_task_from_spec(self, spec: Dict[str, Any]) -> str:
        """
        Create a task from a specification dict (helper method)
        
        Args:
            spec: Task specification dictionary
            
        Returns:
            Task ID
        """
        task_id = f"task_{int(datetime.now().timestamp())}_{len(self.tasks)}"
        
        task = UpgradeTask(
            task_id=task_id,
            title=spec['title'],
            description=spec['description'],
            task_type=spec['task_type'],
            priority=spec['priority'],
            required_agents=spec['required_agents'],
            dependencies=spec.get('dependencies', []),
            estimated_duration_minutes=spec['estimated_duration_minutes'],
            task_data=spec.get('task_data', {})
        )
        
        self.tasks[task_id] = task
        
        if not task.dependencies:
            self.task_queue.append(task_id)
        
        return task_id