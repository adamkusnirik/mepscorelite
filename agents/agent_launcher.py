"""
Agent Launcher - Main entry point for MEP Ranking Sub-Agents System

This module provides the main interface for launching and managing all MEP Ranking sub-agents,
following Anthropic best practices for agent coordination and task management.
"""

import asyncio
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

from .agent_manager import AgentManager, TaskRequest
from .data_pipeline_agent import DataPipelineAgent
from .data_validation_agent import DataValidationAgent
from .api_performance_agent import APIPerformanceAgent
from .frontend_enhancement_agent import FrontendEnhancementAgent
from .qa_agent import QAAgent
from .scoring_system_agent import ScoringSystemAgent
from .security_compliance_agent import SecurityComplianceAgent
from .documentation_agent import DocumentationAgent
from .analytics_insights_agent import AnalyticsInsightsAgent
from .devops_agent import DevOpsAgent


class AgentLauncher:
    """
    Main launcher for the MEP Ranking sub-agents system.
    
    Provides a unified interface for:
    - Agent initialization and management
    - Task delegation and execution
    - System monitoring and reporting
    - Interactive agent communication
    """
    
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        
        # Initialize artifact system for 2025 best practices
        from .artifact_system import ArtifactSystem
        self.artifact_system = ArtifactSystem(self.project_root)
        
        self.agent_manager = AgentManager(self.project_root, self.artifact_system)
        self.logger = self._setup_logging()
        
        # Available agent types
        self.available_agents = {
            'data_pipeline': DataPipelineAgent,
            'data_validation': DataValidationAgent,
            'api_performance': APIPerformanceAgent,
            'frontend_enhancement': FrontendEnhancementAgent,
            'qa': QAAgent,
            'scoring_system': ScoringSystemAgent,
            'security_compliance': SecurityComplianceAgent,
            'documentation': DocumentationAgent,
            'analytics_insights': AnalyticsInsightsAgent,
            'devops': DevOpsAgent
        }
        
        # System status
        self.system_initialized = False
        self.active_agents = {}
        
        self.logger.info("Agent Launcher initialized")
    
    def get_available_agents(self) -> List[str]:
        """Get list of available agent types"""
        return list(self.available_agents.keys())
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for the launcher"""
        logger = logging.getLogger("mep_ranking.agent_launcher")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s | LAUNCHER | %(levelname)s | %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    async def initialize_system(self, agents_to_create: Optional[List[str]] = None) -> bool:
        """Initialize the agent system with specified agents"""
        try:
            self.logger.info("Initializing MEP Ranking Sub-Agents System...")
            
            # Register all available agent types
            for agent_type, agent_class in self.available_agents.items():
                self.agent_manager.register_agent_type(agent_type, agent_class)
            
            # Create default agents if none specified
            if not agents_to_create:
                agents_to_create = [
                    'data_pipeline', 'data_validation', 'api_performance', 'qa',
                    'scoring_system', 'security_compliance', 'documentation', 
                    'analytics_insights', 'devops'
                ]
            
            # Create and initialize agents
            for agent_type in agents_to_create:
                if agent_type in self.available_agents:
                    agent_name = f"{agent_type}_agent"
                    success = await self.agent_manager.create_agent(agent_name, agent_type)
                    
                    if success:
                        self.active_agents[agent_name] = agent_type
                        self.logger.info(f"✓ Created {agent_name}")
                    else:
                        self.logger.error(f"✗ Failed to create {agent_name}")
                        return False
                else:
                    self.logger.error(f"✗ Unknown agent type: {agent_type}")
                    return False
            
            self.system_initialized = True
            self.logger.info(f"System initialized with {len(self.active_agents)} agents")
            
            return True
            
        except Exception as e:
            self.logger.error(f"System initialization failed: {str(e)}")
            return False
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        if not self.system_initialized:
            return {
                'initialized': False,
                'message': 'System not initialized'
            }
        
        status = self.agent_manager.get_system_status()
        status['launcher_info'] = {
            'active_agents': list(self.active_agents.keys()),
            'available_agent_types': list(self.available_agents.keys()),
            'project_root': str(self.project_root)
        }
        
        return status
    
    async def list_agent_capabilities(self) -> Dict[str, List[Dict[str, Any]]]:
        """List all agent capabilities"""
        if not self.system_initialized:
            return {}
        
        capabilities = {}
        
        for agent_name in self.active_agents:
            agent_capabilities = self.agent_manager.get_agent_capabilities().get(agent_name, [])
            capabilities[agent_name] = [
                {
                    'name': cap.name,
                    'description': cap.description,
                    'complexity': cap.complexity_level,
                    'required_tools': cap.required_tools
                } for cap in agent_capabilities
            ]
        
        return capabilities
    
    async def execute_task(self, agent_name: str, task_type: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task with a specific agent"""
        if not self.system_initialized:
            return {
                'success': False,
                'message': 'System not initialized',
                'error': 'Call initialize_system() first'
            }
        
        if agent_name not in self.active_agents:
            return {
                'success': False,
                'message': f'Agent {agent_name} not found',
                'error': f'Available agents: {list(self.active_agents.keys())}'
            }
        
        try:
            self.logger.info(f"Executing task {task_type} with {agent_name}")
            
            result = await self.agent_manager.execute_task_directly(agent_name, task_type, task_data)
            
            return {
                'success': result.success,
                'message': result.message,
                'data': result.data,
                'execution_time': result.execution_time,
                'errors': result.errors,
                'warnings': result.warnings
            }
            
        except Exception as e:
            self.logger.error(f"Task execution failed: {str(e)}")
            return {
                'success': False,
                'message': f'Task execution failed: {str(e)}',
                'error': str(e)
            }
    
    async def submit_task_request(self, task_type: str, task_data: Dict[str, Any], 
                                priority: int = 3, requester: str = 'user') -> str:
        """Submit a task request for automatic agent selection"""
        if not self.system_initialized:
            raise RuntimeError("System not initialized")
        
        request = TaskRequest(
            task_type=task_type,
            priority=priority,
            data=task_data,
            requester=requester
        )
        
        task_id = await self.agent_manager.submit_task(request)
        self.logger.info(f"Task request submitted: {task_id}")
        
        return task_id
    
    async def run_maintenance_tasks(self) -> Dict[str, Any]:
        """Run system maintenance tasks"""
        maintenance_results = {
            'timestamp': datetime.now().isoformat(),
            'tasks_completed': [],
            'issues_found': [],
            'recommendations': []
        }
        
        try:
            # Data validation check
            if 'data_validation_agent' in self.active_agents:
                validation_result = await self.execute_task(
                    'data_validation_agent',
                    'run_comprehensive_validation',
                    {}
                )
                
                maintenance_results['tasks_completed'].append('Data validation check')
                
                if not validation_result['success']:
                    maintenance_results['issues_found'].append(
                        f"Data validation issues: {validation_result['message']}"
                    )
                
                if validation_result.get('data', {}).get('recommendations'):
                    maintenance_results['recommendations'].extend(
                        validation_result['data']['recommendations']
                    )
            
            # Performance monitoring
            if 'api_performance_agent' in self.active_agents:
                performance_result = await self.execute_task(
                    'api_performance_agent',
                    'monitor_api_performance',
                    {}
                )
                
                maintenance_results['tasks_completed'].append('Performance monitoring')
                
                if performance_result.get('data', {}).get('analysis', {}).get('status') != 'healthy':
                    maintenance_results['issues_found'].append(
                        "Performance issues detected"
                    )
            
            # Cache optimization
            if 'api_performance_agent' in self.active_agents:
                cache_result = await self.execute_task(
                    'api_performance_agent',
                    'manage_cache',
                    {'operation': 'optimize'}
                )
                
                maintenance_results['tasks_completed'].append('Cache optimization')
            
            self.logger.info(f"Maintenance completed: {len(maintenance_results['tasks_completed'])} tasks")
            
        except Exception as e:
            self.logger.error(f"Maintenance tasks failed: {str(e)}")
            maintenance_results['issues_found'].append(f"Maintenance failure: {str(e)}")
        
        return maintenance_results
    
    async def generate_system_report(self) -> Dict[str, Any]:
        """Generate comprehensive system report"""
        if not self.system_initialized:
            return {'error': 'System not initialized'}
        
        report_timestamp = datetime.now()
        
        system_report = {
            'report_metadata': {
                'generated_at': report_timestamp.isoformat(),
                'system_version': '1.0.0',
                'project_root': str(self.project_root)
            },
            'system_status': await self.get_system_status(),
            'agent_capabilities': await self.list_agent_capabilities(),
            'performance_metrics': self.agent_manager.get_performance_report(),
            'maintenance_status': await self.run_maintenance_tasks()
        }
        
        # Save report
        reports_dir = self.project_root / 'logs' / 'system_reports'
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        report_filename = f"system_report_{int(report_timestamp.timestamp())}.json"
        report_path = reports_dir / report_filename
        
        with open(report_path, 'w') as f:
            json.dump(system_report, f, indent=2, default=str)
        
        self.logger.info(f"System report generated: {report_filename}")
        
        return system_report
    
    async def interactive_mode(self):
        """Run interactive mode for direct agent communication"""
        if not self.system_initialized:
            print("❌ System not initialized. Run initialize_system() first.")
            return
        
        print("🤖 MEP Ranking Sub-Agents System - Interactive Mode")
        print("=" * 60)
        print("Available commands:")
        print("  status          - Show system status")
        print("  agents          - List active agents")
        print("  capabilities    - Show agent capabilities")
        print("  task <agent> <task_type> [data] - Execute task")
        print("  maintenance     - Run maintenance tasks")
        print("  report          - Generate system report")
        print("  help            - Show this help")
        print("  quit            - Exit interactive mode")
        print("=" * 60)
        
        while True:
            try:
                command = input("\n🔧 > ").strip().lower()
                
                if command == 'quit' or command == 'exit':
                    break
                elif command == 'status':
                    status = await self.get_system_status()
                    print(json.dumps(status, indent=2, default=str))
                elif command == 'agents':
                    print(f"Active agents: {list(self.active_agents.keys())}")
                elif command == 'capabilities':
                    capabilities = await self.list_agent_capabilities()
                    for agent_name, caps in capabilities.items():
                        print(f"\n{agent_name}:")
                        for cap in caps:
                            print(f"  • {cap['name']}: {cap['description']}")
                elif command.startswith('task '):
                    await self._handle_interactive_task(command)
                elif command == 'maintenance':
                    print("🔧 Running maintenance tasks...")
                    maintenance_result = await self.run_maintenance_tasks()
                    print(json.dumps(maintenance_result, indent=2, default=str))
                elif command == 'report':
                    print("📊 Generating system report...")
                    report = await self.generate_system_report()
                    print(f"Report generated with {len(report.get('agent_capabilities', {}))} agents")
                elif command == 'help':
                    print("Available commands listed above. Use 'task <agent> <task_type>' for task execution.")
                else:
                    print(f"❌ Unknown command: {command}. Type 'help' for available commands.")
                    
            except KeyboardInterrupt:
                print("\n👋 Exiting interactive mode...")
                break
            except Exception as e:
                print(f"❌ Error: {str(e)}")
    
    async def _handle_interactive_task(self, command: str):
        """Handle interactive task execution"""
        try:
            parts = command.split()
            if len(parts) < 3:
                print("❌ Usage: task <agent> <task_type> [json_data]")
                return
            
            agent_name = parts[1]
            task_type = parts[2]
            task_data = {}
            
            if len(parts) > 3:
                try:
                    task_data = json.loads(' '.join(parts[3:]))
                except json.JSONDecodeError:
                    print("❌ Invalid JSON data. Using empty task data.")
            
            print(f"🚀 Executing {task_type} with {agent_name}...")
            result = await self.execute_task(agent_name, task_type, task_data)
            
            if result['success']:
                print(f"✅ {result['message']}")
                if result.get('data'):
                    print("📄 Result data available (use full command output to see details)")
            else:
                print(f"❌ {result['message']}")
                if result.get('errors'):
                    for error in result['errors']:
                        print(f"   Error: {error}")
                        
        except Exception as e:
            print(f"❌ Task execution failed: {str(e)}")
    
    async def shutdown(self):
        """Gracefully shutdown the agent system"""
        if self.system_initialized:
            self.logger.info("Shutting down agent system...")
            await self.agent_manager.shutdown()
            self.system_initialized = False
            self.active_agents.clear()
            self.logger.info("System shutdown complete")


async def main():
    """Main entry point for the agent launcher"""
    parser = argparse.ArgumentParser(description='MEP Ranking Sub-Agents System')
    parser.add_argument('--project-root', type=str, default='.', 
                       help='Project root directory')
    parser.add_argument('--agents', nargs='*', 
                       help='Agents to initialize (default: all critical agents)')
    parser.add_argument('--interactive', action='store_true',
                       help='Run in interactive mode')
    parser.add_argument('--task', type=str,
                       help='Execute specific task (format: agent:task_type:json_data)')
    parser.add_argument('--maintenance', action='store_true',
                       help='Run maintenance tasks and exit')
    parser.add_argument('--report', action='store_true',
                       help='Generate system report and exit')
    
    args = parser.parse_args()
    
    # Initialize launcher
    project_root = Path(args.project_root).resolve()
    launcher = AgentLauncher(project_root)
    
    try:
        # Initialize system
        success = await launcher.initialize_system(args.agents)
        if not success:
            print("❌ Failed to initialize agent system")
            return 1
        
        print("✅ MEP Ranking Sub-Agents System initialized successfully")
        
        # Handle different execution modes
        if args.maintenance:
            print("🔧 Running maintenance tasks...")
            maintenance_result = await launcher.run_maintenance_tasks()
            print(json.dumps(maintenance_result, indent=2, default=str))
        
        elif args.report:
            print("📊 Generating system report...")
            report = await launcher.generate_system_report()
            print(f"Report generated: {len(report.get('agent_capabilities', {}))} agents analyzed")
        
        elif args.task:
            # Execute specific task
            try:
                agent_name, task_type, task_data_str = args.task.split(':', 2)
                task_data = json.loads(task_data_str) if task_data_str else {}
                
                result = await launcher.execute_task(agent_name, task_type, task_data)
                print(json.dumps(result, indent=2, default=str))
                
            except ValueError:
                print("❌ Invalid task format. Use: agent:task_type:json_data")
                return 1
        
        elif args.interactive:
            # Run interactive mode
            await launcher.interactive_mode()
        
        else:
            # Show system status and available options
            status = await launcher.get_system_status()
            print("\n📊 System Status:")
            print(f"  Active agents: {status['active_agents']}")
            print(f"  Total tasks processed: {status['system_metrics']['total_tasks_processed']}")
            print(f"  System uptime: {status['system_uptime_hours']:.1f} hours")
            
            print("\n🤖 Available agents and capabilities:")
            capabilities = await launcher.list_agent_capabilities()
            for agent_name, caps in capabilities.items():
                print(f"\n  {agent_name}:")
                for cap in caps[:3]:  # Show first 3 capabilities
                    print(f"    • {cap['name']}: {cap['description']}")
                if len(caps) > 3:
                    print(f"    ... and {len(caps) - 3} more capabilities")
            
            print(f"\n💡 Use --interactive to enter interactive mode")
            print(f"💡 Use --help to see all available options")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n👋 System interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ System error: {str(e)}")
        return 1
    finally:
        await launcher.shutdown()


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))