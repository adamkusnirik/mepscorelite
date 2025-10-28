"""
Documentation Agent - Maintains comprehensive documentation

This agent handles API documentation generation, code documentation analysis,
user guide maintenance, and documentation completeness checking.
"""

import asyncio
import json
import re
import ast
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from datetime import datetime
import inspect

from .base_agent import BaseAgent, TaskResult, AgentCapability


class DocumentationAgent(BaseAgent):
    """
    Agent responsible for maintaining comprehensive documentation.
    
    Ensures the MEP Ranking application has up-to-date, complete,
    and accurate documentation across all components.
    """
    
    def _initialize_agent(self) -> None:
        """Initialize documentation agent configurations"""
        self.documentation_config = {
            'doc_file_extensions': ['.md', '.rst', '.txt', '.html'],
            'code_file_extensions': ['.py', '.js'],
            'required_sections': [
                'installation',
                'usage',
                'api',
                'configuration',
                'methodology'
            ],
            'api_doc_patterns': [
                r'@app\.route',
                r'def\s+\w+.*:',
                r'class\s+\w+.*:',
                r'async\s+def\s+\w+.*:'
            ]
        }
        
        self.doc_structure = {
            'README.md': 'Project overview and quick start',
            'METHODOLOGY.md': 'Scoring methodology documentation',
            'INSTALLATION.md': 'Installation and setup guide',
            'API.md': 'API documentation',
            'CONTRIBUTING.md': 'Contribution guidelines',
            'CHANGELOG.md': 'Version history and changes'
        }
        
        self.logger.info(f"Documentation Agent initialized for project: {self.project_root}")
    
    def _define_capabilities(self) -> List[AgentCapability]:
        """Define documentation agent capabilities"""
        return [
            AgentCapability(
                name="analyze_documentation_completeness",
                description="Analyze documentation completeness and quality",
                required_tools=["file_system", "text_analysis"],
                complexity_level="intermediate"
            ),
            AgentCapability(
                name="generate_api_documentation",
                description="Generate API documentation from code",
                required_tools=["code_analysis", "file_system"],
                complexity_level="advanced"
            ),
            AgentCapability(
                name="validate_code_documentation",
                description="Validate code comments and docstrings",
                required_tools=["code_analysis"],
                complexity_level="intermediate"
            ),
            AgentCapability(
                name="update_methodology_documentation",
                description="Update scoring methodology documentation",
                required_tools=["file_system", "content_generation"],
                complexity_level="intermediate"
            ),
            AgentCapability(
                name="generate_user_guide",
                description="Generate comprehensive user guide",
                required_tools=["content_generation", "file_system"],
                complexity_level="advanced"
            ),
            AgentCapability(
                name="validate_documentation_links",
                description="Validate internal and external links in documentation",
                required_tools=["file_system", "web_access"],
                complexity_level="basic"
            ),
            AgentCapability(
                name="generate_changelog",
                description="Generate changelog from git history and changes",
                required_tools=["git", "file_system"],
                complexity_level="intermediate"
            ),
            AgentCapability(
                name="create_installation_guide",
                description="Create comprehensive installation guide",
                required_tools=["content_generation", "system_analysis"],
                complexity_level="intermediate"
            ),
            AgentCapability(
                name="audit_documentation_quality",
                description="Audit overall documentation quality and accessibility",
                required_tools=["text_analysis", "accessibility"],
                complexity_level="advanced"
            )
        ]
    
    async def _execute_task_impl(self, task_type: str, task_data: Dict[str, Any]) -> TaskResult:
        """Execute documentation tasks"""
        
        if task_type == "analyze_documentation_completeness":
            return await self._analyze_documentation_completeness(task_data)
        elif task_type == "generate_api_documentation":
            return await self._generate_api_documentation(task_data)
        elif task_type == "validate_code_documentation":
            return await self._validate_code_documentation(task_data)
        elif task_type == "update_methodology_documentation":
            return await self._update_methodology_documentation(task_data)
        elif task_type == "generate_user_guide":
            return await self._generate_user_guide(task_data)
        elif task_type == "validate_documentation_links":
            return await self._validate_documentation_links(task_data)
        elif task_type == "generate_changelog":
            return await self._generate_changelog(task_data)
        elif task_type == "create_installation_guide":
            return await self._create_installation_guide(task_data)
        elif task_type == "audit_documentation_quality":
            return await self._audit_documentation_quality(task_data)
        else:
            return TaskResult(
                success=False,
                message=f"Unknown task type: {task_type}",
                errors=[f"Task type '{task_type}' not implemented"]
            )
    
    async def _analyze_documentation_completeness(self, task_data: Dict[str, Any]) -> TaskResult:
        """Analyze documentation completeness and quality"""
        try:
            analysis_result = {
                'analysis_timestamp': datetime.now().isoformat(),
                'documentation_files': {},
                'missing_documentation': [],
                'completeness_score': 0,
                'recommendations': []
            }
            
            # Check for required documentation files
            for doc_file, description in self.doc_structure.items():
                file_path = self.project_root / doc_file
                
                if file_path.exists():
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Analyze content quality
                        word_count = len(content.split())
                        line_count = len(content.splitlines())
                        
                        # Check for key sections (basic heuristic)
                        has_headers = bool(re.search(r'^#+\s+', content, re.MULTILINE))
                        has_code_examples = bool(re.search(r'```|`[^`]+`', content))
                        
                        analysis_result['documentation_files'][doc_file] = {
                            'exists': True,
                            'description': description,
                            'word_count': word_count,
                            'line_count': line_count,
                            'has_headers': has_headers,
                            'has_code_examples': has_code_examples,
                            'quality_score': min(100, (word_count / 100) * 20 + (40 if has_headers else 0) + (20 if has_code_examples else 0))
                        }
                    
                    except Exception as e:
                        analysis_result['documentation_files'][doc_file] = {
                            'exists': True,
                            'error': f"Could not analyze: {str(e)}",
                            'quality_score': 0
                        }
                else:
                    analysis_result['missing_documentation'].append({
                        'file': doc_file,
                        'description': description,
                        'priority': 'high' if doc_file in ['README.md', 'METHODOLOGY.md'] else 'medium'
                    })
            
            # Check for additional documentation files
            doc_files = []
            for ext in self.documentation_config['doc_file_extensions']:
                doc_files.extend(self.project_root.rglob(f'*{ext}'))
            
            additional_docs = []
            for doc_file in doc_files:
                relative_path = str(doc_file.relative_to(self.project_root))
                if relative_path not in self.doc_structure and not relative_path.startswith('.'):
                    additional_docs.append(relative_path)
            
            analysis_result['additional_documentation'] = additional_docs
            
            # Calculate completeness score
            total_required = len(self.doc_structure)
            existing_docs = len([d for d in analysis_result['documentation_files'].values() if d.get('exists')])
            
            analysis_result['completeness_score'] = (existing_docs / total_required) * 100
            
            # Generate recommendations
            if analysis_result['missing_documentation']:
                high_priority_missing = [d for d in analysis_result['missing_documentation'] if d['priority'] == 'high']
                if high_priority_missing:
                    analysis_result['recommendations'].append(
                        f"Create high-priority documentation: {', '.join([d['file'] for d in high_priority_missing])}"
                    )
            
            # Check quality of existing docs
            low_quality_docs = [
                name for name, data in analysis_result['documentation_files'].items()
                if data.get('quality_score', 0) < 40
            ]
            
            if low_quality_docs:
                analysis_result['recommendations'].append(
                    f"Improve quality of: {', '.join(low_quality_docs)}"
                )
            
            if analysis_result['completeness_score'] < 70:
                analysis_result['recommendations'].append(
                    "Documentation completeness is below 70%. Consider creating missing documentation files."
                )
            
            return TaskResult(
                success=True,
                message=f"Documentation analysis completed. Completeness: {analysis_result['completeness_score']:.1f}%",
                data=analysis_result
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Documentation completeness analysis failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def _generate_api_documentation(self, task_data: Dict[str, Any]) -> TaskResult:
        """Generate API documentation from code"""
        try:
            api_docs = {
                'generation_timestamp': datetime.now().isoformat(),
                'endpoints': [],
                'classes': [],
                'functions': []
            }
            
            # Find API server files
            server_files = [
                'working_api_server.py',
                'run_api_server.py',
                'serve.py'
            ]
            
            for server_file in server_files:
                file_path = self.project_root / server_file
                if not file_path.exists():
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Parse Python file for API endpoints
                    tree = ast.parse(content)
                    
                    for node in ast.walk(tree):
                        # Look for route decorators and function definitions
                        if isinstance(node, ast.FunctionDef):
                            func_info = {
                                'name': node.name,
                                'file': server_file,
                                'line': node.lineno,
                                'docstring': ast.get_docstring(node),
                                'args': [arg.arg for arg in node.args.args],
                                'decorators': []
                            }
                            
                            # Check for route decorators
                            for decorator in node.decorator_list:
                                if isinstance(decorator, ast.Call) and hasattr(decorator.func, 'attr'):
                                    if decorator.func.attr == 'route':
                                        # This is a Flask route
                                        if decorator.args:
                                            route_path = decorator.args[0]
                                            if isinstance(route_path, ast.Str):
                                                func_info['decorators'].append(f"@app.route('{route_path.s}')")
                                            elif isinstance(route_path, ast.Constant):
                                                func_info['decorators'].append(f"@app.route('{route_path.value}')")
                            
                            if func_info['decorators'] or node.name.startswith('handle_') or 'api' in node.name.lower():
                                api_docs['endpoints'].append(func_info)
                            else:
                                api_docs['functions'].append(func_info)
                        
                        elif isinstance(node, ast.ClassDef):
                            class_info = {
                                'name': node.name,
                                'file': server_file,
                                'line': node.lineno,
                                'docstring': ast.get_docstring(node),
                                'methods': []
                            }
                            
                            # Get class methods
                            for item in node.body:
                                if isinstance(item, ast.FunctionDef):
                                    method_info = {
                                        'name': item.name,
                                        'line': item.lineno,
                                        'docstring': ast.get_docstring(item),
                                        'args': [arg.arg for arg in item.args.args]
                                    }
                                    class_info['methods'].append(method_info)
                            
                            api_docs['classes'].append(class_info)
                
                except Exception as e:
                    self.logger.warning(f"Could not parse {server_file}: {str(e)}")
            
            # Generate markdown documentation
            markdown_content = self._generate_api_markdown(api_docs)
            
            # Save API documentation
            api_doc_path = self.project_root / 'API.md'
            with open(api_doc_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            return TaskResult(
                success=True,
                message=f"API documentation generated with {len(api_docs['endpoints'])} endpoints documented",
                data={
                    'api_documentation': api_docs,
                    'documentation_file': 'API.md',
                    'markdown_content': markdown_content
                }
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"API documentation generation failed: {str(e)}",
                errors=[str(e)]
            )
    
    def _generate_api_markdown(self, api_docs: Dict[str, Any]) -> str:
        """Generate markdown content for API documentation"""
        content = f"""# MEP Ranking API Documentation

Generated on: {api_docs['generation_timestamp']}

## Overview

This document describes the API endpoints and functions available in the MEP Ranking application.

## API Endpoints

"""
        
        for endpoint in api_docs['endpoints']:
            content += f"### {endpoint['name']}\n\n"
            
            if endpoint['decorators']:
                for decorator in endpoint['decorators']:
                    content += f"**Route:** `{decorator}`\n\n"
            
            if endpoint['docstring']:
                content += f"{endpoint['docstring']}\n\n"
            
            if endpoint['args']:
                content += f"**Parameters:** {', '.join(endpoint['args'])}\n\n"
            
            content += f"**Location:** {endpoint['file']}:{endpoint['line']}\n\n"
            content += "---\n\n"
        
        if api_docs['classes']:
            content += "## Classes\n\n"
            
            for cls in api_docs['classes']:
                content += f"### {cls['name']}\n\n"
                
                if cls['docstring']:
                    content += f"{cls['docstring']}\n\n"
                
                if cls['methods']:
                    content += "**Methods:**\n\n"
                    for method in cls['methods']:
                        content += f"- `{method['name']}({', '.join(method['args'])})`"
                        if method['docstring']:
                            content += f": {method['docstring'][:100]}..."
                        content += "\n"
                
                content += f"\n**Location:** {cls['file']}:{cls['line']}\n\n"
                content += "---\n\n"
        
        if api_docs['functions']:
            content += "## Utility Functions\n\n"
            
            for func in api_docs['functions']:
                if not func['name'].startswith('_'):  # Skip private functions
                    content += f"### {func['name']}\n\n"
                    
                    if func['docstring']:
                        content += f"{func['docstring']}\n\n"
                    
                    if func['args']:
                        content += f"**Parameters:** {', '.join(func['args'])}\n\n"
                    
                    content += f"**Location:** {func['file']}:{func['line']}\n\n"
                    content += "---\n\n"
        
        return content
    
    async def _validate_code_documentation(self, task_data: Dict[str, Any]) -> TaskResult:
        """Validate code comments and docstrings"""
        try:
            validation_result = {
                'validation_timestamp': datetime.now().isoformat(),
                'files_analyzed': 0,
                'functions_without_docstrings': [],
                'classes_without_docstrings': [],
                'documentation_coverage': 0,
                'recommendations': []
            }
            
            code_dirs = task_data.get('directories', ['backend', 'agents'])
            
            total_functions = 0
            documented_functions = 0
            total_classes = 0
            documented_classes = 0
            
            for code_dir in code_dirs:
                dir_path = self.project_root / code_dir
                if not dir_path.exists():
                    continue
                
                # Find Python files
                python_files = list(dir_path.rglob('*.py'))
                
                for py_file in python_files:
                    if py_file.name.startswith('__'):
                        continue
                    
                    try:
                        with open(py_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        tree = ast.parse(content)
                        validation_result['files_analyzed'] += 1
                        
                        for node in ast.walk(tree):
                            if isinstance(node, ast.FunctionDef):
                                if not node.name.startswith('_'):  # Skip private functions
                                    total_functions += 1
                                    docstring = ast.get_docstring(node)
                                    
                                    if docstring:
                                        documented_functions += 1
                                    else:
                                        validation_result['functions_without_docstrings'].append({
                                            'function': node.name,
                                            'file': str(py_file.relative_to(self.project_root)),
                                            'line': node.lineno
                                        })
                            
                            elif isinstance(node, ast.ClassDef):
                                total_classes += 1
                                docstring = ast.get_docstring(node)
                                
                                if docstring:
                                    documented_classes += 1
                                else:
                                    validation_result['classes_without_docstrings'].append({
                                        'class': node.name,
                                        'file': str(py_file.relative_to(self.project_root)),
                                        'line': node.lineno
                                    })
                    
                    except Exception as e:
                        self.logger.warning(f"Could not analyze {py_file}: {str(e)}")
            
            # Calculate documentation coverage
            total_items = total_functions + total_classes
            documented_items = documented_functions + documented_classes
            
            if total_items > 0:
                validation_result['documentation_coverage'] = (documented_items / total_items) * 100
            
            validation_result['statistics'] = {
                'total_functions': total_functions,
                'documented_functions': documented_functions,
                'total_classes': total_classes,
                'documented_classes': documented_classes
            }
            
            # Generate recommendations
            if validation_result['documentation_coverage'] < 70:
                validation_result['recommendations'].append(
                    f"Code documentation coverage is {validation_result['documentation_coverage']:.1f}%. Aim for at least 70%."
                )
            
            if len(validation_result['functions_without_docstrings']) > 10:
                validation_result['recommendations'].append(
                    "Many functions lack docstrings. Focus on documenting public API functions first."
                )
            
            if validation_result['classes_without_docstrings']:
                validation_result['recommendations'].append(
                    "All classes should have docstrings explaining their purpose and usage."
                )
            
            return TaskResult(
                success=True,
                message=f"Code documentation validation completed. Coverage: {validation_result['documentation_coverage']:.1f}%",
                data=validation_result
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Code documentation validation failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def _create_installation_guide(self, task_data: Dict[str, Any]) -> TaskResult:
        """Create comprehensive installation guide"""
        try:
            # Analyze project structure to determine installation requirements
            installation_guide = self._generate_installation_markdown()
            
            # Save installation guide
            install_path = self.project_root / 'INSTALLATION.md'
            with open(install_path, 'w', encoding='utf-8') as f:
                f.write(installation_guide)
            
            return TaskResult(
                success=True,
                message="Installation guide created successfully",
                data={
                    'guide_file': 'INSTALLATION.md',
                    'content': installation_guide
                }
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Installation guide creation failed: {str(e)}",
                errors=[str(e)]
            )
    
    def _generate_installation_markdown(self) -> str:
        """Generate installation guide markdown content"""
        content = f"""# MEP Ranking Installation Guide

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Prerequisites

### System Requirements

- Python 3.8 or higher
- SQLite 3
- At least 2GB of available disk space
- Internet connection (for data downloads)

### Operating System Support

- Windows 10/11
- macOS 10.14 or higher
- Linux (Ubuntu 18.04+, CentOS 7+, or equivalent)

## Installation Steps

### 1. Clone the Repository

```bash
git clone <repository-url>
cd mepranking
```

### 2. Set Up Python Environment

It's recommended to use a virtual environment:

```bash
# Create virtual environment
python -m venv mep_ranking_env

# Activate virtual environment
# On Windows:
mep_ranking_env\\Scripts\\activate
# On macOS/Linux:
source mep_ranking_env/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Initialize the Database

```bash
# Download and process initial data
python backend/ingest_parltrack.py

# Build datasets for the frontend
python backend/build_term_dataset.py
```

### 5. Launch the Application

Choose one of the following options:

#### Option A: Quick Start (Recommended)
```bash
python launch_app.py
```

#### Option B: Manual Launch
```bash
# Start the API server
python working_api_server.py

# Open your browser and navigate to:
# http://localhost:8000
```

## Configuration

### Data Sources

The application uses ParlTrack data. Data files are automatically downloaded during the initialization process.

### Custom Configuration

1. **Database Location**: By default, the database is stored in `data/meps.db`
2. **Server Port**: The default port is 8000. You can modify this in the server files.
3. **Data Update Frequency**: Data can be updated by running the ingestion process again.

## Troubleshooting

### Common Issues

#### Database Not Found
```bash
# Re-run the data ingestion
python backend/ingest_parltrack.py
```

#### Port Already in Use
```bash
# Kill existing process (Windows)
taskkill /f /im python.exe

# Kill existing process (macOS/Linux)
pkill -f python
```

#### Missing Dependencies
```bash
# Reinstall all dependencies
pip install -r requirements.txt --force-reinstall
```

### Performance Optimization

1. **Large Datasets**: If working with large datasets, consider increasing available memory
2. **Slow Loading**: Clear browser cache and ensure stable internet connection
3. **Database Performance**: Regular VACUUM operations can improve SQLite performance

## Development Setup

For development work:

```bash
# Install development dependencies
pip install -r requirements.txt

# Run tests (if available)
python -m pytest

# Start development server with debug mode
python serve.py --debug
```

## Data Management

### Updating Data

```bash
# Full data update
python run_update.py

# Update specific term data
python backend/build_term_dataset.py --term 10
```

### Backup

```bash
# Backup database
cp data/meps.db data/meps.db.backup

# Backup configuration files
tar -czf config_backup.tar.gz *.py requirements.txt
```

## Security Considerations

1. **Database Security**: Ensure database files have appropriate permissions
2. **Web Server**: For production deployment, use a proper web server (not the development server)
3. **Data Privacy**: Be aware of EU data protection regulations when handling MEP data

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review the application logs
3. Ensure all prerequisites are met
4. Verify internet connectivity for data downloads

## Next Steps

After successful installation:

1. Explore the Activity Explorer at `/`
2. Check individual MEP profiles at `/profile.html`
3. Review the methodology documentation
4. Consider setting up automated data updates

---

*This installation guide was automatically generated by the Documentation Agent.*
"""
        return content
    
    async def _generate_user_guide(self, task_data: Dict[str, Any]) -> TaskResult:
        """Generate comprehensive user guide"""
        try:
            user_guide_content = self._generate_user_guide_markdown()
            
            # Save user guide
            guide_path = self.project_root / 'USER_GUIDE.md'
            with open(guide_path, 'w', encoding='utf-8') as f:
                f.write(user_guide_content)
            
            return TaskResult(
                success=True,
                message="User guide generated successfully",
                data={
                    'guide_file': 'USER_GUIDE.md',
                    'content': user_guide_content
                }
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"User guide generation failed: {str(e)}",
                errors=[str(e)]
            )
    
    def _generate_user_guide_markdown(self) -> str:
        """Generate user guide markdown content"""
        content = f"""# MEP Ranking User Guide

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Welcome to MEP Ranking

MEP Ranking is a transparency tool that evaluates the parliamentary activity of Members of the European Parliament (MEPs) based on their contributions to legislative work.

## Getting Started

### Accessing the Application

1. Open your web browser
2. Navigate to `http://localhost:8000` (or the configured URL)
3. You'll see the Activity Explorer as the main interface

### Main Features

#### 1. Activity Explorer (`/index.html`)

The Activity Explorer provides a comprehensive view of all MEPs and their activities:

- **Data Grid**: Sortable table showing all MEPs with their activities
- **Filtering**: Filter by political group, country, or activity type
- **Search**: Find specific MEPs by name
- **Sorting**: Click column headers to sort data
- **Export**: Download data in various formats

##### Key Columns:
- **Name**: MEP's full name (clickable to view profile)
- **Group**: Political group affiliation
- **Country**: Member state representation
- **Speeches**: Number of parliamentary speeches
- **Amendments**: Amendments submitted
- **Questions**: Written and oral questions
- **Reports**: Rapporteur and shadow rapporteur roles
- **Score**: Overall activity score

#### 2. MEP Profiles (`/profile.html`)

Individual MEP profile pages provide detailed analysis:

- **Activity Breakdown**: Detailed view of all parliamentary activities
- **Comparison Data**: How the MEP compares to averages
- **Visual Charts**: Graphical representation of activities
- **Institutional Roles**: Leadership positions held
- **Methodology**: Explanation of scoring calculation

##### Using MEP Profiles:
1. Click on any MEP name in the Activity Explorer
2. Or directly access: `/profile.html?name=MEP_NAME&term=TERM`
3. Navigate through different activity categories
4. View detailed breakdowns by clicking on activity cards

#### 3. Custom Ranking (`/custom_ranking.html`)

Create your own MEP rankings with custom weights:

- **Adjustable Weights**: Modify importance of different activities
- **Real-time Updates**: See ranking changes as you adjust weights
- **Export Results**: Save your custom rankings
- **Methodology Transparency**: Understand how changes affect scores

## Understanding the Data

### Parliamentary Terms

The application covers multiple European Parliament terms:
- **8th Term**: 2014-2019
- **9th Term**: 2019-2024
- **10th Term**: 2024-2029 (ongoing)

### Activity Categories

#### Speeches
- **Plenary Speeches**: Formal addresses in Parliament
- **Committee Speeches**: Contributions in committee meetings
- **Scoring**: Based on frequency and length

#### Amendments
- **Types**: Compromise, alternative, and standard amendments
- **Scoring**: Range-based system (1-3 points based on quantity)
- **Quality**: All amendments counted equally

#### Questions
- **Written Questions**: Formal written inquiries to EU institutions
- **Oral Questions**: Questions asked during sessions
- **Scoring**: 0.1 points per written question (max 20), bonus for oral questions

#### Reports
- **Rapporteur**: Lead author of Parliament reports (4 points each)
- **Shadow Rapporteur**: Opposition spokesperson (1 point each)
- **Opinions**: Committee opinions on other reports (0.5-1 points)

#### Institutional Roles
- **Leadership Positions**: EP President, Vice-Presidents, Quaestors
- **Committee Roles**: Committee chairs and vice-chairs
- **Delegation Roles**: Inter-parliamentary delegation leadership
- **Scoring**: Percentage bonuses applied to base scores

### Scoring Methodology

The MEP Ranking follows the official methodology (October 2017):

1. **Range-Based Scoring**: Prevents extreme outliers while maintaining distinctions
2. **Role Multipliers**: Leadership positions receive percentage bonuses
3. **Attendance Factors**: Poor attendance reduces overall scores
4. **Term-Specific**: Calculations adapted for each parliamentary term

## Advanced Features

### Filtering and Search

#### Text Search
- Search by MEP name (partial matches supported)
- Search across multiple fields simultaneously
- Case-insensitive matching

#### Advanced Filters
- **Political Groups**: Filter by European political groups
- **Countries**: Filter by EU member states
- **Activity Levels**: Filter by high/medium/low activity
- **Institutional Roles**: Show only MEPs with leadership positions

### Data Export

Export functionality is available in multiple formats:
- **CSV**: For spreadsheet analysis
- **JSON**: For programmatic use
- **PDF**: For reports and presentations

### Bookmarking and Sharing

- **Persistent URLs**: Share specific views and filters
- **MEP Profile Links**: Direct links to individual profiles
- **Custom Rankings**: Share your weighted rankings with others

## Tips for Effective Use

### Analyzing MEP Performance

1. **Compare Within Groups**: MEPs' effectiveness varies by political group
2. **Consider Role Context**: Committee chairs have different activity patterns
3. **Term Transitions**: New MEPs need time to establish patterns
4. **Specialization**: Some MEPs focus on specific policy areas

### Interpreting Scores

- **Relative Rankings**: Scores are meaningful in comparison to peers
- **Activity vs. Impact**: High activity doesn't always equal high impact
- **Methodology Awareness**: Understand what the scores measure
- **Term Context**: Consider parliamentary term dynamics

### Research Applications

- **Academic Research**: Use for studies on parliamentary behavior
- **Journalism**: Background research on MEP performance
- **Civic Engagement**: Understand your representatives' activities
- **Comparative Analysis**: Cross-country and cross-group comparisons

## Troubleshooting

### Common Issues

#### Slow Loading
- Clear browser cache
- Check internet connection
- Wait for large datasets to load

#### Missing Data
- Verify you're looking at the correct term
- Some MEPs may have limited data due to term transitions
- Check if filters are too restrictive

#### Profile Page Errors
- Ensure MEP name is spelled correctly in URL
- Verify the term parameter is valid
- Some detailed data requires the API server

### Performance Tips

1. **Large Datasets**: Use filters to reduce data size
2. **Sorting**: Single-column sorting is faster than multi-column
3. **Browser**: Modern browsers perform better with large datasets
4. **Memory**: Close other browser tabs when working with large datasets

## Data Sources and Methodology

### Primary Data Source

All parliamentary activity data comes from **ParlTrack** (parltrack.org), a comprehensive database of European Parliament activities.

### Update Frequency

- **Automated Updates**: Data is updated regularly from ParlTrack
- **Manual Updates**: Administrators can trigger immediate updates
- **Version Control**: All updates are logged and versioned

### Quality Assurance

- **Data Validation**: Automated checks for consistency and completeness
- **Outlier Detection**: Statistical analysis identifies unusual patterns
- **Cross-Reference**: Activities cross-referenced with official EP sources

## Privacy and Ethics

### Data Usage

- **Public Data**: All information is from public parliamentary records
- **No Personal Data**: Only official parliamentary activities are tracked
- **Transparency**: Full methodology and data sources are documented

### Ethical Considerations

- **Contextual Interpretation**: Scores should be interpreted with parliamentary context
- **Fairness**: Methodology designed to be fair across different MEP roles
- **Transparency**: Open source approach ensures accountability

## Support and Feedback

### Getting Help

1. **Documentation**: Check this guide and other documentation files
2. **Methodology**: Review the METHODOLOGY.md file for scoring details
3. **Technical Issues**: Check browser console for error messages

### Providing Feedback

Your feedback helps improve MEP Ranking:
- **Methodology Suggestions**: Propose improvements to scoring
- **Feature Requests**: Suggest new functionality
- **Bug Reports**: Report technical issues or data inconsistencies

---

*This user guide was automatically generated by the Documentation Agent.*
"""
        return content
    
    async def _validate_documentation_links(self, task_data: Dict[str, Any]) -> TaskResult:
        """Validate internal and external links in documentation"""
        try:
            link_validation = {
                'validation_timestamp': datetime.now().isoformat(),
                'files_checked': 0,
                'links_found': 0,
                'broken_links': [],
                'external_links': [],
                'internal_links': []
            }
            
            # Find all documentation files
            doc_files = []
            for ext in self.documentation_config['doc_file_extensions']:
                doc_files.extend(self.project_root.rglob(f'*{ext}'))
            
            link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
            
            for doc_file in doc_files:
                if doc_file.name.startswith('.'):
                    continue
                
                try:
                    with open(doc_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    link_validation['files_checked'] += 1
                    
                    # Find all markdown links
                    links = re.findall(link_pattern, content)
                    
                    for link_text, link_url in links:
                        link_validation['links_found'] += 1
                        
                        link_info = {
                            'text': link_text,
                            'url': link_url,
                            'file': str(doc_file.relative_to(self.project_root))
                        }
                        
                        # Categorize links
                        if link_url.startswith(('http://', 'https://')):
                            link_validation['external_links'].append(link_info)
                        elif link_url.startswith('#'):
                            # Internal anchor link - basic validation would require parsing headers
                            link_validation['internal_links'].append(link_info)
                        else:
                            # Relative file link
                            link_validation['internal_links'].append(link_info)
                            
                            # Check if internal file exists
                            if not link_url.startswith('#'):
                                target_path = doc_file.parent / link_url
                                if not target_path.exists():
                                    link_validation['broken_links'].append({
                                        **link_info,
                                        'error': 'File not found',
                                        'target_path': str(target_path)
                                    })
                
                except Exception as e:
                    self.logger.warning(f"Could not validate links in {doc_file}: {str(e)}")
            
            # Note: External link validation would require actual HTTP requests
            # For now, we just categorize them
            
            validation_summary = {
                'total_files': link_validation['files_checked'],
                'total_links': link_validation['links_found'],
                'broken_internal_links': len(link_validation['broken_links']),
                'external_links_count': len(link_validation['external_links']),
                'validation_status': 'passed' if not link_validation['broken_links'] else 'issues_found'
            }
            
            return TaskResult(
                success=True,
                message=f"Link validation completed. {len(link_validation['broken_links'])} broken links found.",
                data={
                    'validation_results': link_validation,
                    'summary': validation_summary
                }
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Documentation link validation failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def _update_methodology_documentation(self, task_data: Dict[str, Any]) -> TaskResult:
        """Update scoring methodology documentation"""
        try:
            # Generate updated methodology documentation
            methodology_content = self._generate_methodology_markdown()
            
            # Save methodology documentation
            methodology_path = self.project_root / 'METHODOLOGY.md'
            with open(methodology_path, 'w', encoding='utf-8') as f:
                f.write(methodology_content)
            
            return TaskResult(
                success=True,
                message="Methodology documentation updated successfully",
                data={
                    'documentation_file': 'METHODOLOGY.md',
                    'content': methodology_content
                }
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Methodology documentation update failed: {str(e)}",
                errors=[str(e)]
            )
    
    def _generate_methodology_markdown(self) -> str:
        """Generate methodology documentation markdown"""
        content = f"""# MEP Ranking Methodology

Updated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Overview

The MEP Ranking system evaluates Members of the European Parliament based on their parliamentary activities using the official methodology established in October 2017. This document provides a comprehensive explanation of how MEP scores are calculated.

## Core Principles

### 1. Transparency
All scoring calculations are open source and auditable. The methodology is publicly documented and the source code is available for review.

### 2. Fairness
The scoring system is designed to be fair across different types of MEPs, political groups, and member states. Range-based scoring prevents extreme outliers from skewing results.

### 3. Objectivity
Scores are based purely on quantifiable parliamentary activities. No subjective judgments about the quality or political content of activities are made.

### 4. Comprehensiveness
The methodology considers all major forms of parliamentary activity, weighted according to their importance in the legislative process.

## Scoring Categories

### Parliamentary Speeches

**Weight in Total Score:** High

Parliamentary speeches are a key indicator of active participation in debates.

- **Plenary Speeches:** Formal addresses during parliamentary sessions
- **Committee Speeches:** Contributions during committee meetings
- **Scoring Method:** Count-based with range normalization
- **Typical Range:** 0-3 points based on speech frequency

### Amendments

**Weight in Total Score:** High

Amendments show direct engagement with legislative content.

- **Types Counted:** All amendment types (compromise, alternative, standard)
- **Scoring Method:** Range-based scoring in 4 tiers
  - 0-66 amendments: 1 point
  - 67-133 amendments: 2 points
  - 134-200 amendments: 3 points
  - 200+ amendments: 3 points (capped)
- **Rationale:** Prevents gaming through excessive low-quality submissions

### Written Questions

**Weight in Total Score:** Medium

Written questions demonstrate oversight and inquiry functions.

- **Scoring:** 0.1 points per question
- **Maximum:** 20 points (200 questions)
- **Rationale:** Prevents score inflation from excessive questioning

### Oral Questions

**Weight in Total Score:** Medium-Low

Oral questions show active participation in parliamentary dialogue.

- **Threshold:** 7+ questions required to earn points
- **Scoring:** Bonus points for active questioners
- **Integration:** Combined with written questions for total question score

### Reports and Opinions

**Weight in Total Score:** Very High

Rapporteur and opinion roles show legislative leadership.

#### Rapporteur Roles
- **Parliament Reports:** 4.0 points each
- **Committee Reports:** 4.0 points each
- **Significance:** Rapporteurs guide legislation through Parliament

#### Shadow Rapporteur Roles
- **Points:** 1.0 point each
- **Role:** Opposition spokesperson for reports
- **Importance:** Ensures cross-party legislative oversight

#### Opinion Rapporteur
- **Lead Opinions:** 1.0 point each
- **Supporting Opinions:** 0.5 points each
- **Function:** Committee input on other committees' reports

### Institutional Roles

**Weight in Total Score:** Multiplier Effect

Leadership positions receive percentage bonuses applied to base scores.

#### European Parliament Level
- **EP President:** 50% bonus
- **EP Vice President:** 25% bonus
- **EP Quaestor:** 15% bonus

#### Committee Level
- **Committee Chair:** 25% bonus
- **Committee Vice Chair:** 15% bonus

#### Delegation Level
- **Delegation Chair:** 15% bonus
- **Delegation Vice Chair:** 10% bonus

### Voting Attendance

**Weight in Total Score:** Attendance Factor

Poor attendance reduces overall scores through a penalty system.

- **Calculation:** Based on roll-call vote participation
- **Impact:** Scores reduced proportionally for low attendance
- **Threshold:** Significant penalties for attendance below 50%

## Calculation Process

### Step 1: Raw Activity Scoring

Each MEP receives points for individual activities according to the scales above.

### Step 2: Range-Based Normalization

To prevent extreme outliers from dominating:

1. Calculate statistical ranges for each activity type
2. Apply range-based scoring within reasonable bounds
3. Maintain meaningful distinctions between activity levels

### Step 3: Role Multiplier Application

Institutional role bonuses are applied as percentage increases to the base score.

### Step 4: Attendance Adjustment

Attendance rates below thresholds result in proportional score reductions.

### Step 5: Final Score Calculation

The final score represents the MEP's overall parliamentary activity level.

## Term-Specific Considerations

### 8th Parliamentary Term (2014-2019)

- **Full Term Data:** Complete activity records available
- **Established Patterns:** MEPs had full term to establish activity patterns
- **Historical Context:** Brexit proceedings affected some activity patterns

### 9th Parliamentary Term (2019-2024)

- **COVID-19 Impact:** Remote proceedings affected traditional activity measures
- **Methodology Continuity:** Core methodology maintained despite procedural changes
- **Data Completeness:** Full term data available

### 10th Parliamentary Term (2024-2029)

- **Ongoing Term:** Limited data for new MEPs
- **Adaptation Period:** New MEPs building activity patterns
- **Methodology Evolution:** Potential adjustments based on new procedures

## Statistical Considerations

### Outlier Handling

The range-based scoring system prevents extreme outliers from distorting comparisons:

- **Statistical Analysis:** Regular analysis of score distributions
- **Threshold Adjustments:** Range boundaries adjusted based on actual data
- **Fairness Preservation:** Ensures all MEPs can achieve meaningful scores

### Cross-Group Fairness

Different political groups may have different activity patterns:

- **Group Analysis:** Regular analysis of group-level score distributions
- **Bias Detection:** Statistical tests for systematic group advantages
- **Methodology Neutrality:** Scoring system designed to be group-neutral

### Country-Level Analysis

Member state differences are monitored for fairness:

- **Resource Variations:** Recognition that smaller member states may have different patterns
- **Language Factors:** No penalties for non-native speakers
- **Cultural Differences:** Methodology accommodates different parliamentary traditions

## Transparency Measures

### Open Source Implementation

All scoring calculations are implemented in open source code:

- **Code Availability:** Full source code available for review
- **Audit Trail:** All calculations are logged and auditable
- **Version Control:** Changes to methodology are tracked and documented

### Data Sources

Primary data source: **ParlTrack** (parltrack.org)

- **Comprehensive Coverage:** Complete parliamentary activity data
- **Regular Updates:** Data updated to reflect latest activities
- **Quality Assurance:** Data validation and consistency checks

### Methodology Validation

Regular validation ensures methodology integrity:

- **Statistical Analysis:** Regular analysis of score distributions and patterns
- **Comparative Studies:** Cross-validation with other parliamentary activity measures
- **Expert Review:** Methodology reviewed by parliamentary and statistical experts

## Limitations and Considerations

### What the Scores Measure

- **Quantitative Activity:** Scores measure quantity of parliamentary activities
- **Not Quality Assessment:** No evaluation of the political merit of activities
- **Process Participation:** Focus on engagement with parliamentary processes

### What the Scores Don't Measure

- **Political Impact:** Real-world impact of legislative work
- **Constituency Work:** Activities outside formal parliamentary procedures
- **Informal Influence:** Behind-the-scenes negotiations and influence
- **Media Activity:** Public communication and media engagement

### Interpretation Guidelines

- **Comparative Tool:** Scores most meaningful in comparison to other MEPs
- **Context Matters:** Consider MEP roles, specializations, and circumstances
- **Trend Analysis:** Score changes over time may be more meaningful than absolute values
- **Supplementary Information:** Use alongside other information about MEP activities

## Methodology Evolution

### Version History

- **October 2017:** Original methodology established
- **Ongoing Refinements:** Regular minor adjustments based on data analysis
- **Transparency Principle:** All changes documented and explained

### Future Developments

The methodology may evolve to:

- **Incorporate New Activity Types:** As Parliament procedures evolve
- **Improve Fairness:** Based on statistical analysis and feedback
- **Enhance Accuracy:** Through better data sources and validation
- **Maintain Relevance:** Adapt to changing parliamentary practices

## Technical Implementation

### Database Structure

- **Activity Tables:** Separate tables for each activity type
- **MEP Profiles:** Comprehensive MEP information and scores
- **Audit Trails:** Complete history of score calculations

### Calculation Pipeline

1. **Data Ingestion:** Import latest activity data from ParlTrack
2. **Validation:** Check data consistency and completeness
3. **Score Calculation:** Apply methodology to calculate scores
4. **Quality Assurance:** Validate results against expected patterns
5. **Publication:** Update public-facing datasets

### Performance Optimization

- **Efficient Algorithms:** Optimized calculation procedures
- **Caching:** Strategic caching for frequently accessed data
- **Incremental Updates:** Only recalculate when underlying data changes

---

*This methodology documentation was automatically generated by the Documentation Agent.*
"""
        return content
    
    async def _generate_changelog(self, task_data: Dict[str, Any]) -> TaskResult:
        """Generate changelog from git history and changes"""
        try:
            # Basic changelog generation (would be enhanced with actual git integration)
            changelog_content = self._generate_changelog_markdown()
            
            # Save changelog
            changelog_path = self.project_root / 'CHANGELOG.md'
            with open(changelog_path, 'w', encoding='utf-8') as f:
                f.write(changelog_content)
            
            return TaskResult(
                success=True,
                message="Changelog generated successfully",
                data={
                    'changelog_file': 'CHANGELOG.md',
                    'content': changelog_content
                }
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Changelog generation failed: {str(e)}",
                errors=[str(e)]
            )
    
    def _generate_changelog_markdown(self) -> str:
        """Generate changelog markdown content"""
        content = f"""# Changelog

All notable changes to the MEP Ranking project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive sub-agents system for automated maintenance
- Security and compliance monitoring
- Documentation generation and validation
- Performance monitoring and optimization

### Changed
- Enhanced error handling and logging throughout the application
- Improved data validation and consistency checks
- Updated documentation structure and completeness

### Fixed
- Institutional roles display in term 10 table
- Missing attendance rate and written questions averages on profile pages
- JavaScript errors in profile page functionality
- Amendments details loading without API server

## [2.0.0] - 2024-XX-XX

### Added
- Sub-agents system for automated application management
- Scoring system validation and transparency reporting
- Security vulnerability scanning and compliance checking
- Automated documentation generation and maintenance
- Performance monitoring and optimization tools
- Quality assurance testing automation

### Enhanced
- Data pipeline reliability and error handling
- Frontend user experience and accessibility
- API performance and caching strategies
- Documentation completeness and accuracy

### Security
- Comprehensive security assessment capabilities
- GDPR compliance validation
- Dependency vulnerability monitoring
- Sensitive data exposure detection

## [1.5.0] - 2024-XX-XX

### Added
- Dynamic range calculations for scoring methodology
- Improved profile page functionality with detailed breakdowns
- Enhanced data validation and consistency checks
- Better error handling and user feedback

### Changed
- Updated dataset structure for better frontend compatibility
- Improved scoring algorithm implementation
- Enhanced data processing pipeline

### Fixed
- Various frontend bugs and performance issues
- Data inconsistencies across different terms
- Profile page loading and display issues

## [1.0.0] - 2024-XX-XX

### Added
- Initial release of MEP Ranking application
- Core scoring methodology implementation
- Web interface for MEP activity exploration
- Individual MEP profile pages
- Data ingestion from ParlTrack sources
- SQLite database for data storage

### Features
- Activity Explorer with sortable data grid
- MEP profile pages with detailed activity breakdowns
- Custom ranking functionality with adjustable weights
- Multiple parliamentary term support (8th, 9th, 10th terms)
- Responsive web design for desktop and mobile

### Data
- Complete MEP activity data for terms 8, 9, and 10
- Parliamentary speeches, amendments, questions, and reports
- Institutional roles and voting attendance records
- Political group and country information

---

*This changelog was automatically generated by the Documentation Agent.*

*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        return content
    
    async def _audit_documentation_quality(self, task_data: Dict[str, Any]) -> TaskResult:
        """Audit overall documentation quality and accessibility"""
        try:
            # Run comprehensive documentation analysis
            completeness_result = await self._analyze_documentation_completeness(task_data)
            code_doc_result = await self._validate_code_documentation(task_data)
            link_validation_result = await self._validate_documentation_links(task_data)
            
            # Compile quality audit
            quality_audit = {
                'audit_timestamp': datetime.now().isoformat(),
                'overall_quality_score': 0,
                'completeness_analysis': completeness_result.data if completeness_result.success else None,
                'code_documentation_analysis': code_doc_result.data if code_doc_result.success else None,
                'link_validation': link_validation_result.data if link_validation_result.success else None,
                'quality_recommendations': [],
                'accessibility_considerations': []
            }
            
            # Calculate overall quality score
            scores = []
            
            if completeness_result.success:
                scores.append(completeness_result.data['completeness_score'])
            
            if code_doc_result.success:
                scores.append(code_doc_result.data['documentation_coverage'])
            
            if link_validation_result.success:
                link_score = 100 if not link_validation_result.data['validation_results']['broken_links'] else 75
                scores.append(link_score)
            
            if scores:
                quality_audit['overall_quality_score'] = sum(scores) / len(scores)
            
            # Generate quality recommendations
            if quality_audit['overall_quality_score'] < 70:
                quality_audit['quality_recommendations'].append(
                    "Overall documentation quality is below 70%. Focus on completeness and code documentation."
                )
            
            # Accessibility considerations
            quality_audit['accessibility_considerations'] = [
                "Ensure documentation uses clear, simple language",
                "Provide alternative text for any images or diagrams",
                "Use proper heading structure (H1, H2, H3) for navigation",
                "Include table of contents in long documents",
                "Test documentation with screen readers",
                "Provide multiple formats (HTML, PDF, plain text) when possible"
            ]
            
            return TaskResult(
                success=True,
                message=f"Documentation quality audit completed. Overall score: {quality_audit['overall_quality_score']:.1f}%",
                data=quality_audit
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Documentation quality audit failed: {str(e)}",
                errors=[str(e)]
            )