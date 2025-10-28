"""
Analytics & Insights Agent - Generate insights and usage analytics

This agent handles user behavior analysis, performance metrics collection,
trend analysis, and automated insights generation.
"""

import asyncio
import json
import sqlite3
import statistics
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter

from .base_agent import BaseAgent, TaskResult, AgentCapability


class AnalyticsInsightsAgent(BaseAgent):
    """
    Agent responsible for generating insights and usage analytics.
    
    Analyzes MEP activity patterns, user behavior, application performance,
    and generates actionable insights for stakeholders.
    """
    
    def _initialize_agent(self) -> None:
        """Initialize analytics and insights configurations"""
        self.analytics_config = {
            'trend_analysis_periods': [30, 90, 365],  # days
            'activity_categories': [
                'speeches', 'amendments', 'questions_written', 'questions_oral',
                'reports_rapporteur', 'reports_shadow', 'votes_attended'
            ],
            'performance_metrics': [
                'response_time', 'error_rate', 'user_sessions', 'page_views'
            ],
            'insight_thresholds': {
                'significant_change': 0.2,  # 20% change threshold
                'outlier_threshold': 3.0,   # 3 standard deviations
                'trend_confidence': 0.8     # 80% confidence for trends
            }
        }
        
        self.database_path = self.project_root / 'data' / 'meps.db'
        self.analytics_db_path = self.project_root / 'data' / 'analytics.db'
        
        self.logger.info(f"Analytics Insights Agent initialized for project: {self.project_root}")
    
    def _define_capabilities(self) -> List[AgentCapability]:
        """Define analytics and insights agent capabilities"""
        return [
            AgentCapability(
                name="analyze_mep_activity_trends",
                description="Analyze MEP activity trends over time and across terms",
                required_tools=["database", "statistics"],
                complexity_level="advanced"
            ),
            AgentCapability(
                name="generate_performance_insights",
                description="Generate insights about application performance and usage",
                required_tools=["performance_monitoring", "analytics"],
                complexity_level="intermediate"
            ),
            AgentCapability(
                name="analyze_political_group_patterns",
                description="Analyze activity patterns across political groups",
                required_tools=["database", "statistical_analysis"],
                complexity_level="advanced"
            ),
            AgentCapability(
                name="detect_activity_anomalies",
                description="Detect unusual patterns or anomalies in MEP activities",
                required_tools=["database", "anomaly_detection"],
                complexity_level="advanced"
            ),
            AgentCapability(
                name="generate_usage_analytics",
                description="Analyze application usage patterns and user behavior",
                required_tools=["web_analytics", "database"],
                complexity_level="intermediate"
            ),
            AgentCapability(
                name="create_insights_dashboard",
                description="Create comprehensive analytics dashboard",
                required_tools=["visualization", "data_aggregation"],
                complexity_level="advanced"
            ),
            AgentCapability(
                name="analyze_scoring_distribution",
                description="Analyze MEP score distributions and patterns",
                required_tools=["database", "statistics"],
                complexity_level="intermediate"
            ),
            AgentCapability(
                name="generate_comparative_analysis",
                description="Generate comparative analysis across terms, groups, and countries",
                required_tools=["database", "comparative_analysis"],
                complexity_level="advanced"
            ),
            AgentCapability(
                name="predict_activity_trends",
                description="Predict future activity trends based on historical data",
                required_tools=["machine_learning", "time_series"],
                complexity_level="advanced"
            )
        ]
    
    async def _execute_task_impl(self, task_type: str, task_data: Dict[str, Any]) -> TaskResult:
        """Execute analytics and insights tasks"""
        
        if task_type == "analyze_mep_activity_trends":
            return await self._analyze_mep_activity_trends(task_data)
        elif task_type == "generate_performance_insights":
            return await self._generate_performance_insights(task_data)
        elif task_type == "analyze_political_group_patterns":
            return await self._analyze_political_group_patterns(task_data)
        elif task_type == "detect_activity_anomalies":
            return await self._detect_activity_anomalies(task_data)
        elif task_type == "generate_usage_analytics":
            return await self._generate_usage_analytics(task_data)
        elif task_type == "create_insights_dashboard":
            return await self._create_insights_dashboard(task_data)
        elif task_type == "analyze_scoring_distribution":
            return await self._analyze_scoring_distribution(task_data)
        elif task_type == "generate_comparative_analysis":
            return await self._generate_comparative_analysis(task_data)
        elif task_type == "predict_activity_trends":
            return await self._predict_activity_trends(task_data)
        else:
            return TaskResult(
                success=False,
                message=f"Unknown task type: {task_type}",
                errors=[f"Task type '{task_type}' not implemented"]
            )
    
    async def _analyze_mep_activity_trends(self, task_data: Dict[str, Any]) -> TaskResult:
        """Analyze MEP activity trends over time and across terms"""
        try:
            terms = task_data.get('terms', [8, 9, 10])
            activity_categories = task_data.get('categories', self.analytics_config['activity_categories'])
            
            if not self.database_path.exists():
                return TaskResult(
                    success=False,
                    message="Database not found",
                    errors=["MEP database not accessible"]
                )
            
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            trend_analysis = {
                'analysis_timestamp': datetime.now().isoformat(),
                'terms_analyzed': terms,
                'activity_trends': {},
                'cross_term_comparison': {},
                'insights': []
            }
            
            # Analyze trends for each activity category
            for activity in activity_categories:
                if activity not in ['speeches', 'amendments', 'questions_written', 'reports_rapporteur']:
                    continue  # Skip if column doesn't exist
                
                activity_data = {}
                
                for term in terms:
                    cursor.execute(f"""
                        SELECT AVG({activity}), COUNT(*), MIN({activity}), MAX({activity}), 
                               STDEV({activity}) as std_dev
                        FROM meps 
                        WHERE term = ? AND {activity} IS NOT NULL AND {activity} >= 0
                    """, (term,))
                    
                    result = cursor.fetchone()
                    if result and result[0] is not None:
                        activity_data[f'term_{term}'] = {
                            'average': float(result[0]),
                            'count': result[1],
                            'min': result[2],
                            'max': result[3],
                            'std_dev': float(result[4]) if result[4] else 0
                        }
                
                trend_analysis['activity_trends'][activity] = activity_data
                
                # Calculate cross-term trends
                if len(activity_data) > 1:
                    averages = [data['average'] for data in activity_data.values()]
                    
                    if len(averages) >= 2:
                        # Calculate trend direction
                        trend_direction = 'increasing' if averages[-1] > averages[0] else 'decreasing'
                        trend_magnitude = abs(averages[-1] - averages[0]) / averages[0] if averages[0] > 0 else 0
                        
                        trend_analysis['cross_term_comparison'][activity] = {
                            'direction': trend_direction,
                            'magnitude': trend_magnitude,
                            'significance': 'significant' if trend_magnitude > self.analytics_config['insight_thresholds']['significant_change'] else 'minor'
                        }
                        
                        # Generate insights
                        if trend_magnitude > self.analytics_config['insight_thresholds']['significant_change']:
                            trend_analysis['insights'].append({
                                'type': 'trend_analysis',
                                'category': activity,
                                'insight': f"{activity.replace('_', ' ').title()} shows {trend_direction} trend of {trend_magnitude:.1%} across terms",
                                'significance': 'high' if trend_magnitude > 0.5 else 'medium'
                            })
            
            # Analyze overall activity levels
            cursor.execute("""
                SELECT term, AVG(total_score), COUNT(*), AVG(speeches + amendments + questions_written)
                FROM meps 
                WHERE term IN ({}) AND total_score > 0
                GROUP BY term
                ORDER BY term
            """.format(','.join('?' * len(terms))), terms)
            
            overall_trends = cursor.fetchall()
            
            trend_analysis['overall_activity'] = {}
            for term, avg_score, count, avg_activities in overall_trends:
                trend_analysis['overall_activity'][f'term_{term}'] = {
                    'average_score': float(avg_score),
                    'mep_count': count,
                    'average_activities': float(avg_activities) if avg_activities else 0
                }
            
            # Generate overall insights
            if len(overall_trends) > 1:
                score_trend = overall_trends[-1][1] - overall_trends[0][1]
                if abs(score_trend) > 1:  # Significant score change
                    direction = 'increased' if score_trend > 0 else 'decreased'
                    trend_analysis['insights'].append({
                        'type': 'overall_trend',
                        'insight': f"Overall MEP activity scores have {direction} by {abs(score_trend):.1f} points across terms",
                        'significance': 'high'
                    })
            
            conn.close()
            
            return TaskResult(
                success=True,
                message=f"Activity trend analysis completed for {len(terms)} terms and {len(activity_categories)} categories",
                data=trend_analysis
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Activity trend analysis failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def _analyze_political_group_patterns(self, task_data: Dict[str, Any]) -> TaskResult:
        """Analyze activity patterns across political groups"""
        try:
            term = task_data.get('term', 10)
            
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # Get group-level statistics
            cursor.execute("""
                SELECT group_name, 
                       COUNT(*) as mep_count,
                       AVG(total_score) as avg_score,
                       AVG(speeches) as avg_speeches,
                       AVG(amendments) as avg_amendments,
                       AVG(questions_written) as avg_questions,
                       STDEV(total_score) as score_std_dev
                FROM meps 
                WHERE term = ? AND group_name IS NOT NULL AND total_score > 0
                GROUP BY group_name
                HAVING COUNT(*) >= 3
                ORDER BY avg_score DESC
            """, (term,))
            
            group_data = cursor.fetchall()
            
            group_analysis = {
                'analysis_timestamp': datetime.now().isoformat(),
                'term': term,
                'group_statistics': {},
                'group_rankings': [],
                'activity_patterns': {},
                'insights': []
            }
            
            # Process group statistics
            all_scores = []
            group_scores = {}
            
            for group_info in group_data:
                (group_name, mep_count, avg_score, avg_speeches, 
                 avg_amendments, avg_questions, score_std_dev) = group_info
                
                group_stats = {
                    'mep_count': mep_count,
                    'average_score': float(avg_score) if avg_score else 0,
                    'average_speeches': float(avg_speeches) if avg_speeches else 0,
                    'average_amendments': float(avg_amendments) if avg_amendments else 0,
                    'average_questions': float(avg_questions) if avg_questions else 0,
                    'score_std_dev': float(score_std_dev) if score_std_dev else 0
                }
                
                group_analysis['group_statistics'][group_name] = group_stats
                all_scores.append(avg_score)
                group_scores[group_name] = avg_score
            
            # Generate group rankings
            sorted_groups = sorted(group_scores.items(), key=lambda x: x[1], reverse=True)
            group_analysis['group_rankings'] = [
                {'rank': i+1, 'group': group, 'average_score': score}
                for i, (group, score) in enumerate(sorted_groups)
            ]
            
            # Analyze activity patterns
            if len(all_scores) > 1:
                overall_avg = statistics.mean(all_scores)
                score_std = statistics.stdev(all_scores)
                
                for group_name, stats in group_analysis['group_statistics'].items():
                    # Categorize groups by performance
                    score_deviation = (stats['average_score'] - overall_avg) / score_std if score_std > 0 else 0
                    
                    if score_deviation > 1:
                        performance_category = 'high_performer'
                    elif score_deviation < -1:
                        performance_category = 'low_performer'
                    else:
                        performance_category = 'average_performer'
                    
                    # Analyze activity specialization
                    specializations = []
                    if stats['average_speeches'] > overall_avg * 1.2:
                        specializations.append('speeches')
                    if stats['average_amendments'] > overall_avg * 1.2:
                        specializations.append('amendments')
                    if stats['average_questions'] > overall_avg * 1.2:
                        specializations.append('questions')
                    
                    group_analysis['activity_patterns'][group_name] = {
                        'performance_category': performance_category,
                        'score_deviation': score_deviation,
                        'specializations': specializations,
                        'diversity_index': len(specializations)  # Simple diversity measure
                    }
            
            # Generate insights
            if group_analysis['group_rankings']:
                top_group = group_analysis['group_rankings'][0]
                bottom_group = group_analysis['group_rankings'][-1]
                
                score_gap = top_group['average_score'] - bottom_group['average_score']
                
                group_analysis['insights'].append({
                    'type': 'group_performance_gap',
                    'insight': f"Score gap between highest ({top_group['group']}) and lowest ({bottom_group['group']}) performing groups is {score_gap:.1f} points",
                    'significance': 'high' if score_gap > 5 else 'medium'
                })
                
                # Identify specialized groups
                specialized_groups = [
                    group for group, pattern in group_analysis['activity_patterns'].items()
                    if len(pattern['specializations']) == 1
                ]
                
                if specialized_groups:
                    group_analysis['insights'].append({
                        'type': 'specialization_pattern',
                        'insight': f"Groups with clear specialization: {', '.join(specialized_groups)}",
                        'significance': 'medium'
                    })
            
            conn.close()
            
            return TaskResult(
                success=True,
                message=f"Political group pattern analysis completed for {len(group_data)} groups in term {term}",
                data=group_analysis
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Political group pattern analysis failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def _detect_activity_anomalies(self, task_data: Dict[str, Any]) -> TaskResult:
        """Detect unusual patterns or anomalies in MEP activities"""
        try:
            term = task_data.get('term', 10)
            threshold = task_data.get('threshold', self.analytics_config['insight_thresholds']['outlier_threshold'])
            
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            anomaly_analysis = {
                'analysis_timestamp': datetime.now().isoformat(),
                'term': term,
                'outlier_threshold': threshold,
                'anomalies': [],
                'summary': {},
                'recommendations': []
            }
            
            # Define activities to check for anomalies
            activities = ['speeches', 'amendments', 'questions_written', 'total_score']
            
            for activity in activities:
                cursor.execute(f"""
                    SELECT name, {activity}, group_name, country
                    FROM meps 
                    WHERE term = ? AND {activity} IS NOT NULL
                """, (term,))
                
                data = cursor.fetchall()
                if not data:
                    continue
                
                values = [row[1] for row in data if row[1] is not None]
                
                if len(values) < 10:  # Need sufficient data for anomaly detection
                    continue
                
                mean_val = statistics.mean(values)
                std_val = statistics.stdev(values) if len(values) > 1 else 0
                
                if std_val == 0:
                    continue
                
                # Identify outliers
                outliers = []
                for row in data:
                    name, value, group, country = row
                    if value is None:
                        continue
                    
                    z_score = abs(value - mean_val) / std_val
                    
                    if z_score > threshold:
                        outlier_type = 'extreme_high' if value > mean_val else 'extreme_low'
                        
                        outliers.append({
                            'mep_name': name,
                            'activity': activity,
                            'value': value,
                            'z_score': z_score,
                            'outlier_type': outlier_type,
                            'group': group,
                            'country': country,
                            'deviation_from_mean': value - mean_val
                        })
                
                if outliers:
                    anomaly_analysis['anomalies'].extend(outliers)
                    
                    # Summary statistics
                    anomaly_analysis['summary'][activity] = {
                        'mean': mean_val,
                        'std_dev': std_val,
                        'outliers_count': len(outliers),
                        'extreme_high_count': len([o for o in outliers if o['outlier_type'] == 'extreme_high']),
                        'extreme_low_count': len([o for o in outliers if o['outlier_type'] == 'extreme_low'])
                    }
            
            # Group anomalies by MEP to identify multi-category outliers
            mep_anomaly_counts = Counter(anomaly['mep_name'] for anomaly in anomaly_analysis['anomalies'])
            multi_category_outliers = [mep for mep, count in mep_anomaly_counts.items() if count > 1]
            
            # Generate recommendations
            if multi_category_outliers:
                anomaly_analysis['recommendations'].append({
                    'type': 'data_validation',
                    'recommendation': f"Review data quality for MEPs with multiple anomalies: {', '.join(multi_category_outliers[:3])}{'...' if len(multi_category_outliers) > 3 else ''}",
                    'priority': 'high'
                })
            
            # Check for systematic anomalies by group or country
            group_anomaly_counts = Counter(
                anomaly['group'] for anomaly in anomaly_analysis['anomalies'] 
                if anomaly['group']
            )
            
            if group_anomaly_counts:
                top_anomaly_group = group_anomaly_counts.most_common(1)[0]
                if top_anomaly_group[1] > 3:  # Group with many anomalies
                    anomaly_analysis['recommendations'].append({
                        'type': 'systematic_review',
                        'recommendation': f"Investigate systematic issues in group {top_anomaly_group[0]} (has {top_anomaly_group[1]} anomalies)",
                        'priority': 'medium'
                    })
            
            # Statistical patterns
            total_anomalies = len(anomaly_analysis['anomalies'])
            if total_anomalies > 0:
                cursor.execute("SELECT COUNT(*) FROM meps WHERE term = ?", (term,))
                total_meps = cursor.fetchone()[0]
                
                anomaly_rate = total_anomalies / total_meps if total_meps > 0 else 0
                
                anomaly_analysis['overall_statistics'] = {
                    'total_meps': total_meps,
                    'total_anomalies': total_anomalies,
                    'anomaly_rate': anomaly_rate,
                    'multi_category_outliers': len(multi_category_outliers)
                }
                
                if anomaly_rate > 0.1:  # More than 10% anomalies
                    anomaly_analysis['recommendations'].append({
                        'type': 'methodology_review',
                        'recommendation': f"High anomaly rate ({anomaly_rate:.1%}) suggests possible methodology or data issues",
                        'priority': 'high'
                    })
            
            conn.close()
            
            return TaskResult(
                success=True,
                message=f"Anomaly detection completed. Found {len(anomaly_analysis['anomalies'])} anomalies",
                data=anomaly_analysis
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Activity anomaly detection failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def _generate_performance_insights(self, task_data: Dict[str, Any]) -> TaskResult:
        """Generate insights about application performance and usage"""
        try:
            # Simulate performance metrics analysis (in production, this would use real metrics)
            performance_insights = {
                'analysis_timestamp': datetime.now().isoformat(),
                'performance_metrics': {},
                'insights': [],
                'recommendations': []
            }
            
            # Check database performance
            db_size = self.database_path.stat().st_size if self.database_path.exists() else 0
            
            performance_insights['performance_metrics']['database'] = {
                'size_mb': round(db_size / (1024 * 1024), 2),
                'status': 'healthy' if db_size > 0 else 'missing'
            }
            
            # Check dataset file sizes
            datasets_dir = self.project_root / 'public' / 'data'
            if datasets_dir.exists():
                dataset_sizes = {}
                total_dataset_size = 0
                
                for dataset_file in datasets_dir.glob('term*_dataset.json'):
                    size = dataset_file.stat().st_size
                    dataset_sizes[dataset_file.name] = round(size / (1024 * 1024), 2)
                    total_dataset_size += size
                
                performance_insights['performance_metrics']['datasets'] = {
                    'individual_sizes_mb': dataset_sizes,
                    'total_size_mb': round(total_dataset_size / (1024 * 1024), 2),
                    'count': len(dataset_sizes)
                }
                
                # Generate performance insights
                largest_dataset = max(dataset_sizes.values()) if dataset_sizes else 0
                
                if largest_dataset > 10:  # MB
                    performance_insights['insights'].append({
                        'type': 'performance_concern',
                        'insight': f"Largest dataset is {largest_dataset:.1f}MB, may cause slow loading",
                        'category': 'frontend_performance'
                    })
                    
                    performance_insights['recommendations'].append({
                        'type': 'optimization',
                        'recommendation': 'Consider implementing dataset pagination or lazy loading',
                        'priority': 'medium'
                    })
            
            # Analyze code complexity (simplified)
            code_metrics = await self._analyze_code_complexity()
            if code_metrics:
                performance_insights['performance_metrics']['code_complexity'] = code_metrics
                
                if code_metrics.get('large_files_count', 0) > 5:
                    performance_insights['recommendations'].append({
                        'type': 'code_optimization',
                        'recommendation': 'Consider refactoring large files for better maintainability',
                        'priority': 'low'
                    })
            
            # System resource usage simulation
            performance_insights['performance_metrics']['system'] = {
                'estimated_memory_usage_mb': round((db_size + total_dataset_size) / (1024 * 1024) * 1.5, 2),
                'disk_usage_mb': round((db_size + total_dataset_size) / (1024 * 1024), 2)
            }
            
            return TaskResult(
                success=True,
                message=f"Performance insights generated with {len(performance_insights['insights'])} insights",
                data=performance_insights
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Performance insights generation failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def _analyze_code_complexity(self) -> Dict[str, Any]:
        """Analyze code complexity metrics"""
        try:
            complexity_metrics = {
                'total_files': 0,
                'total_lines': 0,
                'large_files_count': 0,
                'average_file_size': 0
            }
            
            # Analyze Python files
            python_files = list(self.project_root.rglob('*.py'))
            file_sizes = []
            
            for py_file in python_files:
                if py_file.name.startswith('__'):
                    continue
                
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        lines = len(f.readlines())
                    
                    file_sizes.append(lines)
                    complexity_metrics['total_lines'] += lines
                    
                    if lines > 500:  # Consider large files
                        complexity_metrics['large_files_count'] += 1
                
                except Exception as e:
                    self.logger.warning(f"Could not analyze {py_file}: {str(e)}")
            
            complexity_metrics['total_files'] = len(file_sizes)
            if file_sizes:
                complexity_metrics['average_file_size'] = round(sum(file_sizes) / len(file_sizes), 1)
            
            return complexity_metrics
            
        except Exception as e:
            self.logger.warning(f"Code complexity analysis failed: {str(e)}")
            return {}
    
    async def _create_insights_dashboard(self, task_data: Dict[str, Any]) -> TaskResult:
        """Create comprehensive analytics dashboard"""
        try:
            # Generate comprehensive dashboard by combining multiple analyses
            dashboard_data = {
                'dashboard_timestamp': datetime.now().isoformat(),
                'summary_metrics': {},
                'trend_analysis': None,
                'group_analysis': None,
                'anomalies': None,
                'performance_insights': None,
                'key_insights': [],
                'action_items': []
            }
            
            # Get trend analysis
            trend_result = await self._analyze_mep_activity_trends(task_data)
            if trend_result.success:
                dashboard_data['trend_analysis'] = trend_result.data
                dashboard_data['key_insights'].extend(trend_result.data.get('insights', []))
            
            # Get group analysis
            group_result = await self._analyze_political_group_patterns(task_data)
            if group_result.success:
                dashboard_data['group_analysis'] = group_result.data
                dashboard_data['key_insights'].extend(group_result.data.get('insights', []))
            
            # Get anomaly analysis
            anomaly_result = await self._detect_activity_anomalies(task_data)
            if anomaly_result.success:
                dashboard_data['anomalies'] = anomaly_result.data
                dashboard_data['action_items'].extend(anomaly_result.data.get('recommendations', []))
            
            # Get performance insights
            performance_result = await self._generate_performance_insights(task_data)
            if performance_result.success:
                dashboard_data['performance_insights'] = performance_result.data
                dashboard_data['action_items'].extend(performance_result.data.get('recommendations', []))
            
            # Generate summary metrics
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # Overall statistics
            cursor.execute("SELECT COUNT(DISTINCT term) FROM meps")
            terms_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM meps WHERE total_score > 0")
            active_meps_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT AVG(total_score) FROM meps WHERE total_score > 0")
            avg_score = cursor.fetchone()[0]
            
            dashboard_data['summary_metrics'] = {
                'total_terms': terms_count,
                'active_meps': active_meps_count,
                'average_score': round(float(avg_score), 2) if avg_score else 0,
                'last_updated': datetime.now().isoformat()
            }
            
            conn.close()
            
            # Generate dashboard HTML
            dashboard_html = self._generate_dashboard_html(dashboard_data)
            
            # Save dashboard
            dashboard_path = self.project_root / 'reports' / 'analytics_dashboard.html'
            dashboard_path.parent.mkdir(exist_ok=True)
            
            with open(dashboard_path, 'w', encoding='utf-8') as f:
                f.write(dashboard_html)
            
            return TaskResult(
                success=True,
                message=f"Analytics dashboard created with {len(dashboard_data['key_insights'])} insights",
                data={
                    'dashboard_path': str(dashboard_path),
                    'dashboard_data': dashboard_data
                }
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Insights dashboard creation failed: {str(e)}",
                errors=[str(e)]
            )
    
    def _generate_dashboard_html(self, dashboard_data: Dict[str, Any]) -> str:
        """Generate HTML for analytics dashboard"""
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MEP Ranking Analytics Dashboard</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .metric-card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .metric-value {{ font-size: 2em; font-weight: bold; color: #2563eb; }}
        .metric-label {{ color: #6b7280; margin-top: 5px; }}
        .insights-section {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }}
        .insight-item {{ padding: 10px; margin: 10px 0; border-left: 4px solid #2563eb; background: #f8fafc; }}
        .action-item {{ padding: 10px; margin: 10px 0; border-left: 4px solid #dc2626; background: #fef2f2; }}
        .priority-high {{ border-left-color: #dc2626; }}
        .priority-medium {{ border-left-color: #d97706; }}
        .priority-low {{ border-left-color: #059669; }}
        .section-title {{ font-size: 1.5em; font-weight: bold; margin-bottom: 15px; color: #374151; }}
        .timestamp {{ color: #6b7280; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>MEP Ranking Analytics Dashboard</h1>
            <p class="timestamp">Generated on: {dashboard_data['dashboard_timestamp']}</p>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value">{dashboard_data['summary_metrics'].get('total_terms', 0)}</div>
                <div class="metric-label">Parliamentary Terms</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{dashboard_data['summary_metrics'].get('active_meps', 0)}</div>
                <div class="metric-label">Active MEPs</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{dashboard_data['summary_metrics'].get('average_score', 0)}</div>
                <div class="metric-label">Average Activity Score</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{len(dashboard_data['key_insights'])}</div>
                <div class="metric-label">Key Insights</div>
            </div>
        </div>
        
        <div class="insights-section">
            <h2 class="section-title">Key Insights</h2>
"""
        
        for insight in dashboard_data['key_insights']:
            html += f"""
            <div class="insight-item">
                <strong>{insight.get('type', '').replace('_', ' ').title()}:</strong> 
                {insight.get('insight', '')}
            </div>
"""
        
        html += """
        </div>
        
        <div class="insights-section">
            <h2 class="section-title">Action Items</h2>
"""
        
        for action in dashboard_data['action_items']:
            priority_class = f"priority-{action.get('priority', 'medium')}"
            html += f"""
            <div class="action-item {priority_class}">
                <strong>[{action.get('priority', 'medium').upper()}]</strong> 
                {action.get('recommendation', '')}
            </div>
"""
        
        html += f"""
        </div>
        
        <div class="insights-section">
            <h2 class="section-title">System Information</h2>
            <p><strong>Last Analysis:</strong> {dashboard_data['dashboard_timestamp']}</p>
            <p><strong>Data Source:</strong> ParlTrack European Parliament Database</p>
            <p><strong>Dashboard Generated By:</strong> Analytics & Insights Agent</p>
        </div>
    </div>
</body>
</html>
"""
        
        return html
    
    async def _analyze_scoring_distribution(self, task_data: Dict[str, Any]) -> TaskResult:
        """Analyze MEP score distributions and patterns"""
        try:
            # This would be similar to the scoring system agent's distribution analysis
            # but focused on analytics insights
            term = task_data.get('term', 10)
            
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT total_score, group_name, country 
                FROM meps 
                WHERE term = ? AND total_score > 0
            """, (term,))
            
            data = cursor.fetchall()
            conn.close()
            
            if not data:
                return TaskResult(
                    success=False,
                    message=f"No scoring data found for term {term}",
                    errors=["Insufficient data for analysis"]
                )
            
            scores = [row[0] for row in data]
            
            distribution_analysis = {
                'term': term,
                'total_meps': len(scores),
                'distribution_stats': {
                    'mean': statistics.mean(scores),
                    'median': statistics.median(scores),
                    'std_dev': statistics.stdev(scores) if len(scores) > 1 else 0,
                    'min_score': min(scores),
                    'max_score': max(scores)
                },
                'insights': []
            }
            
            # Add percentile analysis
            if len(scores) >= 4:
                quartiles = statistics.quantiles(scores, n=4)
                distribution_analysis['distribution_stats']['quartiles'] = quartiles
                
                # Identify scoring patterns
                q1, q2, q3 = quartiles
                iqr = q3 - q1
                
                if iqr > distribution_analysis['distribution_stats']['mean'] * 0.5:
                    distribution_analysis['insights'].append({
                        'type': 'score_variance',
                        'insight': f"High score variance detected (IQR: {iqr:.1f})",
                        'recommendation': 'Review scoring methodology for consistency'
                    })
            
            return TaskResult(
                success=True,
                message=f"Score distribution analysis completed for {len(scores)} MEPs",
                data=distribution_analysis
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Score distribution analysis failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def _generate_comparative_analysis(self, task_data: Dict[str, Any]) -> TaskResult:
        """Generate comparative analysis across terms, groups, and countries"""
        try:
            # Comprehensive comparative analysis
            comparative_analysis = {
                'analysis_timestamp': datetime.now().isoformat(),
                'comparisons': {},
                'insights': []
            }
            
            # Cross-term comparison
            terms_comparison = await self._analyze_mep_activity_trends(task_data)
            if terms_comparison.success:
                comparative_analysis['comparisons']['cross_term'] = terms_comparison.data
            
            # Cross-group comparison
            group_comparison = await self._analyze_political_group_patterns(task_data)
            if group_comparison.success:
                comparative_analysis['comparisons']['cross_group'] = group_comparison.data
            
            # Generate comparative insights
            if terms_comparison.success and group_comparison.success:
                comparative_analysis['insights'].append({
                    'type': 'comprehensive_analysis',
                    'insight': 'Comparative analysis completed across terms and political groups',
                    'details': 'Multiple dimensions of MEP activity analyzed for patterns and trends'
                })
            
            return TaskResult(
                success=True,
                message="Comparative analysis completed across multiple dimensions",
                data=comparative_analysis
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Comparative analysis failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def _generate_usage_analytics(self, task_data: Dict[str, Any]) -> TaskResult:
        """Analyze application usage patterns and user behavior"""
        try:
            # Simulated usage analytics (in production, would use real analytics data)
            usage_analytics = {
                'analysis_timestamp': datetime.now().isoformat(),
                'usage_patterns': {
                    'most_accessed_features': [
                        {'feature': 'Activity Explorer', 'usage_score': 95},
                        {'feature': 'MEP Profiles', 'usage_score': 80},
                        {'feature': 'Custom Rankings', 'usage_score': 45}
                    ],
                    'popular_search_terms': [
                        'amendments', 'speeches', 'voting attendance'
                    ],
                    'common_filters': [
                        'political group', 'country', 'activity level'
                    ]
                },
                'insights': [
                    {
                        'type': 'feature_usage',
                        'insight': 'Activity Explorer is the most used feature (95% usage)',
                        'recommendation': 'Continue investing in grid functionality improvements'
                    },
                    {
                        'type': 'engagement_pattern',
                        'insight': 'Custom Rankings has lower usage (45%)',
                        'recommendation': 'Consider UX improvements or better feature promotion'
                    }
                ]
            }
            
            return TaskResult(
                success=True,
                message="Usage analytics generated (simulated data)",
                data=usage_analytics
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Usage analytics generation failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def _predict_activity_trends(self, task_data: Dict[str, Any]) -> TaskResult:
        """Predict future activity trends based on historical data"""
        try:
            # Simplified trend prediction (in production, would use proper ML models)
            trend_analysis = await self._analyze_mep_activity_trends(task_data)
            
            if not trend_analysis.success:
                return trend_analysis
            
            predictions = {
                'prediction_timestamp': datetime.now().isoformat(),
                'methodology': 'Linear trend extrapolation (simplified)',
                'predictions': {},
                'confidence_levels': {},
                'insights': []
            }
            
            # Generate simple predictions based on trend analysis
            cross_term_data = trend_analysis.data.get('cross_term_comparison', {})
            
            for activity, trend_info in cross_term_data.items():
                direction = trend_info['direction']
                magnitude = trend_info['magnitude']
                
                # Simple prediction: continue trend with decreasing confidence
                predicted_change = magnitude * 0.5  # Conservative prediction
                confidence = 0.7 if trend_info['significance'] == 'significant' else 0.4
                
                predictions['predictions'][activity] = {
                    'predicted_direction': direction,
                    'predicted_magnitude': predicted_change,
                    'prediction_type': 'trend_continuation'
                }
                
                predictions['confidence_levels'][activity] = confidence
                
                if confidence > 0.6:
                    predictions['insights'].append({
                        'type': 'trend_prediction',
                        'insight': f"{activity.replace('_', ' ').title()} likely to continue {direction} trend",
                        'confidence': confidence
                    })
            
            return TaskResult(
                success=True,
                message=f"Activity trend predictions generated for {len(predictions['predictions'])} activities",
                data=predictions
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Activity trend prediction failed: {str(e)}",
                errors=[str(e)]
            )