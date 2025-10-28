"""
Agent Manager - Central coordination system for MEP Ranking sub-agents

This module implements a centralized agent management system following
Anthropic's best practices for multi-agent coordination and task delegation.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Type
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
import json

from .base_agent import BaseAgent, TaskResult, AgentCapability


@dataclass
class TaskRequest:
    """Standardized task request format"""
    task_type: str
    priority: int  # 1 (highest) to 5 (lowest)
    data: Dict[str, Any]
    requester: str
    deadline: Optional[datetime] = None
    dependencies: Optional[List[str]] = None


class AgentManager:
    """
    Central agent management system implementing:
    
    1. Agent lifecycle management
    2. Task routing and delegation
    3. Load balancing and performance monitoring
    4. Error handling and recovery
    5. Agent coordination and communication
    6. Resource management
    """
    
    def __init__(self, project_root: Path, artifact_system=None):
        self.project_root = Path(project_root)
        self.artifact_system = artifact_system
        self.logger = self._setup_logging()
        self.agents: Dict[str, BaseAgent] = {}
        self.task_queue: List[TaskRequest] = []
        self.active_tasks: Dict[str, TaskRequest] = {}
        self.agent_registry: Dict[str, Type[BaseAgent]] = {}
        
        # Performance and monitoring
        self.system_metrics: Dict[str, Any] = {
            'total_tasks_processed': 0,
            'active_agents': 0,
            'system_uptime': datetime.now(),
            'task_distribution': {}
        }
        
        self.logger.info("Agent Manager initialized")
    
    def _setup_logging(self) -> logging.Logger:
        """Set up structured logging for the agent manager"""
        logger = logging.getLogger("mep_ranking.agent_manager")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s | MANAGER | %(levelname)s | %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def register_agent_type(self, agent_name: str, agent_class: Type[BaseAgent]) -> None:
        """Register an agent type for later instantiation"""
        self.agent_registry[agent_name] = agent_class
        self.logger.info(f"Registered agent type: {agent_name}")
    
    async def create_agent(self, agent_name: str, agent_type: str) -> bool:
        """Create and initialize an agent instance"""
        try:
            if agent_type not in self.agent_registry:
                self.logger.error(f"Unknown agent type: {agent_type}")
                return False
            
            if agent_name in self.agents:
                self.logger.warning(f"Agent {agent_name} already exists")
                return False
            
            agent_class = self.agent_registry[agent_type]
            agent = agent_class(agent_name, self.project_root, self.artifact_system)
            
            self.agents[agent_name] = agent
            self.system_metrics['active_agents'] = len(self.agents)
            
            self.logger.info(f"Created agent: {agent_name} of type {agent_type}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create agent {agent_name}: {str(e)}")
            return False
    
    def remove_agent(self, agent_name: str) -> bool:
        """Remove an agent from the system"""
        if agent_name not in self.agents:
            self.logger.warning(f"Agent {agent_name} not found")
            return False
        
        del self.agents[agent_name]
        self.system_metrics['active_agents'] = len(self.agents)
        
        self.logger.info(f"Removed agent: {agent_name}")
        return True
    
    def get_agent_capabilities(self) -> Dict[str, List[AgentCapability]]:
        """Get capabilities of all registered agents"""
        capabilities = {}
        for agent_name, agent in self.agents.items():
            capabilities[agent_name] = agent.get_capabilities()
        return capabilities
    
    def find_capable_agents(self, task_type: str) -> List[str]:
        """Find agents capable of handling a specific task type"""
        capable_agents = []
        
        for agent_name, agent in self.agents.items():
            if agent._can_handle_task(task_type):
                capable_agents.append(agent_name)
        
        return capable_agents
    
    def select_best_agent(self, task_type: str, priority: int = 3) -> Optional[str]:
        """
        Select the best agent for a task based on:
        1. Capability to handle the task
        2. Current workload
        3. Performance history
        4. Agent specialization
        """
        capable_agents = self.find_capable_agents(task_type)
        
        if not capable_agents:
            self.logger.warning(f"No agents capable of handling task type: {task_type}")
            return None
        
        if len(capable_agents) == 1:
            return capable_agents[0]
        
        # Score agents based on performance and workload
        agent_scores = {}
        
        for agent_name in capable_agents:
            agent = self.agents[agent_name]
            metrics = agent.get_performance_metrics()
            
            # Calculate score based on multiple factors
            score = 100  # Base score
            
            # Performance factor (success rate)
            if task_type in metrics.get('task_metrics', {}):
                task_metrics = metrics['task_metrics'][task_type]
                if task_metrics['total_executions'] > 0:
                    success_rate = task_metrics['success_count'] / task_metrics['total_executions']
                    score += success_rate * 50  # Boost for high success rate
                    
                    # Average execution time factor (faster is better)
                    avg_time = task_metrics['total_time'] / task_metrics['total_executions']
                    if avg_time < 5.0:  # Less than 5 seconds is good
                        score += 20
                    elif avg_time > 30.0:  # More than 30 seconds is concerning
                        score -= 20
            
            # Current workload factor (prefer less busy agents)
            active_tasks_count = sum(1 for task in self.active_tasks.values() 
                                   if task.data.get('assigned_agent') == agent_name)
            score -= active_tasks_count * 10
            
            agent_scores[agent_name] = score
        
        # Return agent with highest score
        best_agent = max(agent_scores.items(), key=lambda x: x[1])[0]
        self.logger.debug(f"Selected agent {best_agent} for task {task_type} (scores: {agent_scores})")
        
        return best_agent
    
    async def submit_task(self, task_request: TaskRequest) -> str:
        """Submit a task for execution"""
        task_id = f"task_{int(datetime.now().timestamp())}"
        
        # Add task to queue
        self.task_queue.append(task_request)
        self.task_queue.sort(key=lambda x: x.priority)  # Sort by priority
        
        self.logger.info(f"Task {task_id} submitted: {task_request.task_type}")
        
        # Try to process immediately if possible
        await self._process_task_queue()
        
        return task_id
    
    async def _process_task_queue(self) -> None:
        """Process pending tasks in the queue"""
        processed_tasks = []
        
        for task_request in self.task_queue[:]:  # Create copy to avoid modification during iteration
            # Find best agent for the task
            best_agent_name = self.select_best_agent(task_request.task_type, task_request.priority)
            
            if best_agent_name:
                # Remove from queue and execute
                self.task_queue.remove(task_request)
                task_id = f"task_{int(datetime.now().timestamp())}"
                
                # Execute task asynchronously
                asyncio.create_task(self._execute_task_with_agent(
                    task_id, best_agent_name, task_request
                ))
                
                processed_tasks.append(task_id)
        
        if processed_tasks:
            self.logger.info(f"Dispatched {len(processed_tasks)} tasks from queue")
    
    async def _execute_task_with_agent(self, task_id: str, agent_name: str, 
                                     task_request: TaskRequest) -> TaskResult:
        """Execute a task with a specific agent"""
        try:
            self.active_tasks[task_id] = task_request
            agent = self.agents[agent_name]
            
            self.logger.info(f"Executing task {task_id} with agent {agent_name}")
            
            # Execute the task
            result = await agent.execute_task(task_request.task_type, task_request.data)
            
            # Update system metrics
            self.system_metrics['total_tasks_processed'] += 1
            
            if task_request.task_type not in self.system_metrics['task_distribution']:
                self.system_metrics['task_distribution'][task_request.task_type] = 0
            self.system_metrics['task_distribution'][task_request.task_type] += 1
            
            # Remove from active tasks
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
            
            self.logger.info(f"Task {task_id} completed: {result.success}")
            return result
            
        except Exception as e:
            self.logger.error(f"Task execution failed for {task_id}: {str(e)}")
            
            # Clean up
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
            
            return TaskResult(
                success=False,
                message=f"Task execution failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def execute_task_directly(self, agent_name: str, task_type: str, 
                                  task_data: Dict[str, Any]) -> TaskResult:
        """Execute a task directly with a specific agent"""
        if agent_name not in self.agents:
            return TaskResult(
                success=False,
                message=f"Agent {agent_name} not found",
                errors=[f"Unknown agent: {agent_name}"]
            )
        
        agent = self.agents[agent_name]
        return await agent.execute_task(task_type, task_data)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        agent_statuses = {}
        for agent_name, agent in self.agents.items():
            agent_statuses[agent_name] = agent.get_status()
        
        return {
            'system_metrics': self.system_metrics,
            'active_agents': len(self.agents),
            'queued_tasks': len(self.task_queue),
            'active_tasks': len(self.active_tasks),
            'agent_statuses': agent_statuses,
            'system_uptime_hours': (datetime.now() - self.system_metrics['system_uptime']).total_seconds() / 3600
        }
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        report = {
            'system_overview': self.get_system_status(),
            'agent_performance': {}
        }
        
        for agent_name, agent in self.agents.items():
            report['agent_performance'][agent_name] = agent.get_performance_metrics()
        
        return report
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the agent system"""
        self.logger.info("Shutting down agent system...")
        
        # Wait for active tasks to complete (with timeout)
        if self.active_tasks:
            self.logger.info(f"Waiting for {len(self.active_tasks)} active tasks to complete...")
            timeout = 60  # 60 seconds timeout
            start_time = datetime.now()
            
            while self.active_tasks and (datetime.now() - start_time).total_seconds() < timeout:
                await asyncio.sleep(1)
        
        # Clear all agents
        self.agents.clear()
        self.task_queue.clear()
        self.active_tasks.clear()
        
        self.logger.info("Agent system shutdown complete")
    
    def export_configuration(self) -> Dict[str, Any]:
        """Export current system configuration"""
        return {
            'registered_agent_types': list(self.agent_registry.keys()),
            'active_agents': list(self.agents.keys()),
            'system_metrics': self.system_metrics
        }
    
    def save_performance_data(self, filepath: Optional[Path] = None) -> bool:
        """Save performance data to file"""
        try:
            if not filepath:
                filepath = self.project_root / 'logs' / 'agent_performance.json'
            
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            performance_data = {
                'timestamp': datetime.now().isoformat(),
                'system_status': self.get_system_status(),
                'performance_report': self.get_performance_report()
            }
            
            with open(filepath, 'w') as f:
                json.dump(performance_data, f, indent=2, default=str)
            
            self.logger.info(f"Performance data saved to {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save performance data: {str(e)}")
            return False