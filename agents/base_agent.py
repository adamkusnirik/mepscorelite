"""
Base Agent Class following Anthropic Best Practices

This module provides the foundational architecture for all MEP Ranking sub-agents,
implementing Anthropic's recommended patterns for AI agent development.
"""

import abc
import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from pathlib import Path
import json


@dataclass
class TaskResult:
    """Standardized task result format"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    execution_time: Optional[float] = None
    errors: Optional[List[str]] = None
    warnings: Optional[List[str]] = None


@dataclass
class AgentCapability:
    """Agent capability definition"""
    name: str
    description: str
    required_tools: List[str]
    complexity_level: str  # 'basic', 'intermediate', 'advanced'


class BaseAgent(abc.ABC):
    """
    Base agent class implementing Anthropic best practices:
    
    1. Clear capability definitions
    2. Structured task handling
    3. Comprehensive logging
    4. Error recovery mechanisms
    5. Performance monitoring
    6. Ethical guidelines compliance
    """
    
    def __init__(self, name: str, project_root: Path, artifact_system=None):
        self.name = name
        self.project_root = Path(project_root)
        self.logger = self._setup_logging()
        self.capabilities: List[AgentCapability] = []
        self.task_history: List[Dict[str, Any]] = []
        self.performance_metrics: Dict[str, Any] = {}
        self.artifact_system = artifact_system  # Injected artifact system
        
        # Initialize agent-specific setup
        self._initialize_agent()
    
    def _setup_logging(self) -> logging.Logger:
        """Set up structured logging for the agent"""
        logger = logging.getLogger(f"mep_ranking.agents.{self.name}")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s | %(name)s | %(levelname)s | %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    @abc.abstractmethod
    def _initialize_agent(self) -> None:
        """Initialize agent-specific configurations and capabilities"""
        pass
    
    @abc.abstractmethod
    def _define_capabilities(self) -> List[AgentCapability]:
        """Define what this agent can do"""
        pass
    
    def get_capabilities(self) -> List[AgentCapability]:
        """Return agent capabilities"""
        if not self.capabilities:
            self.capabilities = self._define_capabilities()
        return self.capabilities
    
    async def execute_task(self, task_type: str, task_data: Dict[str, Any]) -> TaskResult:
        """
        Execute a task with comprehensive monitoring and error handling
        
        Args:
            task_type: Type of task to execute
            task_data: Task parameters and data
            
        Returns:
            TaskResult with execution details
        """
        start_time = time.time()
        task_id = f"{self.name}_{task_type}_{int(start_time)}"
        
        self.logger.info(f"Starting task: {task_id}")
        
        try:
            # Validate task can be handled
            if not self._can_handle_task(task_type):
                return TaskResult(
                    success=False,
                    message=f"Agent {self.name} cannot handle task type: {task_type}",
                    errors=[f"Unsupported task type: {task_type}"]
                )
            
            # Pre-task validation
            validation_result = await self._validate_task_input(task_type, task_data)
            if not validation_result.success:
                return validation_result
            
            # Execute the actual task
            result = await self._execute_task_impl(task_type, task_data)
            
            # Post-task cleanup and validation
            await self._post_task_cleanup(task_type, task_data, result)
            
            execution_time = time.time() - start_time
            result.execution_time = execution_time
            
            # Record task in history
            self._record_task_execution(task_id, task_type, task_data, result)
            
            self.logger.info(f"Task completed: {task_id} in {execution_time:.2f}s")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_result = TaskResult(
                success=False,
                message=f"Task execution failed: {str(e)}",
                execution_time=execution_time,
                errors=[str(e)]
            )
            
            self._record_task_execution(task_id, task_type, task_data, error_result)
            self.logger.error(f"Task failed: {task_id} - {str(e)}")
            
            return error_result
    
    @abc.abstractmethod
    async def _execute_task_impl(self, task_type: str, task_data: Dict[str, Any]) -> TaskResult:
        """Implement the actual task execution logic"""
        pass
    
    def _can_handle_task(self, task_type: str) -> bool:
        """Check if this agent can handle the given task type"""
        capabilities = self.get_capabilities()
        return any(cap.name == task_type for cap in capabilities)
    
    async def _validate_task_input(self, task_type: str, task_data: Dict[str, Any]) -> TaskResult:
        """Validate task input data"""
        # Default validation - can be overridden by specific agents
        if not isinstance(task_data, dict):
            return TaskResult(
                success=False,
                message="Task data must be a dictionary",
                errors=["Invalid task data format"]
            )
        
        return TaskResult(success=True, message="Validation passed")
    
    async def _post_task_cleanup(self, task_type: str, task_data: Dict[str, Any], result: TaskResult) -> None:
        """Perform any cleanup after task execution"""
        # Update performance metrics
        if result.execution_time:
            if task_type not in self.performance_metrics:
                self.performance_metrics[task_type] = {
                    'total_executions': 0,
                    'total_time': 0.0,
                    'success_count': 0,
                    'failure_count': 0
                }
            
            metrics = self.performance_metrics[task_type]
            metrics['total_executions'] += 1
            metrics['total_time'] += result.execution_time
            
            if result.success:
                metrics['success_count'] += 1
            else:
                metrics['failure_count'] += 1
    
    def _record_task_execution(self, task_id: str, task_type: str, 
                             task_data: Dict[str, Any], result: TaskResult) -> None:
        """Record task execution for audit and analysis"""
        record = {
            'task_id': task_id,
            'task_type': task_type,
            'timestamp': datetime.now().isoformat(),
            'success': result.success,
            'execution_time': result.execution_time,
            'message': result.message
        }
        
        self.task_history.append(record)
        
        # Keep only last 100 records to prevent memory issues
        if len(self.task_history) > 100:
            self.task_history = self.task_history[-100:]
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get agent performance metrics"""
        return {
            'agent_name': self.name,
            'total_tasks': len(self.task_history),
            'task_metrics': self.performance_metrics,
            'recent_tasks': self.task_history[-10:] if self.task_history else []
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            'name': self.name,
            'status': 'active',
            'capabilities_count': len(self.get_capabilities()),
            'total_tasks_executed': len(self.task_history),
            'last_task_time': self.task_history[-1]['timestamp'] if self.task_history else None
        }
    
    def _ensure_directory(self, path: Path) -> None:
        """Ensure directory exists"""
        path.mkdir(parents=True, exist_ok=True)
    
    def _safe_file_operation(self, operation: callable, *args, **kwargs) -> TaskResult:
        """Safely perform file operations with error handling"""
        try:
            result = operation(*args, **kwargs)
            return TaskResult(
                success=True,
                message="File operation completed successfully",
                data={'result': result}
            )
        except FileNotFoundError as e:
            return TaskResult(
                success=False,
                message=f"File not found: {str(e)}",
                errors=[str(e)]
            )
        except PermissionError as e:
            return TaskResult(
                success=False,
                message=f"Permission denied: {str(e)}",
                errors=[str(e)]
            )
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"File operation failed: {str(e)}",
                errors=[str(e)]
            )
    
    # Artifact System Integration Methods (2025 Best Practices)
    
    async def create_artifact(self, 
                            artifact_type,  # ArtifactType from artifact_system
                            title: str,
                            description: str,
                            content: Dict[str, Any],
                            expires_in_hours: Optional[int] = None,
                            metadata: Optional[Dict[str, Any]] = None,
                            related_artifacts: Optional[List[str]] = None) -> Optional[str]:
        """
        Create an artifact for sharing results with other agents
        
        Returns:
            Artifact ID if successful, None if artifact system not available
        """
        if not self.artifact_system:
            self.logger.warning("Artifact system not available - cannot create artifact")
            return None
        
        try:
            artifact_id = await self.artifact_system.create_artifact(
                artifact_type=artifact_type,
                title=title,
                description=description,
                content=content,
                created_by=self.name,
                expires_in_hours=expires_in_hours,
                metadata=metadata,
                related_artifacts=related_artifacts
            )
            
            self.logger.info(f"Created artifact {artifact_id}: {title}")
            return artifact_id
            
        except Exception as e:
            self.logger.error(f"Failed to create artifact: {e}")
            return None
    
    async def get_artifact_reference(self, artifact_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a lightweight reference to an artifact (JIT loading pattern)
        
        Returns:
            Artifact reference if successful, None otherwise
        """
        if not self.artifact_system:
            return None
            
        try:
            return await self.artifact_system.get_artifact_reference(artifact_id)
        except Exception as e:
            self.logger.error(f"Failed to get artifact reference {artifact_id}: {e}")
            return None
    
    async def get_artifact_content(self, artifact_id: str) -> Optional[Dict[str, Any]]:
        """
        Get full artifact content (use sparingly to prevent token bloat)
        
        Returns:
            Artifact content if successful, None otherwise
        """
        if not self.artifact_system:
            return None
            
        try:
            return await self.artifact_system.get_artifact_content(artifact_id, self.name)
        except Exception as e:
            self.logger.error(f"Failed to get artifact content {artifact_id}: {e}")
            return None
    
    async def create_handoff_token(self,
                                 to_agent: str,
                                 artifact_refs: List[str],
                                 context_summary: str,
                                 validation_required: bool = True) -> Optional[str]:
        """
        Create a handoff token for transferring context to another agent
        
        Returns:
            Handoff token ID if successful, None otherwise
        """
        if not self.artifact_system:
            return None
            
        try:
            token_id = await self.artifact_system.create_handoff_token(
                from_agent=self.name,
                to_agent=to_agent,
                artifact_refs=artifact_refs,
                context_summary=context_summary,
                validation_required=validation_required
            )
            
            self.logger.info(f"Created handoff token {token_id} for {to_agent}")
            return token_id
            
        except Exception as e:
            self.logger.error(f"Failed to create handoff token: {e}")
            return None
    
    async def validate_handoff_token(self, token_id: str):
        """
        Validate a handoff token received from another agent
        
        Returns:
            HandoffToken if valid, None otherwise
        """
        if not self.artifact_system:
            return None
            
        try:
            return await self.artifact_system.validate_handoff_token(token_id, self.name)
        except Exception as e:
            self.logger.error(f"Failed to validate handoff token {token_id}: {e}")
            return None