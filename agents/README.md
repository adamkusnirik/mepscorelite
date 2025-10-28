# MEP Ranking Sub-Agents System

A sophisticated agent-based system for managing and enhancing the MEP Ranking application, built following Anthropic's best practices for AI agent development.

## 🎯 Overview

The MEP Ranking Sub-Agents System provides specialized AI agents that automate various aspects of the MEP (Member of European Parliament) Ranking application, from data pipeline management to frontend optimization and quality assurance.

## 🤖 Available Agents

### 1. Data Pipeline Agent (`data_pipeline`)
**Purpose**: Automate and monitor the entire data processing pipeline

**Key Capabilities**:
- Monitor ParlTrack data sources for updates
- Orchestrate data ingestion pipeline (download → decompress → ingest → process)
- Validate data integrity at each step
- Handle data versioning and backup
- Generate data quality reports
- Schedule automated updates

**Example Usage**:
```python
await launcher.execute_task('data_pipeline_agent', 'run_data_pipeline', {})
```

### 2. Data Validation Agent (`data_validation`)
**Purpose**: Ensure data quality and accuracy throughout the system

**Key Capabilities**:
- MEP profile completeness checking
- Activity count validation against source data
- Cross-reference validation (roles, committees, dates)
- Anomaly detection in parliamentary activities
- Historical data consistency checks
- Term boundary validation

**Example Usage**:
```python
await launcher.execute_task('data_validation_agent', 'run_comprehensive_validation', {})
```

### 3. API Performance Agent (`api_performance`)
**Purpose**: Optimize and monitor API performance

**Key Capabilities**:
- Cache management for expensive queries
- Query optimization recommendations
- API response time monitoring
- Performance bottleneck identification
- Resource usage monitoring
- Automated performance alerts

**Example Usage**:
```python
await launcher.execute_task('api_performance_agent', 'monitor_api_performance', {})
```

### 4. Frontend Enhancement Agent (`frontend_enhancement`)
**Purpose**: Improve user experience and interface quality

**Key Capabilities**:
- Component testing and validation
- Accessibility compliance checking (WCAG guidelines)
- Performance optimization (bundle size, loading times)
- Cross-browser compatibility testing
- UI/UX improvement suggestions
- Mobile responsiveness validation

**Example Usage**:
```python
await launcher.execute_task('frontend_enhancement_agent', 'check_accessibility', {})
```

### 5. Quality Assurance Agent (`qa`)
**Purpose**: Comprehensive testing automation

**Key Capabilities**:
- Unit test coverage analysis
- Integration testing automation
- End-to-end user journey testing
- Performance regression testing
- Data integrity testing
- Cross-term compatibility testing

**Example Usage**:
```python
await launcher.execute_task('qa_agent', 'run_unit_tests', {'suites': ['scoring_algorithm_tests']})
```

## 🚀 Quick Start

### 1. Installation

```bash
# Navigate to the MEP Ranking project directory
cd /path/to/mepranking

# Install required dependencies
pip install -r requirements.txt

# Additional dependencies for agents
pip install psutil  # For system monitoring
```

### 2. Basic Usage

#### Command Line Interface

```bash
# Initialize system with all agents
python -m agents.agent_launcher

# Initialize with specific agents only
python -m agents.agent_launcher --agents data_pipeline data_validation

# Run in interactive mode
python -m agents.agent_launcher --interactive

# Execute specific task
python -m agents.agent_launcher --task "data_pipeline_agent:check_data_freshness:{}"

# Run maintenance tasks
python -m agents.agent_launcher --maintenance

# Generate system report
python -m agents.agent_launcher --report
```

#### Python API

```python
import asyncio
from pathlib import Path
from agents.agent_launcher import AgentLauncher

async def main():
    # Initialize launcher
    launcher = AgentLauncher(Path('.'))
    
    # Initialize system with default agents
    await launcher.initialize_system()
    
    # Execute a task
    result = await launcher.execute_task(
        'data_validation_agent',
        'validate_mep_profiles',
        {'terms': [10]}
    )
    
    print(f"Task result: {result['message']}")
    
    # Shutdown system
    await launcher.shutdown()

# Run
asyncio.run(main())
```

## 🔧 Configuration

### Agent System Configuration

The agent system can be configured through various parameters:

```python
# Custom agent initialization
agents_to_create = ['data_pipeline', 'qa']
await launcher.initialize_system(agents_to_create)

# Task execution with priority
task_id = await launcher.submit_task_request(
    task_type='run_data_pipeline',
    task_data={'force': True},
    priority=1,  # High priority
    requester='automated_system'
)
```

### Performance Thresholds

Each agent has configurable performance thresholds:

```python
# API Performance Agent thresholds
thresholds = {
    'response_time_warning': 2.0,  # seconds
    'response_time_critical': 5.0,
    'memory_usage_warning': 80,  # percentage
    'cache_hit_rate_warning': 0.6  # 60%
}
```

## 📊 Monitoring and Reporting

### System Status

```python
# Get comprehensive system status
status = await launcher.get_system_status()
print(f"Active agents: {status['active_agents']}")
```

### Performance Reports

```python
# Generate system report
report = await launcher.generate_system_report()

# The report includes:
# - System status and metrics
# - Agent capabilities overview
# - Performance analysis
# - Maintenance recommendations
```

### Maintenance Tasks

```python
# Run automated maintenance
maintenance_result = await launcher.run_maintenance_tasks()

# Includes:
# - Data validation checks
# - Performance monitoring
# - Cache optimization
# - System health assessment
```

## 🎮 Interactive Mode

The interactive mode provides a command-line interface for real-time agent interaction:

```bash
python -m agents.agent_launcher --interactive
```

Available commands:
- `status` - Show system status
- `agents` - List active agents
- `capabilities` - Show agent capabilities
- `task <agent> <task_type> [data]` - Execute task
- `maintenance` - Run maintenance tasks
- `report` - Generate system report
- `help` - Show help
- `quit` - Exit

## 📋 Common Use Cases

### 1. Daily Data Pipeline Maintenance

```python
# Check data freshness and update if needed
freshness_result = await launcher.execute_task(
    'data_pipeline_agent',
    'check_data_freshness',
    {'threshold_hours': 24}
)

if freshness_result['data']['needs_update']:
    # Run full pipeline update
    pipeline_result = await launcher.execute_task(
        'data_pipeline_agent',
        'run_data_pipeline',
        {}
    )
```

### 2. Quality Assurance Testing

```python
# Run comprehensive testing suite
qa_results = []

# Unit tests
unit_result = await launcher.execute_task('qa_agent', 'run_unit_tests', {})
qa_results.append(unit_result)

# Integration tests
integration_result = await launcher.execute_task('qa_agent', 'run_integration_tests', {})
qa_results.append(integration_result)

# Generate QA report
report_result = await launcher.execute_task('qa_agent', 'generate_test_report', {})
```

### 3. Performance Optimization

```python
# Monitor current performance
perf_result = await launcher.execute_task(
    'api_performance_agent',
    'monitor_api_performance',
    {}
)

# Analyze bottlenecks
bottleneck_result = await launcher.execute_task(
    'api_performance_agent',
    'analyze_bottlenecks',
    {}
)

# Optimize based on findings
if bottleneck_result['data']['identified_bottlenecks']:
    optimization_result = await launcher.execute_task(
        'api_performance_agent',
        'optimize_resource_usage',
        {}
    )
```

### 4. Frontend Quality Assessment

```python
# Check accessibility compliance
accessibility_result = await launcher.execute_task(
    'frontend_enhancement_agent',
    'check_accessibility',
    {}
)

# Validate component quality
component_result = await launcher.execute_task(
    'frontend_enhancement_agent',
    'validate_components',
    {}
)

# Generate improvement suggestions
ui_suggestions = await launcher.execute_task(
    'frontend_enhancement_agent',
    'suggest_ui_improvements',
    {}
)
```

## 🔍 Troubleshooting

### Common Issues

1. **System Initialization Failed**
   ```python
   # Check project root path
   launcher = AgentLauncher(Path('/correct/path/to/mepranking'))
   
   # Verify required directories exist
   # The system will create missing log directories automatically
   ```

2. **Agent Task Execution Failed**
   ```python
   # Check agent capabilities
   capabilities = await launcher.list_agent_capabilities()
   
   # Verify task type is supported
   # Check task data format matches expectations
   ```

3. **Performance Issues**
   ```python
   # Monitor system resources
   status = await launcher.get_system_status()
   
   # Run maintenance tasks
   maintenance_result = await launcher.run_maintenance_tasks()
   ```

### Debug Mode

Enable debug logging for detailed troubleshooting:

```python
import logging
logging.getLogger('mep_ranking').setLevel(logging.DEBUG)
```

## 📁 File Structure

```
agents/
├── __init__.py                 # Package initialization
├── README.md                   # This documentation
├── agent_launcher.py           # Main launcher and CLI
├── agent_manager.py            # Central agent coordination
├── base_agent.py              # Base agent class
├── data_pipeline_agent.py     # Data pipeline management
├── data_validation_agent.py   # Data quality validation
├── api_performance_agent.py   # API performance optimization
├── frontend_enhancement_agent.py # Frontend quality improvement
└── qa_agent.py                # Quality assurance testing
```

## 🔐 Security Considerations

- All agents operate with read-only access by default
- Database modifications are logged and can be audited
- File system operations are restricted to project directory
- API calls are rate-limited and monitored
- Sensitive data is never logged or exposed

## 🚦 Best Practices

1. **Regular Maintenance**: Run maintenance tasks daily
2. **Performance Monitoring**: Monitor system metrics continuously
3. **Data Validation**: Validate data integrity after each update
4. **Testing**: Run QA tests before deploying changes
5. **Documentation**: Keep agent configurations documented
6. **Monitoring**: Use system reports for trend analysis

## 🤝 Contributing

When extending the agent system:

1. Follow the base agent pattern in `base_agent.py`
2. Implement comprehensive error handling
3. Add logging for all operations
4. Include performance metrics
5. Write comprehensive tests
6. Update documentation

## 📄 License

This agent system is part of the MEP Ranking application and follows the same licensing terms.

## 🆘 Support

For support with the agent system:

1. Check the troubleshooting section above
2. Review agent logs in the `logs/` directory
3. Run system diagnostics with `--report` flag
4. Check individual agent capabilities with `--interactive` mode

---

*Built with ❤️ following Anthropic's best practices for AI agent development*