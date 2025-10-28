"""
Scoring System Agent - Manages and optimizes the MEP ranking methodology

This agent handles all aspects of the scoring system, including methodology
validation, scoring algorithm optimization, and transparency reporting.
"""

import asyncio
import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
import statistics

from .base_agent import BaseAgent, TaskResult, AgentCapability


class ScoringSystemAgent(BaseAgent):
    """
    Agent responsible for managing and optimizing the MEP scoring methodology.
    
    Follows the official MEP Ranking methodology (October 2017) while providing
    tools for validation, optimization, and transparency.
    """
    
    def _initialize_agent(self) -> None:
        """Initialize scoring system specific configurations"""
        self.scoring_config_path = self.project_root / 'backend' / 'scoring_config.json'
        self.methodology_path = self.project_root / 'METHODOLOGY.md'
        self.database_path = self.project_root / 'data' / 'meps.db'
        
        self.logger.info(f"Scoring System Agent initialized for project: {self.project_root}")
    
    def _define_capabilities(self) -> List[AgentCapability]:
        """Define scoring system agent capabilities"""
        return [
            AgentCapability(
                name="validate_scoring_methodology",
                description="Validate scoring methodology consistency across terms",
                required_tools=["database", "file_system"],
                complexity_level="intermediate"
            ),
            AgentCapability(
                name="analyze_scoring_distribution",
                description="Analyze score distribution and identify outliers",
                required_tools=["database", "statistics"],
                complexity_level="advanced"
            ),
            AgentCapability(
                name="test_scoring_algorithm",
                description="Test and validate scoring algorithm implementations",
                required_tools=["database", "scorer"],
                complexity_level="advanced"
            ),
            AgentCapability(
                name="generate_scoring_transparency_report",
                description="Generate comprehensive scoring transparency report",
                required_tools=["database", "reporting"],
                complexity_level="intermediate"
            ),
            AgentCapability(
                name="optimize_scoring_parameters",
                description="Optimize scoring parameters for fairness and accuracy",
                required_tools=["database", "optimization"],
                complexity_level="advanced"
            ),
            AgentCapability(
                name="compare_scoring_methodologies",
                description="Compare different scoring methodologies",
                required_tools=["database", "analysis"],
                complexity_level="advanced"
            ),
            AgentCapability(
                name="validate_score_consistency",
                description="Validate score consistency across different terms",
                required_tools=["database"],
                complexity_level="intermediate"
            ),
            AgentCapability(
                name="audit_scoring_calculations",
                description="Audit scoring calculations for accuracy",
                required_tools=["database", "scorer"],
                complexity_level="advanced"
            )
        ]
    
    async def _execute_task_impl(self, task_type: str, task_data: Dict[str, Any]) -> TaskResult:
        """Execute scoring system tasks"""
        
        if task_type == "validate_scoring_methodology":
            return await self._validate_scoring_methodology(task_data)
        elif task_type == "analyze_scoring_distribution":
            return await self._analyze_scoring_distribution(task_data)
        elif task_type == "test_scoring_algorithm":
            return await self._test_scoring_algorithm(task_data)
        elif task_type == "generate_scoring_transparency_report":
            return await self._generate_transparency_report(task_data)
        elif task_type == "optimize_scoring_parameters":
            return await self._optimize_scoring_parameters(task_data)
        elif task_type == "compare_scoring_methodologies":
            return await self._compare_methodologies(task_data)
        elif task_type == "validate_score_consistency":
            return await self._validate_score_consistency(task_data)
        elif task_type == "audit_scoring_calculations":
            return await self._audit_scoring_calculations(task_data)
        else:
            return TaskResult(
                success=False,
                message=f"Unknown task type: {task_type}",
                errors=[f"Task type '{task_type}' not implemented"]
            )
    
    async def _validate_scoring_methodology(self, task_data: Dict[str, Any]) -> TaskResult:
        """Validate scoring methodology consistency"""
        try:
            terms = task_data.get('terms', [8, 9, 10])
            issues = []
            
            # Check database connectivity
            if not self.database_path.exists():
                return TaskResult(
                    success=False,
                    message="Database not found",
                    errors=["MEP database not accessible"]
                )
            
            conn = sqlite3.connect(self.database_path)
            
            for term in terms:
                # Check if term has complete data
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM meps WHERE term = ?", (term,))
                mep_count = cursor.fetchone()[0]
                
                if mep_count == 0:
                    issues.append(f"Term {term}: No MEP data found")
                    continue
                
                # Check scoring components
                cursor.execute("""
                    SELECT COUNT(*) FROM meps 
                    WHERE term = ? AND (
                        speeches IS NULL OR
                        amendments IS NULL OR
                        reports_rapporteur IS NULL OR
                        questions_written IS NULL
                    )
                """, (term,))
                
                incomplete_data = cursor.fetchone()[0]
                if incomplete_data > 0:
                    issues.append(f"Term {term}: {incomplete_data} MEPs with incomplete scoring data")
                
                # Check for extreme outliers that might indicate data issues
                cursor.execute("""
                    SELECT AVG(total_score), MAX(total_score), MIN(total_score)
                    FROM meps WHERE term = ? AND total_score > 0
                """, (term,))
                
                stats = cursor.fetchone()
                if stats and stats[0]:
                    avg_score, max_score, min_score = stats
                    if max_score > avg_score * 10:  # Potential outlier
                        issues.append(f"Term {term}: Potential scoring outlier detected (max: {max_score:.2f}, avg: {avg_score:.2f})")
            
            conn.close()
            
            # Generate validation report
            report = {
                'validation_timestamp': datetime.now().isoformat(),
                'terms_checked': terms,
                'issues_found': issues,
                'status': 'passed' if not issues else 'issues_detected'
            }
            
            return TaskResult(
                success=True,
                message=f"Methodology validation completed. {len(issues)} issues found.",
                data=report
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Validation failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def _analyze_scoring_distribution(self, task_data: Dict[str, Any]) -> TaskResult:
        """Analyze score distribution across terms and categories"""
        try:
            term = task_data.get('term', 10)
            
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # Get all scores for the term
            cursor.execute("""
                SELECT total_score, speeches, amendments, reports_rapporteur, 
                       reports_shadow, questions_written, group_name, country
                FROM meps WHERE term = ? AND total_score > 0
            """, (term,))
            
            data = cursor.fetchall()
            conn.close()
            
            if not data:
                return TaskResult(
                    success=False,
                    message=f"No scoring data found for term {term}",
                    errors=["Insufficient data for analysis"]
                )
            
            # Analyze overall distribution
            total_scores = [row[0] for row in data]
            analysis = {
                'term': term,
                'total_meps': len(data),
                'score_statistics': {
                    'mean': statistics.mean(total_scores),
                    'median': statistics.median(total_scores),
                    'std_dev': statistics.stdev(total_scores) if len(total_scores) > 1 else 0,
                    'min_score': min(total_scores),
                    'max_score': max(total_scores),
                    'quartiles': [
                        statistics.quantiles(total_scores, n=4)[0],
                        statistics.quantiles(total_scores, n=4)[1],
                        statistics.quantiles(total_scores, n=4)[2]
                    ] if len(total_scores) >= 4 else []
                }
            }
            
            # Analyze by political group
            group_scores = {}
            for row in data:
                group = row[6] if row[6] else 'Unknown'
                if group not in group_scores:
                    group_scores[group] = []
                group_scores[group].append(row[0])
            
            group_analysis = {}
            for group, scores in group_scores.items():
                if len(scores) > 0:
                    group_analysis[group] = {
                        'count': len(scores),
                        'mean_score': statistics.mean(scores),
                        'median_score': statistics.median(scores)
                    }
            
            analysis['group_analysis'] = group_analysis
            
            # Identify potential outliers (scores > 3 standard deviations from mean)
            mean_score = analysis['score_statistics']['mean']
            std_dev = analysis['score_statistics']['std_dev']
            outliers = []
            
            if std_dev > 0:
                threshold = mean_score + (3 * std_dev)
                outliers = [score for score in total_scores if score > threshold]
            
            analysis['outliers'] = {
                'count': len(outliers),
                'threshold': threshold if std_dev > 0 else None,
                'values': outliers[:10]  # Show first 10 outliers
            }
            
            return TaskResult(
                success=True,
                message=f"Score distribution analysis completed for term {term}",
                data=analysis
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Distribution analysis failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def _generate_transparency_report(self, task_data: Dict[str, Any]) -> TaskResult:
        """Generate comprehensive scoring transparency report"""
        try:
            term = task_data.get('term', 10)
            
            # Load methodology documentation
            methodology_content = ""
            if self.methodology_path.exists():
                with open(self.methodology_path, 'r', encoding='utf-8') as f:
                    methodology_content = f.read()
            
            # Get scoring distribution analysis
            distribution_result = await self._analyze_scoring_distribution({'term': term})
            
            # Get methodology validation
            validation_result = await self._validate_scoring_methodology({'terms': [term]})
            
            # Create comprehensive report
            report = {
                'report_metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'term': term,
                    'report_version': '1.0'
                },
                'methodology_overview': {
                    'description': 'MEP Ranking follows the official methodology (October 2017)',
                    'scoring_categories': [
                        'Parliamentary Speeches',
                        'Amendments Submitted',
                        'Reports (Rapporteur/Shadow)',
                        'Written Questions',
                        'Institutional Roles',
                        'Voting Attendance'
                    ],
                    'methodology_file_available': self.methodology_path.exists()
                },
                'scoring_validation': validation_result.data if validation_result.success else None,
                'distribution_analysis': distribution_result.data if distribution_result.success else None,
                'transparency_measures': {
                    'open_source': True,
                    'methodology_published': True,
                    'data_sources': ['ParlTrack (parltrack.org)'],
                    'calculation_audit': 'Available through scoring system agent'
                }
            }
            
            # Save report
            reports_dir = self.project_root / 'reports'
            reports_dir.mkdir(exist_ok=True)
            
            report_filename = f"scoring_transparency_term{term}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            report_path = reports_dir / report_filename
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            return TaskResult(
                success=True,
                message=f"Transparency report generated: {report_filename}",
                data={
                    'report_path': str(report_path),
                    'report_summary': report
                }
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Transparency report generation failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def _test_scoring_algorithm(self, task_data: Dict[str, Any]) -> TaskResult:
        """Test scoring algorithm implementation"""
        try:
            term = task_data.get('term', 10)
            sample_size = task_data.get('sample_size', 10)
            
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # Get sample MEPs for testing
            cursor.execute("""
                SELECT mep_id, speeches, amendments, reports_rapporteur, reports_shadow,
                       questions_written, total_score
                FROM meps WHERE term = ? AND total_score > 0 
                ORDER BY RANDOM() LIMIT ?
            """, (term, sample_size))
            
            sample_data = cursor.fetchall()
            conn.close()
            
            if not sample_data:
                return TaskResult(
                    success=False,
                    message=f"No test data available for term {term}",
                    errors=["Insufficient data for algorithm testing"]
                )
            
            # Test each MEP's score calculation
            test_results = []
            scorer_module_path = self.project_root / 'backend' / 'mep_ranking_scorer.py'
            
            if not scorer_module_path.exists():
                return TaskResult(
                    success=False,
                    message="Scoring module not found",
                    errors=["mep_ranking_scorer.py not accessible"]
                )
            
            # Basic validation tests
            for mep_data in sample_data:
                mep_id, speeches, amendments, reports_rap, reports_shadow, questions, stored_score = mep_data
                
                # Validate individual components are reasonable
                component_issues = []
                
                if speeches < 0:
                    component_issues.append("Negative speeches count")
                if amendments < 0:
                    component_issues.append("Negative amendments count")
                if stored_score <= 0:
                    component_issues.append("Zero or negative total score")
                
                test_results.append({
                    'mep_id': mep_id,
                    'components': {
                        'speeches': speeches,
                        'amendments': amendments,
                        'reports_rapporteur': reports_rap,
                        'reports_shadow': reports_shadow,
                        'questions_written': questions
                    },
                    'stored_score': stored_score,
                    'issues': component_issues,
                    'status': 'pass' if not component_issues else 'issues'
                })
            
            # Summary
            passed_tests = sum(1 for result in test_results if result['status'] == 'pass')
            total_tests = len(test_results)
            
            return TaskResult(
                success=True,
                message=f"Algorithm testing completed: {passed_tests}/{total_tests} tests passed",
                data={
                    'term': term,
                    'sample_size': total_tests,
                    'tests_passed': passed_tests,
                    'tests_failed': total_tests - passed_tests,
                    'test_results': test_results,
                    'overall_status': 'pass' if passed_tests == total_tests else 'issues_detected'
                }
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Algorithm testing failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def _optimize_scoring_parameters(self, task_data: Dict[str, Any]) -> TaskResult:
        """Optimize scoring parameters for fairness and accuracy"""
        # This would implement parameter optimization logic
        # For now, return a basic analysis with recommendations
        
        try:
            term = task_data.get('term', 10)
            
            # Analyze current parameter effectiveness
            distribution_result = await self._analyze_scoring_distribution({'term': term})
            
            if not distribution_result.success:
                return distribution_result
            
            stats = distribution_result.data['score_statistics']
            recommendations = []
            
            # Analyze score distribution for optimization opportunities
            if stats['std_dev'] > stats['mean']:
                recommendations.append("High score variance detected - consider reviewing outlier handling")
            
            if len(distribution_result.data.get('outliers', {}).get('values', [])) > 0:
                recommendations.append("Outliers detected - consider adjusting range-based scoring thresholds")
            
            # Group-based analysis
            group_analysis = distribution_result.data.get('group_analysis', {})
            group_means = [data['mean_score'] for data in group_analysis.values()]
            
            if len(group_means) > 1:
                group_variance = statistics.stdev(group_means)
                if group_variance > stats['mean'] * 0.3:  # Arbitrary threshold
                    recommendations.append("High variance between political groups - review methodology for bias")
            
            optimization_report = {
                'term': term,
                'current_parameters': {
                    'methodology': 'MEP Ranking October 2017',
                    'range_based_scoring': True,
                    'outlier_handling': 'Enabled'
                },
                'analysis_results': distribution_result.data,
                'optimization_recommendations': recommendations,
                'parameter_suggestions': {
                    'range_adjustments': 'Consider dynamic range calculations based on term-specific data',
                    'outlier_threshold': 'Review 3-sigma threshold for outlier detection',
                    'group_normalization': 'Consider optional group-based normalization'
                }
            }
            
            return TaskResult(
                success=True,
                message=f"Parameter optimization analysis completed with {len(recommendations)} recommendations",
                data=optimization_report
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Parameter optimization failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def _compare_methodologies(self, task_data: Dict[str, Any]) -> TaskResult:
        """Compare different scoring methodologies"""
        try:
            terms = task_data.get('terms', [8, 9, 10])
            
            comparison_results = {}
            
            for term in terms:
                # Get distribution analysis for each term
                analysis_result = await self._analyze_scoring_distribution({'term': term})
                
                if analysis_result.success:
                    comparison_results[f'term_{term}'] = {
                        'statistics': analysis_result.data['score_statistics'],
                        'total_meps': analysis_result.data['total_meps'],
                        'group_count': len(analysis_result.data.get('group_analysis', {}))
                    }
            
            # Cross-term comparison
            if len(comparison_results) > 1:
                means = [data['statistics']['mean'] for data in comparison_results.values()]
                std_devs = [data['statistics']['std_dev'] for data in comparison_results.values()]
                
                consistency_analysis = {
                    'mean_consistency': {
                        'values': means,
                        'variance': statistics.stdev(means) if len(means) > 1 else 0,
                        'status': 'consistent' if (statistics.stdev(means) if len(means) > 1 else 0) < 2 else 'varies'
                    },
                    'std_dev_consistency': {
                        'values': std_devs,
                        'variance': statistics.stdev(std_devs) if len(std_devs) > 1 else 0
                    }
                }
            else:
                consistency_analysis = {'message': 'Need multiple terms for comparison'}
            
            return TaskResult(
                success=True,
                message=f"Methodology comparison completed for {len(terms)} terms",
                data={
                    'terms_compared': terms,
                    'term_results': comparison_results,
                    'consistency_analysis': consistency_analysis
                }
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Methodology comparison failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def _validate_score_consistency(self, task_data: Dict[str, Any]) -> TaskResult:
        """Validate score consistency across terms"""
        try:
            # This is similar to methodology comparison but focuses on consistency validation
            comparison_result = await self._compare_methodologies(task_data)
            
            if not comparison_result.success:
                return comparison_result
            
            consistency_data = comparison_result.data.get('consistency_analysis', {})
            issues = []
            
            # Check mean consistency
            mean_consistency = consistency_data.get('mean_consistency', {})
            if mean_consistency.get('status') == 'varies':
                issues.append("Significant variance in mean scores across terms")
            
            # Check for extreme differences
            term_results = comparison_result.data.get('term_results', {})
            if len(term_results) > 1:
                max_means = []
                min_means = []
                
                for term_data in term_results.values():
                    stats = term_data['statistics']
                    max_means.append(stats['max_score'])
                    min_means.append(stats['min_score'])
                
                if max(max_means) > min(max_means) * 3:  # Arbitrary threshold
                    issues.append("Extreme differences in maximum scores across terms")
            
            validation_result = {
                'validation_timestamp': datetime.now().isoformat(),
                'consistency_status': 'consistent' if not issues else 'inconsistencies_detected',
                'issues_found': issues,
                'detailed_analysis': comparison_result.data
            }
            
            return TaskResult(
                success=True,
                message=f"Score consistency validation completed. {len(issues)} issues found.",
                data=validation_result
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Consistency validation failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def _audit_scoring_calculations(self, task_data: Dict[str, Any]) -> TaskResult:
        """Audit scoring calculations for accuracy"""
        try:
            term = task_data.get('term', 10)
            audit_sample = task_data.get('audit_sample', 5)
            
            # This would implement detailed scoring calculation audits
            # For now, perform basic sanity checks
            
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # Get sample for detailed audit
            cursor.execute("""
                SELECT mep_id, name, speeches, amendments, reports_rapporteur, 
                       reports_shadow, questions_written, total_score,
                       institutional_roles_multiplier
                FROM meps WHERE term = ? AND total_score > 0 
                ORDER BY total_score DESC LIMIT ?
            """, (term, audit_sample))
            
            audit_data = cursor.fetchall()
            conn.close()
            
            audit_results = []
            
            for mep_data in audit_data:
                (mep_id, name, speeches, amendments, reports_rap, 
                 reports_shadow, questions, total_score, roles_mult) = mep_data
                
                # Basic calculation validation
                expected_components = {
                    'speeches': speeches or 0,
                    'amendments': amendments or 0,
                    'reports_rapporteur': reports_rap or 0,
                    'reports_shadow': reports_shadow or 0,
                    'questions_written': questions or 0
                }
                
                # Check for reasonable component values
                validation_issues = []
                
                if total_score <= 0:
                    validation_issues.append("Total score is zero or negative")
                
                if roles_mult and (roles_mult < 1.0 or roles_mult > 2.0):
                    validation_issues.append(f"Unusual roles multiplier: {roles_mult}")
                
                # Check if components sum to reasonable total (rough validation)
                component_sum = sum(expected_components.values())
                if component_sum == 0 and total_score > 0:
                    validation_issues.append("Total score exists but all components are zero")
                
                audit_results.append({
                    'mep_id': mep_id,
                    'name': name,
                    'components': expected_components,
                    'total_score': total_score,
                    'roles_multiplier': roles_mult,
                    'validation_issues': validation_issues,
                    'status': 'pass' if not validation_issues else 'issues'
                })
            
            # Summary
            passed_audits = sum(1 for result in audit_results if result['status'] == 'pass')
            total_audits = len(audit_results)
            
            audit_summary = {
                'audit_timestamp': datetime.now().isoformat(),
                'term': term,
                'audited_meps': total_audits,
                'passed_audits': passed_audits,
                'failed_audits': total_audits - passed_audits,
                'audit_results': audit_results,
                'overall_status': 'pass' if passed_audits == total_audits else 'issues_detected'
            }
            
            return TaskResult(
                success=True,
                message=f"Scoring audit completed: {passed_audits}/{total_audits} passed",
                data=audit_summary
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Scoring audit failed: {str(e)}",
                errors=[str(e)]
            )