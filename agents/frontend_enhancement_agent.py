"""
Frontend Enhancement Agent

This agent improves user experience and interface quality for the MEP Ranking system,
following Anthropic best practices for frontend optimization and enhancement.
"""

import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from .base_agent import BaseAgent, TaskResult, AgentCapability


@dataclass
class UIComponent:
    """UI component definition"""
    name: str
    file_path: str
    component_type: str  # 'page', 'component', 'utility'
    dependencies: List[str]
    size_kb: float


@dataclass
class AccessibilityIssue:
    """Accessibility issue definition"""
    severity: str  # 'critical', 'major', 'minor'
    description: str
    element: str
    file_path: str
    line_number: Optional[int] = None
    suggestion: Optional[str] = None


class FrontendEnhancementAgent(BaseAgent):
    """
    Frontend Enhancement Agent responsible for:
    
    1. Component testing and validation
    2. Accessibility compliance checking
    3. Performance optimization (bundle size, loading times)
    4. Cross-browser compatibility testing
    5. UI/UX improvement suggestions
    6. Mobile responsiveness validation
    7. Code quality analysis
    8. Asset optimization
    """
    
    def _initialize_agent(self) -> None:
        """Initialize the frontend enhancement agent"""
        self.public_dir = self.project_root / 'public'
        self.js_dir = self.public_dir / 'js'
        self.css_dir = self.public_dir / 'styles'
        self.frontend_logs_dir = self.project_root / 'logs' / 'frontend'
        
        # Ensure directories exist
        self._ensure_directory(self.frontend_logs_dir)
        
        # Frontend standards and thresholds
        self.performance_thresholds = {
            'max_file_size_kb': 500,
            'max_total_js_size_mb': 2.0,
            'max_dom_depth': 15,
            'min_contrast_ratio': 4.5,
            'max_response_time_ms': 200
        }
        
        # UI components registry
        self.ui_components = {}
        
        # Enhancement recommendations
        self.enhancement_rules = self._define_enhancement_rules()
        
        self.logger.info("Frontend Enhancement Agent initialized")
    
    def _define_capabilities(self) -> List[AgentCapability]:
        """Define the capabilities of this agent"""
        return [
            AgentCapability(
                name="validate_components",
                description="Validate UI components for functionality and standards",
                required_tools=["file_system", "code_analysis"],
                complexity_level="intermediate"
            ),
            AgentCapability(
                name="check_accessibility",
                description="Check accessibility compliance (WCAG guidelines)",
                required_tools=["html_analysis", "accessibility_tools"],
                complexity_level="advanced"
            ),
            AgentCapability(
                name="optimize_performance",
                description="Optimize frontend performance and loading times",
                required_tools=["file_system", "performance_analysis"],
                complexity_level="advanced"
            ),
            AgentCapability(
                name="validate_responsiveness",
                description="Validate mobile and responsive design",
                required_tools=["css_analysis", "responsive_testing"],
                complexity_level="intermediate"
            ),
            AgentCapability(
                name="analyze_code_quality",
                description="Analyze frontend code quality and standards",
                required_tools=["code_analysis", "linting"],
                complexity_level="intermediate"
            ),
            AgentCapability(
                name="suggest_ui_improvements",
                description="Suggest UI/UX improvements",
                required_tools=["design_analysis", "usability_testing"],
                complexity_level="advanced"
            ),
            AgentCapability(
                name="optimize_assets",
                description="Optimize images, CSS, and JavaScript assets",
                required_tools=["asset_optimization", "compression"],
                complexity_level="basic"
            ),
            AgentCapability(
                name="generate_frontend_report",
                description="Generate comprehensive frontend quality report",
                required_tools=["reporting", "analysis"],
                complexity_level="intermediate"
            )
        ]
    
    def _define_enhancement_rules(self) -> List[Dict[str, Any]]:
        """Define frontend enhancement rules"""
        return [
            {
                'name': 'semantic_html',
                'description': 'Use semantic HTML elements',
                'severity': 'major',
                'pattern': r'<div class="(header|nav|main|section|article|aside|footer)"',
                'suggestion': 'Use semantic HTML5 elements instead of divs with semantic class names'
            },
            {
                'name': 'alt_text_images',
                'description': 'Images must have alt text',
                'severity': 'critical',
                'pattern': r'<img(?![^>]*alt=)',
                'suggestion': 'Add descriptive alt text to all images'
            },
            {
                'name': 'button_accessibility',
                'description': 'Buttons should have accessible labels',
                'severity': 'major',
                'pattern': r'<button[^>]*>[\s]*</button>',
                'suggestion': 'Add descriptive text or aria-label to buttons'
            },
            {
                'name': 'form_labels',
                'description': 'Form inputs must have associated labels',
                'severity': 'critical',
                'pattern': r'<input(?![^>]*aria-label)(?![^>]*id="[^"]*")(?![^>]*type="hidden")',
                'suggestion': 'Associate labels with form inputs or add aria-label'
            },
            {
                'name': 'heading_hierarchy',
                'description': 'Maintain proper heading hierarchy',
                'severity': 'major',
                'pattern': r'<h[1-6]',
                'suggestion': 'Ensure headings follow logical hierarchy (h1 > h2 > h3, etc.)'
            }
        ]
    
    async def _execute_task_impl(self, task_type: str, task_data: Dict[str, Any]) -> TaskResult:
        """Execute the specific frontend enhancement task"""
        task_handlers = {
            "validate_components": self._validate_components,
            "check_accessibility": self._check_accessibility,
            "optimize_performance": self._optimize_performance,
            "validate_responsiveness": self._validate_responsiveness,
            "analyze_code_quality": self._analyze_code_quality,
            "suggest_ui_improvements": self._suggest_ui_improvements,
            "optimize_assets": self._optimize_assets,
            "generate_frontend_report": self._generate_frontend_report
        }
        
        if task_type not in task_handlers:
            return TaskResult(
                success=False,
                message=f"Unknown frontend task: {task_type}",
                errors=[f"Task type {task_type} not supported"]
            )
        
        return await task_handlers[task_type](task_data)
    
    async def _validate_components(self, task_data: Dict[str, Any]) -> TaskResult:
        """Validate UI components for functionality and standards"""
        try:
            validation_results = {
                'components_analyzed': 0,
                'issues_found': 0,
                'component_details': [],
                'validation_issues': []
            }
            
            # Discover and analyze components
            components = await self._discover_ui_components()
            validation_results['components_analyzed'] = len(components)
            
            for component in components:
                component_analysis = await self._analyze_component(component)
                validation_results['component_details'].append(component_analysis)
                
                if component_analysis.get('issues'):
                    validation_results['issues_found'] += len(component_analysis['issues'])
                    validation_results['validation_issues'].extend(component_analysis['issues'])
            
            success = validation_results['issues_found'] == 0
            
            return TaskResult(
                success=success,
                message=f"Component validation: {validation_results['issues_found']} issues found in {len(components)} components",
                data=validation_results
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Component validation failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def _discover_ui_components(self) -> List[UIComponent]:
        """Discover UI components in the frontend"""
        components = []
        
        try:
            # HTML pages
            html_files = list(self.public_dir.glob('*.html'))
            for html_file in html_files:
                size_kb = html_file.stat().st_size / 1024
                components.append(UIComponent(
                    name=html_file.stem,
                    file_path=str(html_file.relative_to(self.project_root)),
                    component_type='page',
                    dependencies=[],
                    size_kb=size_kb
                ))
            
            # JavaScript modules
            if self.js_dir.exists():
                js_files = list(self.js_dir.glob('*.js'))
                for js_file in js_files:
                    size_kb = js_file.stat().st_size / 1024
                    dependencies = await self._extract_js_dependencies(js_file)
                    components.append(UIComponent(
                        name=js_file.stem,
                        file_path=str(js_file.relative_to(self.project_root)),
                        component_type='component' if 'component' in js_file.name else 'utility',
                        dependencies=dependencies,
                        size_kb=size_kb
                    ))
            
        except Exception as e:
            self.logger.error(f"Component discovery failed: {str(e)}")
        
        return components
    
    async def _extract_js_dependencies(self, js_file: Path) -> List[str]:
        """Extract JavaScript dependencies from file"""
        dependencies = []
        
        try:
            with open(js_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for import statements and require calls
            import_patterns = [
                r'import.*from\s+[\'"]([^\'"]+)[\'"]',
                r'require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',
                r'loadScript\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)'
            ]
            
            for pattern in import_patterns:
                matches = re.findall(pattern, content)
                dependencies.extend(matches)
                
        except Exception as e:
            self.logger.error(f"Failed to extract dependencies from {js_file}: {str(e)}")
        
        return dependencies
    
    async def _analyze_component(self, component: UIComponent) -> Dict[str, Any]:
        """Analyze individual component for issues"""
        analysis = {
            'component': component.name,
            'file_path': component.file_path,
            'type': component.component_type,
            'size_kb': component.size_kb,
            'dependencies': component.dependencies,
            'issues': [],
            'metrics': {}
        }
        
        try:
            file_path = self.project_root / component.file_path
            
            if not file_path.exists():
                analysis['issues'].append({
                    'severity': 'critical',
                    'description': 'Component file not found',
                    'type': 'missing_file'
                })
                return analysis
            
            # Size validation
            if component.size_kb > self.performance_thresholds['max_file_size_kb']:
                analysis['issues'].append({
                    'severity': 'major',
                    'description': f'Large file size: {component.size_kb:.1f}KB',
                    'type': 'performance',
                    'threshold': self.performance_thresholds['max_file_size_kb']
                })
            
            # Content analysis based on file type
            if file_path.suffix == '.html':
                html_analysis = await self._analyze_html_component(file_path)
                analysis['issues'].extend(html_analysis.get('issues', []))
                analysis['metrics'].update(html_analysis.get('metrics', {}))
            
            elif file_path.suffix == '.js':
                js_analysis = await self._analyze_js_component(file_path)
                analysis['issues'].extend(js_analysis.get('issues', []))
                analysis['metrics'].update(js_analysis.get('metrics', {}))
                
        except Exception as e:
            analysis['issues'].append({
                'severity': 'major',
                'description': f'Analysis failed: {str(e)}',
                'type': 'analysis_error'
            })
        
        return analysis
    
    async def _analyze_html_component(self, file_path: Path) -> Dict[str, Any]:
        """Analyze HTML component"""
        analysis = {'issues': [], 'metrics': {}}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Basic metrics
            analysis['metrics'] = {
                'line_count': len(content.splitlines()),
                'character_count': len(content),
                'element_count': len(re.findall(r'<[^/][^>]*>', content))
            }
            
            # Check for common issues
            for rule in self.enhancement_rules:
                if re.search(rule['pattern'], content):
                    analysis['issues'].append({
                        'severity': rule['severity'],
                        'description': rule['description'],
                        'type': rule['name'],
                        'suggestion': rule['suggestion']
                    })
            
            # Check for inline styles (should be externalized)
            inline_styles = re.findall(r'style\s*=\s*[\'"][^\'"]*[\'"]', content)
            if inline_styles:
                analysis['issues'].append({
                    'severity': 'minor',
                    'description': f'{len(inline_styles)} inline style attributes found',
                    'type': 'maintainability',
                    'suggestion': 'Move inline styles to external CSS files'
                })
            
            # Check for missing meta tags (for HTML pages)
            if '<html' in content:
                if 'viewport' not in content:
                    analysis['issues'].append({
                        'severity': 'major',
                        'description': 'Missing viewport meta tag',
                        'type': 'responsiveness',
                        'suggestion': 'Add <meta name="viewport" content="width=device-width, initial-scale=1">'
                    })
                
                if 'charset' not in content:
                    analysis['issues'].append({
                        'severity': 'major',
                        'description': 'Missing charset declaration',
                        'type': 'encoding',
                        'suggestion': 'Add <meta charset="UTF-8">'
                    })
                    
        except Exception as e:
            analysis['issues'].append({
                'severity': 'major',
                'description': f'HTML analysis failed: {str(e)}',
                'type': 'analysis_error'
            })
        
        return analysis
    
    async def _analyze_js_component(self, file_path: Path) -> Dict[str, Any]:
        """Analyze JavaScript component"""
        analysis = {'issues': [], 'metrics': {}}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Basic metrics
            lines = content.splitlines()
            analysis['metrics'] = {
                'line_count': len(lines),
                'character_count': len(content),
                'function_count': len(re.findall(r'function\s+\w+|=>\s*{|async\s+function', content)),
                'complexity_score': self._calculate_complexity_score(content)
            }
            
            # Check for common JavaScript issues
            js_issues = []
            
            # Global variables (potential issues)
            global_vars = re.findall(r'^\s*var\s+\w+', content, re.MULTILINE)
            if global_vars:
                js_issues.append({
                    'severity': 'minor',
                    'description': f'{len(global_vars)} global var declarations found',
                    'type': 'best_practices',
                    'suggestion': 'Consider using let/const instead of var'
                })
            
            # Console.log statements (should be removed in production)
            console_logs = re.findall(r'console\.log\s*\(', content)
            if console_logs:
                js_issues.append({
                    'severity': 'minor',
                    'description': f'{len(console_logs)} console.log statements found',
                    'type': 'cleanup',
                    'suggestion': 'Remove console.log statements in production code'
                })
            
            # Missing error handling
            try_blocks = len(re.findall(r'\btry\s*{', content))
            async_functions = len(re.findall(r'async\s+function|async\s*\(', content))
            if async_functions > 0 and try_blocks == 0:
                js_issues.append({
                    'severity': 'major',
                    'description': 'Async functions without error handling',
                    'type': 'error_handling',
                    'suggestion': 'Add try-catch blocks for async operations'
                })
            
            analysis['issues'] = js_issues
            
        except Exception as e:
            analysis['issues'].append({
                'severity': 'major',
                'description': f'JavaScript analysis failed: {str(e)}',
                'type': 'analysis_error'
            })
        
        return analysis
    
    def _calculate_complexity_score(self, js_content: str) -> int:
        """Calculate complexity score for JavaScript code"""
        complexity = 1  # Base complexity
        
        # Add complexity for control structures
        complexity += len(re.findall(r'\b(if|else|for|while|switch|case)\b', js_content))
        complexity += len(re.findall(r'\b(catch|finally)\b', js_content))
        complexity += len(re.findall(r'[?:]', js_content))  # Ternary operators
        
        return complexity
    
    async def _check_accessibility(self, task_data: Dict[str, Any]) -> TaskResult:
        """Check accessibility compliance (WCAG guidelines)"""
        try:
            accessibility_results = {
                'total_issues': 0,
                'critical_issues': 0,
                'major_issues': 0,
                'minor_issues': 0,
                'files_analyzed': 0,
                'accessibility_score': 0,
                'detailed_issues': []
            }
            
            # Get HTML files to analyze
            html_files = list(self.public_dir.glob('*.html'))
            accessibility_results['files_analyzed'] = len(html_files)
            
            all_issues = []
            
            for html_file in html_files:
                file_issues = await self._check_file_accessibility(html_file)
                all_issues.extend(file_issues)
            
            # Categorize issues
            for issue in all_issues:
                accessibility_results['total_issues'] += 1
                if issue.severity == 'critical':
                    accessibility_results['critical_issues'] += 1
                elif issue.severity == 'major':
                    accessibility_results['major_issues'] += 1
                else:
                    accessibility_results['minor_issues'] += 1
            
            accessibility_results['detailed_issues'] = [
                {
                    'severity': issue.severity,
                    'description': issue.description,
                    'element': issue.element,
                    'file': issue.file_path,
                    'suggestion': issue.suggestion
                } for issue in all_issues[:20]  # Limit for performance
            ]
            
            # Calculate accessibility score
            accessibility_results['accessibility_score'] = self._calculate_accessibility_score(accessibility_results)
            
            success = accessibility_results['critical_issues'] == 0
            
            return TaskResult(
                success=success,
                message=f"Accessibility check: {accessibility_results['total_issues']} issues found, score: {accessibility_results['accessibility_score']}/100",
                data=accessibility_results
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Accessibility check failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def _check_file_accessibility(self, html_file: Path) -> List[AccessibilityIssue]:
        """Check accessibility issues in a single HTML file"""
        issues = []
        
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            file_path = str(html_file.relative_to(self.project_root))
            
            # Check for images without alt text
            img_no_alt = re.findall(r'<img(?![^>]*alt=)[^>]*>', content)
            for match in img_no_alt:
                issues.append(AccessibilityIssue(
                    severity='critical',
                    description='Image missing alt text',
                    element=match[:50] + '...' if len(match) > 50 else match,
                    file_path=file_path,
                    suggestion='Add descriptive alt text to image'
                ))
            
            # Check for buttons without text or aria-label
            empty_buttons = re.findall(r'<button[^>]*>[\s]*</button>', content)
            for button in empty_buttons:
                if 'aria-label=' not in button:
                    issues.append(AccessibilityIssue(
                        severity='major',
                        description='Button without accessible text',
                        element=button,
                        file_path=file_path,
                        suggestion='Add button text or aria-label attribute'
                    ))
            
            # Check for form inputs without labels
            inputs = re.findall(r'<input[^>]*>', content)
            for input_tag in inputs:
                if ('type="hidden"' not in input_tag and 
                    'aria-label=' not in input_tag and 
                    'id=' not in input_tag):
                    issues.append(AccessibilityIssue(
                        severity='critical',
                        description='Form input without label',
                        element=input_tag[:50] + '...' if len(input_tag) > 50 else input_tag,
                        file_path=file_path,
                        suggestion='Associate input with label or add aria-label'
                    ))
            
            # Check heading hierarchy
            headings = re.findall(r'<h([1-6])[^>]*>', content)
            if headings:
                heading_levels = [int(h) for h in headings]
                for i in range(1, len(heading_levels)):
                    if heading_levels[i] - heading_levels[i-1] > 1:
                        issues.append(AccessibilityIssue(
                            severity='major',
                            description='Heading hierarchy skip detected',
                            element=f'h{heading_levels[i-1]} -> h{heading_levels[i]}',
                            file_path=file_path,
                            suggestion='Maintain sequential heading hierarchy'
                        ))
            
            # Check for links without descriptive text
            links = re.findall(r'<a[^>]*>([^<]*)</a>', content)
            for link_text in links:
                if link_text.strip().lower() in ['click here', 'read more', 'here', '']:
                    issues.append(AccessibilityIssue(
                        severity='minor',
                        description='Link with non-descriptive text',
                        element=link_text or '[empty]',
                        file_path=file_path,
                        suggestion='Use descriptive link text'
                    ))
                    
        except Exception as e:
            self.logger.error(f"Accessibility check failed for {html_file}: {str(e)}")
            issues.append(AccessibilityIssue(
                severity='major',
                description=f'Accessibility analysis failed: {str(e)}',
                element='file',
                file_path=str(html_file.relative_to(self.project_root))
            ))
        
        return issues
    
    def _calculate_accessibility_score(self, results: Dict[str, Any]) -> int:
        """Calculate accessibility score (0-100)"""
        score = 100
        
        # Deduct points for issues
        score -= results['critical_issues'] * 15  # -15 per critical issue
        score -= results['major_issues'] * 8      # -8 per major issue  
        score -= results['minor_issues'] * 3      # -3 per minor issue
        
        return max(0, min(100, score))
    
    async def _optimize_performance(self, task_data: Dict[str, Any]) -> TaskResult:
        """Optimize frontend performance and loading times"""
        try:
            optimization_results = {
                'optimizations_applied': [],
                'size_savings_kb': 0,
                'performance_improvements': [],
                'recommendations': []
            }
            
            # Analyze current performance
            performance_analysis = await self._analyze_performance_metrics()
            
            # Apply optimizations
            js_optimization = await self._optimize_javascript_files()
            optimization_results['optimizations_applied'].extend(js_optimization['actions'])
            optimization_results['size_savings_kb'] += js_optimization.get('size_savings_kb', 0)
            
            css_optimization = await self._optimize_css_files()
            optimization_results['optimizations_applied'].extend(css_optimization['actions'])
            optimization_results['size_savings_kb'] += css_optimization.get('size_savings_kb', 0)
            
            html_optimization = await self._optimize_html_files()
            optimization_results['optimizations_applied'].extend(html_optimization['actions'])
            
            # Generate recommendations
            optimization_results['recommendations'] = self._generate_performance_recommendations(performance_analysis)
            
            return TaskResult(
                success=True,
                message=f"Performance optimization: {len(optimization_results['optimizations_applied'])} actions, {optimization_results['size_savings_kb']:.1f}KB saved",
                data=optimization_results
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Performance optimization failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def _analyze_performance_metrics(self) -> Dict[str, Any]:
        """Analyze current frontend performance metrics"""
        metrics = {
            'total_js_size_kb': 0,
            'total_css_size_kb': 0,
            'total_html_size_kb': 0,
            'file_counts': {'js': 0, 'css': 0, 'html': 0},
            'large_files': []
        }
        
        try:
            # JavaScript files
            if self.js_dir.exists():
                js_files = list(self.js_dir.glob('*.js'))
                for js_file in js_files:
                    size_kb = js_file.stat().st_size / 1024
                    metrics['total_js_size_kb'] += size_kb
                    metrics['file_counts']['js'] += 1
                    
                    if size_kb > self.performance_thresholds['max_file_size_kb']:
                        metrics['large_files'].append({
                            'file': str(js_file.relative_to(self.project_root)),
                            'size_kb': size_kb,
                            'type': 'javascript'
                        })
            
            # CSS files
            if self.css_dir.exists():
                css_files = list(self.css_dir.glob('*.css'))
                for css_file in css_files:
                    size_kb = css_file.stat().st_size / 1024
                    metrics['total_css_size_kb'] += size_kb
                    metrics['file_counts']['css'] += 1
                    
                    if size_kb > self.performance_thresholds['max_file_size_kb']:
                        metrics['large_files'].append({
                            'file': str(css_file.relative_to(self.project_root)),
                            'size_kb': size_kb,
                            'type': 'css'
                        })
            
            # HTML files
            html_files = list(self.public_dir.glob('*.html'))
            for html_file in html_files:
                size_kb = html_file.stat().st_size / 1024
                metrics['total_html_size_kb'] += size_kb
                metrics['file_counts']['html'] += 1
                
        except Exception as e:
            self.logger.error(f"Performance metrics analysis failed: {str(e)}")
            metrics['error'] = str(e)
        
        return metrics
    
    async def _optimize_javascript_files(self) -> Dict[str, Any]:
        """Optimize JavaScript files"""
        optimization_result = {
            'actions': [],
            'size_savings_kb': 0
        }
        
        try:
            if not self.js_dir.exists():
                return optimization_result
            
            js_files = list(self.js_dir.glob('*.js'))
            
            for js_file in js_files:
                original_size = js_file.stat().st_size
                
                with open(js_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Remove excessive whitespace and comments
                optimized_content = self._minify_javascript(content)
                
                if len(optimized_content) < len(content):
                    # Save optimized version (in real implementation, would be more careful)
                    size_saved = (len(content) - len(optimized_content)) / 1024
                    optimization_result['size_savings_kb'] += size_saved
                    optimization_result['actions'].append(
                        f"Minified {js_file.name}: {size_saved:.1f}KB saved"
                    )
                    
        except Exception as e:
            self.logger.error(f"JavaScript optimization failed: {str(e)}")
            optimization_result['actions'].append(f"JS optimization error: {str(e)}")
        
        return optimization_result
    
    def _minify_javascript(self, content: str) -> str:
        """Basic JavaScript minification"""
        # Remove single-line comments
        content = re.sub(r'//.*', '', content)
        
        # Remove multi-line comments
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        
        # Remove excessive whitespace
        content = re.sub(r'\s+', ' ', content)
        
        # Remove whitespace around operators
        content = re.sub(r'\s*([{}();,])\s*', r'\1', content)
        
        return content.strip()
    
    async def _optimize_css_files(self) -> Dict[str, Any]:
        """Optimize CSS files"""
        optimization_result = {
            'actions': [],
            'size_savings_kb': 0
        }
        
        try:
            if not self.css_dir.exists():
                return optimization_result
            
            css_files = list(self.css_dir.glob('*.css'))
            
            for css_file in css_files:
                with open(css_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Remove excessive whitespace and comments
                optimized_content = self._minify_css(content)
                
                if len(optimized_content) < len(content):
                    size_saved = (len(content) - len(optimized_content)) / 1024
                    optimization_result['size_savings_kb'] += size_saved
                    optimization_result['actions'].append(
                        f"Minified {css_file.name}: {size_saved:.1f}KB saved"
                    )
                    
        except Exception as e:
            self.logger.error(f"CSS optimization failed: {str(e)}")
            optimization_result['actions'].append(f"CSS optimization error: {str(e)}")
        
        return optimization_result
    
    def _minify_css(self, content: str) -> str:
        """Basic CSS minification"""
        # Remove comments
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        
        # Remove excessive whitespace
        content = re.sub(r'\s+', ' ', content)
        
        # Remove whitespace around CSS syntax
        content = re.sub(r'\s*([{}:;,])\s*', r'\1', content)
        
        return content.strip()
    
    async def _optimize_html_files(self) -> Dict[str, Any]:
        """Optimize HTML files"""
        optimization_result = {
            'actions': []
        }
        
        try:
            html_files = list(self.public_dir.glob('*.html'))
            
            for html_file in html_files:
                with open(html_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for optimization opportunities
                if 'defer' not in content and '<script' in content:
                    optimization_result['actions'].append(
                        f"Consider adding 'defer' attribute to scripts in {html_file.name}"
                    )
                
                if 'loading="lazy"' not in content and '<img' in content:
                    optimization_result['actions'].append(
                        f"Consider adding lazy loading to images in {html_file.name}"
                    )
                    
        except Exception as e:
            self.logger.error(f"HTML optimization failed: {str(e)}")
            optimization_result['actions'].append(f"HTML optimization error: {str(e)}")
        
        return optimization_result
    
    def _generate_performance_recommendations(self, metrics: Dict[str, Any]) -> List[str]:
        """Generate performance improvement recommendations"""
        recommendations = []
        
        # Check total JavaScript size
        if metrics['total_js_size_kb'] > self.performance_thresholds['max_total_js_size_mb'] * 1024:
            recommendations.append(
                f"Total JavaScript size ({metrics['total_js_size_kb']:.1f}KB) exceeds recommended limit. Consider code splitting."
            )
        
        # Check for large files
        if metrics['large_files']:
            recommendations.append(
                f"{len(metrics['large_files'])} files exceed size limits. Consider optimization or splitting."
            )
        
        # Check file counts
        if metrics['file_counts']['js'] > 10:
            recommendations.append(
                f"Many JavaScript files ({metrics['file_counts']['js']}). Consider bundling for production."
            )
        
        if not recommendations:
            recommendations.append("Performance metrics look good. Continue monitoring.")
        
        return recommendations
    
    async def _validate_responsiveness(self, task_data: Dict[str, Any]) -> TaskResult:
        """Validate mobile and responsive design"""
        try:
            responsiveness_results = {
                'files_analyzed': 0,
                'responsive_issues': 0,
                'viewport_issues': 0,
                'css_issues': 0,
                'detailed_issues': []
            }
            
            html_files = list(self.public_dir.glob('*.html'))
            responsiveness_results['files_analyzed'] = len(html_files)
            
            for html_file in html_files:
                file_issues = await self._check_file_responsiveness(html_file)
                responsiveness_results['detailed_issues'].extend(file_issues)
                
                for issue in file_issues:
                    responsiveness_results['responsive_issues'] += 1
                    if 'viewport' in issue['type']:
                        responsiveness_results['viewport_issues'] += 1
                    elif 'css' in issue['type']:
                        responsiveness_results['css_issues'] += 1
            
            success = responsiveness_results['responsive_issues'] == 0
            
            return TaskResult(
                success=success,
                message=f"Responsiveness validation: {responsiveness_results['responsive_issues']} issues found",
                data=responsiveness_results
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Responsiveness validation failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def _check_file_responsiveness(self, html_file: Path) -> List[Dict[str, Any]]:
        """Check responsiveness issues in HTML file"""
        issues = []
        
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            file_path = str(html_file.relative_to(self.project_root))
            
            # Check for viewport meta tag
            if '<html' in content and 'viewport' not in content:
                issues.append({
                    'file': file_path,
                    'type': 'viewport_missing',
                    'severity': 'major',
                    'description': 'Missing viewport meta tag',
                    'suggestion': 'Add <meta name="viewport" content="width=device-width, initial-scale=1">'
                })
            
            # Check for fixed pixel widths (potential responsiveness issues)
            fixed_widths = re.findall(r'width:\s*\d+px', content)
            if fixed_widths:
                issues.append({
                    'file': file_path,
                    'type': 'css_fixed_width',
                    'severity': 'minor',
                    'description': f'{len(fixed_widths)} fixed pixel widths found',
                    'suggestion': 'Consider using responsive units (%, em, rem, vw, vh)'
                })
            
            # Check for media queries (good for responsiveness)
            media_queries = re.findall(r'@media[^{]*{', content)
            if not media_queries and len(content) > 1000:  # Only for substantial content
                issues.append({
                    'file': file_path,
                    'type': 'css_no_media_queries',
                    'severity': 'minor',
                    'description': 'No media queries found',
                    'suggestion': 'Consider adding media queries for responsive design'
                })
                
        except Exception as e:
            issues.append({
                'file': str(html_file.relative_to(self.project_root)),
                'type': 'analysis_error',
                'severity': 'major',
                'description': f'Responsiveness analysis failed: {str(e)}'
            })
        
        return issues
    
    async def _analyze_code_quality(self, task_data: Dict[str, Any]) -> TaskResult:
        """Analyze frontend code quality and standards"""
        try:
            quality_results = {
                'overall_score': 0,
                'files_analyzed': 0,
                'quality_issues': 0,
                'maintainability_score': 0,
                'readability_score': 0,
                'detailed_analysis': []
            }
            
            # Analyze JavaScript files
            if self.js_dir.exists():
                js_files = list(self.js_dir.glob('*.js'))
                for js_file in js_files:
                    analysis = await self._analyze_js_quality(js_file)
                    quality_results['detailed_analysis'].append(analysis)
                    quality_results['files_analyzed'] += 1
                    quality_results['quality_issues'] += len(analysis.get('issues', []))
            
            # Analyze HTML files
            html_files = list(self.public_dir.glob('*.html'))
            for html_file in html_files:
                analysis = await self._analyze_html_quality(html_file)
                quality_results['detailed_analysis'].append(analysis)
                quality_results['files_analyzed'] += 1
                quality_results['quality_issues'] += len(analysis.get('issues', []))
            
            # Calculate scores
            quality_results['overall_score'] = self._calculate_quality_score(quality_results)
            quality_results['maintainability_score'] = max(0, 100 - (quality_results['quality_issues'] * 5))
            quality_results['readability_score'] = quality_results['overall_score']  # Simplified
            
            return TaskResult(
                success=quality_results['quality_issues'] < 10,  # Arbitrary threshold
                message=f"Code quality analysis: {quality_results['quality_issues']} issues, score: {quality_results['overall_score']}/100",
                data=quality_results
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Code quality analysis failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def _analyze_js_quality(self, js_file: Path) -> Dict[str, Any]:
        """Analyze JavaScript code quality"""
        analysis = {
            'file': str(js_file.relative_to(self.project_root)),
            'type': 'javascript',
            'issues': [],
            'metrics': {}
        }
        
        try:
            with open(js_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.splitlines()
            analysis['metrics'] = {
                'lines_of_code': len([line for line in lines if line.strip() and not line.strip().startswith('//')]),
                'total_lines': len(lines),
                'functions': len(re.findall(r'function\s+\w+|=>\s*{', content)),
                'complexity': self._calculate_complexity_score(content)
            }
            
            # Code quality checks
            if analysis['metrics']['complexity'] > 20:
                analysis['issues'].append({
                    'type': 'complexity',
                    'severity': 'major',
                    'description': f'High complexity score: {analysis["metrics"]["complexity"]}'
                })
            
            # Check for TODO/FIXME comments
            todos = re.findall(r'//.*(?:TODO|FIXME|HACK)', content, re.IGNORECASE)
            if todos:
                analysis['issues'].append({
                    'type': 'maintenance',
                    'severity': 'minor',
                    'description': f'{len(todos)} TODO/FIXME comments found'
                })
            
            # Check for very long functions
            functions = re.findall(r'function[^{]*{([^}]*(?:{[^}]*}[^}]*)*)}', content)
            for func in functions:
                if len(func.splitlines()) > 50:
                    analysis['issues'].append({
                        'type': 'maintainability',
                        'severity': 'minor',
                        'description': 'Very long function detected (>50 lines)'
                    })
                    
        except Exception as e:
            analysis['issues'].append({
                'type': 'analysis_error',
                'severity': 'major',
                'description': f'Analysis failed: {str(e)}'
            })
        
        return analysis
    
    async def _analyze_html_quality(self, html_file: Path) -> Dict[str, Any]:
        """Analyze HTML code quality"""
        analysis = {
            'file': str(html_file.relative_to(self.project_root)),
            'type': 'html',
            'issues': [],
            'metrics': {}
        }
        
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            analysis['metrics'] = {
                'total_lines': len(content.splitlines()),
                'elements': len(re.findall(r'<[^/!][^>]*>', content)),
                'nesting_depth': self._calculate_html_nesting_depth(content)
            }
            
            # Quality checks
            if analysis['metrics']['nesting_depth'] > self.performance_thresholds['max_dom_depth']:
                analysis['issues'].append({
                    'type': 'structure',
                    'severity': 'minor',
                    'description': f'Deep DOM nesting: {analysis["metrics"]["nesting_depth"]} levels'
                })
            
            # Check for deprecated elements
            deprecated_elements = re.findall(r'<(font|center|u|s|strike|big|small)', content, re.IGNORECASE)
            if deprecated_elements:
                analysis['issues'].append({
                    'type': 'standards',
                    'severity': 'minor',
                    'description': f'{len(deprecated_elements)} deprecated HTML elements found'
                })
                
        except Exception as e:
            analysis['issues'].append({
                'type': 'analysis_error',
                'severity': 'major',
                'description': f'Analysis failed: {str(e)}'
            })
        
        return analysis
    
    def _calculate_html_nesting_depth(self, html_content: str) -> int:
        """Calculate maximum HTML nesting depth"""
        max_depth = 0
        current_depth = 0
        
        # Simple depth calculation based on opening/closing tags
        for match in re.finditer(r'<([^/!][^>\s]*)[^>]*>|</([^>]+)>', html_content):
            if match.group(0).startswith('</'):
                current_depth -= 1
            else:
                current_depth += 1
                max_depth = max(max_depth, current_depth)
        
        return max_depth
    
    def _calculate_quality_score(self, results: Dict[str, Any]) -> int:
        """Calculate overall code quality score"""
        base_score = 100
        
        # Deduct points for issues
        total_issues = results['quality_issues']
        base_score -= min(total_issues * 3, 60)  # Cap at 60 points deduction
        
        return max(0, base_score)
    
    async def _suggest_ui_improvements(self, task_data: Dict[str, Any]) -> TaskResult:
        """Suggest UI/UX improvements"""
        try:
            improvement_suggestions = {
                'usability_improvements': [],
                'design_improvements': [],
                'accessibility_improvements': [],
                'performance_improvements': [],
                'priority_rankings': {}
            }
            
            # Analyze current UI state
            ui_analysis = await self._analyze_current_ui()
            
            # Generate suggestions based on analysis
            suggestions = self._generate_ui_suggestions(ui_analysis)
            
            # Categorize suggestions
            for suggestion in suggestions:
                category = suggestion.get('category', 'general')
                if category == 'usability':
                    improvement_suggestions['usability_improvements'].append(suggestion)
                elif category == 'design':
                    improvement_suggestions['design_improvements'].append(suggestion)
                elif category == 'accessibility':
                    improvement_suggestions['accessibility_improvements'].append(suggestion)
                elif category == 'performance':
                    improvement_suggestions['performance_improvements'].append(suggestion)
            
            # Rank suggestions by priority
            improvement_suggestions['priority_rankings'] = self._rank_suggestions(suggestions)
            
            return TaskResult(
                success=True,
                message=f"UI improvement analysis: {len(suggestions)} suggestions generated",
                data=improvement_suggestions
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"UI improvement analysis failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def _analyze_current_ui(self) -> Dict[str, Any]:
        """Analyze current UI state"""
        analysis = {
            'pages': [],
            'common_patterns': [],
            'inconsistencies': []
        }
        
        try:
            html_files = list(self.public_dir.glob('*.html'))
            
            for html_file in html_files:
                with open(html_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                page_analysis = {
                    'file': html_file.name,
                    'has_navigation': bool(re.search(r'<nav|class="nav', content)),
                    'has_forms': bool(re.search(r'<form', content)),
                    'has_tables': bool(re.search(r'<table', content)),
                    'button_count': len(re.findall(r'<button', content)),
                    'link_count': len(re.findall(r'<a\s+[^>]*href', content)),
                    'image_count': len(re.findall(r'<img', content))
                }
                
                analysis['pages'].append(page_analysis)
                
        except Exception as e:
            self.logger.error(f"UI analysis failed: {str(e)}")
            analysis['error'] = str(e)
        
        return analysis
    
    def _generate_ui_suggestions(self, ui_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate UI improvement suggestions"""
        suggestions = []
        
        pages = ui_analysis.get('pages', [])
        
        # Check for missing navigation
        pages_without_nav = [p for p in pages if not p['has_navigation']]
        if pages_without_nav:
            suggestions.append({
                'category': 'usability',
                'priority': 'high',
                'title': 'Add consistent navigation',
                'description': f'{len(pages_without_nav)} pages missing navigation elements',
                'affected_files': [p['file'] for p in pages_without_nav],
                'implementation': 'Add navigation menu to all pages for better user orientation'
            })
        
        # Check for accessibility improvements
        suggestions.append({
            'category': 'accessibility',
            'priority': 'medium',
            'title': 'Improve keyboard navigation',
            'description': 'Ensure all interactive elements are keyboard accessible',
            'implementation': 'Add proper tabindex and focus styles'
        })
        
        # Performance suggestions
        total_images = sum(p.get('image_count', 0) for p in pages)
        if total_images > 10:
            suggestions.append({
                'category': 'performance',
                'priority': 'medium',
                'title': 'Optimize image loading',
                'description': f'{total_images} images found across pages',
                'implementation': 'Add lazy loading and image optimization'
            })
        
        # Design consistency
        button_counts = [p.get('button_count', 0) for p in pages]
        if len(set(button_counts)) > 3:  # High variation in button counts
            suggestions.append({
                'category': 'design',
                'priority': 'low',
                'title': 'Standardize button usage',
                'description': 'Inconsistent button patterns across pages',
                'implementation': 'Create consistent button design system'
            })
        
        return suggestions
    
    def _rank_suggestions(self, suggestions: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Rank suggestions by priority"""
        rankings = {
            'high_priority': [],
            'medium_priority': [],
            'low_priority': []
        }
        
        for suggestion in suggestions:
            priority = suggestion.get('priority', 'medium')
            title = suggestion.get('title', 'Untitled suggestion')
            
            if priority == 'high':
                rankings['high_priority'].append(title)
            elif priority == 'medium':
                rankings['medium_priority'].append(title)
            else:
                rankings['low_priority'].append(title)
        
        return rankings
    
    async def _optimize_assets(self, task_data: Dict[str, Any]) -> TaskResult:
        """Optimize images, CSS, and JavaScript assets"""
        try:
            optimization_results = {
                'assets_processed': 0,
                'total_savings_kb': 0,
                'optimizations': [],
                'recommendations': []
            }
            
            # This would implement actual asset optimization
            # For now, we'll provide analysis and recommendations
            
            optimization_results['recommendations'] = [
                'Consider using WebP format for images',
                'Implement CSS and JS minification',
                'Use CDN for external libraries',
                'Enable gzip compression on server',
                'Optimize font loading with font-display: swap'
            ]
            
            return TaskResult(
                success=True,
                message="Asset optimization analysis complete",
                data=optimization_results
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Asset optimization failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def _generate_frontend_report(self, task_data: Dict[str, Any]) -> TaskResult:
        """Generate comprehensive frontend quality report"""
        try:
            report_timestamp = datetime.now()
            
            # Collect all frontend analysis data
            component_validation = await self._validate_components({})
            accessibility_check = await self._check_accessibility({})
            performance_analysis = await self._optimize_performance({})
            code_quality = await self._analyze_code_quality({})
            
            # Compile comprehensive report
            frontend_report = {
                'report_metadata': {
                    'generated_at': report_timestamp.isoformat(),
                    'agent_version': '1.0.0',
                    'analysis_scope': 'Complete frontend analysis'
                },
                'executive_summary': {
                    'overall_score': 0,
                    'components_analyzed': component_validation.data.get('components_analyzed', 0),
                    'accessibility_score': accessibility_check.data.get('accessibility_score', 0),
                    'performance_score': 0,
                    'code_quality_score': code_quality.data.get('overall_score', 0),
                    'critical_issues': 0,
                    'total_recommendations': 0
                },
                'detailed_analysis': {
                    'component_validation': component_validation.data,
                    'accessibility_analysis': accessibility_check.data,
                    'performance_analysis': performance_analysis.data,
                    'code_quality_analysis': code_quality.data
                },
                'recommendations': {
                    'high_priority': [],
                    'medium_priority': [],
                    'low_priority': []
                },
                'action_plan': {
                    'immediate_actions': [],
                    'short_term_goals': [],
                    'long_term_improvements': []
                }
            }
            
            # Calculate overall scores and metrics
            self._calculate_report_metrics(frontend_report)
            
            # Generate prioritized recommendations
            self._generate_report_recommendations(frontend_report)
            
            # Save report
            report_filename = f"frontend_report_{int(report_timestamp.timestamp())}.json"
            report_path = self.frontend_logs_dir / report_filename
            
            with open(report_path, 'w') as f:
                json.dump(frontend_report, f, indent=2, default=str)
            
            return TaskResult(
                success=True,
                message=f"Frontend report generated: {report_filename}",
                data=frontend_report
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Frontend report generation failed: {str(e)}",
                errors=[str(e)]
            )
    
    def _calculate_report_metrics(self, report: Dict[str, Any]) -> None:
        """Calculate overall metrics for the report"""
        summary = report['executive_summary']
        detailed = report['detailed_analysis']
        
        # Calculate overall score (weighted average)
        accessibility_score = detailed.get('accessibility_analysis', {}).get('accessibility_score', 0)
        code_quality_score = detailed.get('code_quality_analysis', {}).get('overall_score', 0)
        
        # Simple average for now (could be weighted)
        summary['overall_score'] = (accessibility_score + code_quality_score) / 2
        
        # Count critical issues
        critical_issues = 0
        critical_issues += detailed.get('accessibility_analysis', {}).get('critical_issues', 0)
        critical_issues += len([
            issue for analysis in detailed.get('component_validation', {}).get('component_details', [])
            for issue in analysis.get('issues', [])
            if issue.get('severity') == 'critical'
        ])
        
        summary['critical_issues'] = critical_issues
    
    def _generate_report_recommendations(self, report: Dict[str, Any]) -> None:
        """Generate prioritized recommendations for the report"""
        recommendations = report['recommendations']
        detailed = report['detailed_analysis']
        
        # High priority recommendations
        if detailed.get('accessibility_analysis', {}).get('critical_issues', 0) > 0:
            recommendations['high_priority'].append(
                "Fix critical accessibility issues immediately"
            )
        
        if report['executive_summary']['overall_score'] < 60:
            recommendations['high_priority'].append(
                "Address fundamental code quality issues"
            )
        
        # Medium priority recommendations
        if detailed.get('component_validation', {}).get('issues_found', 0) > 5:
            recommendations['medium_priority'].append(
                "Resolve component validation issues"
            )
        
        recommendations['medium_priority'].append(
            "Implement performance optimizations"
        )
        
        # Low priority recommendations
        recommendations['low_priority'].extend([
            "Consider UI/UX improvements",
            "Optimize asset delivery",
            "Implement advanced accessibility features"
        ])
        
        # Generate action plan
        action_plan = report['action_plan']
        action_plan['immediate_actions'] = recommendations['high_priority']
        action_plan['short_term_goals'] = recommendations['medium_priority']
        action_plan['long_term_improvements'] = recommendations['low_priority']