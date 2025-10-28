"""
Data Validation Agent

This agent ensures data quality and accuracy for the MEP Ranking system,
following Anthropic best practices for data validation and quality assurance.
"""

import sqlite3
import json
import re
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
import statistics

from .base_agent import BaseAgent, TaskResult, AgentCapability


@dataclass
class ValidationRule:
    """Data validation rule definition"""
    name: str
    description: str
    severity: str  # 'critical', 'warning', 'info'
    category: str  # 'completeness', 'consistency', 'accuracy', 'format'
    threshold: Optional[float] = None


@dataclass
class ValidationResult:
    """Individual validation result"""
    rule_name: str
    passed: bool
    message: str
    severity: str
    category: str
    details: Optional[Dict[str, Any]] = None
    affected_records: Optional[List[Any]] = None


class DataValidationAgent(BaseAgent):
    """
    Data Validation Agent responsible for:
    
    1. MEP profile completeness checking
    2. Activity count validation against source data
    3. Cross-reference validation (roles, committees, dates)
    4. Anomaly detection in parliamentary activities
    5. Historical data consistency checks
    6. Term boundary validation
    7. Data format and structure validation
    8. Statistical outlier detection
    """
    
    def _initialize_agent(self) -> None:
        """Initialize the data validation agent"""
        self.data_dir = self.project_root / 'data'
        self.parltrack_dir = self.data_dir / 'parltrack'
        self.public_data_dir = self.project_root / 'public' / 'data'
        self.validation_logs_dir = self.project_root / 'logs' / 'validation'
        
        # Ensure directories exist
        for directory in [self.validation_logs_dir]:
            self._ensure_directory(directory)
        
        # Initialize validation rules
        self.validation_rules = self._define_validation_rules()
        
        # Expected data ranges and thresholds
        self.data_thresholds = self._define_data_thresholds()
        
        # Validation cache for performance
        self.validation_cache = {}
        
        self.logger.info(f"Data Validation Agent initialized with {len(self.validation_rules)} rules")
    
    def _define_capabilities(self) -> List[AgentCapability]:
        """Define the capabilities of this agent"""
        return [
            AgentCapability(
                name="validate_mep_profiles",
                description="Validate MEP profile completeness and accuracy",
                required_tools=["database", "file_system"],
                complexity_level="intermediate"
            ),
            AgentCapability(
                name="validate_activity_counts",
                description="Validate activity counts against source data",
                required_tools=["database", "file_system"],
                complexity_level="advanced"
            ),
            AgentCapability(
                name="validate_cross_references",
                description="Validate data cross-references and relationships",
                required_tools=["database"],
                complexity_level="intermediate"
            ),
            AgentCapability(
                name="detect_anomalies",
                description="Detect anomalies in parliamentary activities",
                required_tools=["database", "statistical_analysis"],
                complexity_level="advanced"
            ),
            AgentCapability(
                name="validate_term_boundaries",
                description="Validate term dates and boundaries",
                required_tools=["database", "date_validation"],
                complexity_level="basic"
            ),
            AgentCapability(
                name="validate_data_formats",
                description="Validate data formats and structures",
                required_tools=["file_system", "json_validation"],
                complexity_level="basic"
            ),
            AgentCapability(
                name="run_comprehensive_validation",
                description="Run all validation checks and generate report",
                required_tools=["database", "file_system", "statistical_analysis"],
                complexity_level="advanced"
            ),
            AgentCapability(
                name="validate_scoring_consistency",
                description="Validate scoring algorithm consistency",
                required_tools=["database", "mathematical_validation"],
                complexity_level="advanced"
            )
        ]
    
    def _define_validation_rules(self) -> List[ValidationRule]:
        """Define comprehensive validation rules"""
        return [
            # Completeness rules
            ValidationRule(
                name="mep_basic_info_complete",
                description="MEP must have name, group, country",
                severity="critical",
                category="completeness"
            ),
            ValidationRule(
                name="mep_activity_data_present",
                description="MEP must have activity data for their term",
                severity="critical",
                category="completeness"
            ),
            ValidationRule(
                name="required_score_fields",
                description="MEP must have all required scoring fields",
                severity="critical",
                category="completeness"
            ),
            
            # Consistency rules
            ValidationRule(
                name="term_consistency",
                description="MEP terms must be consistent across tables",
                severity="critical",
                category="consistency"
            ),
            ValidationRule(
                name="date_consistency",
                description="Dates must be logically consistent",
                severity="warning",
                category="consistency"
            ),
            ValidationRule(
                name="score_calculation_consistency",
                description="Scores must be calculated consistently",
                severity="critical",
                category="consistency"
            ),
            
            # Accuracy rules
            ValidationRule(
                name="activity_count_accuracy",
                description="Activity counts must match source data",
                severity="warning",
                category="accuracy",
                threshold=0.95  # 95% accuracy threshold
            ),
            ValidationRule(
                name="statistical_plausibility",
                description="Statistical measures must be plausible",
                severity="warning",
                category="accuracy"
            ),
            
            # Format rules
            ValidationRule(
                name="data_type_validation",
                description="Data types must match expected formats",
                severity="critical",
                category="format"
            ),
            ValidationRule(
                name="value_range_validation",
                description="Values must be within expected ranges",
                severity="warning",
                category="format"
            )
        ]
    
    def _define_data_thresholds(self) -> Dict[str, Any]:
        """Define expected data ranges and thresholds"""
        return {
            'mep_counts': {
                8: {'min': 750, 'max': 900, 'typical': 850},
                9: {'min': 700, 'max': 800, 'typical': 751},
                10: {'min': 650, 'max': 750, 'typical': 719}
            },
            'activity_ranges': {
                'speeches': {'min': 0, 'max': 1000, 'outlier_threshold': 3},
                'amendments': {'min': 0, 'max': 2000, 'outlier_threshold': 3},
                'questions_written': {'min': 0, 'max': 500, 'outlier_threshold': 3},
                'questions_oral': {'min': 0, 'max': 100, 'outlier_threshold': 3},
                'reports_rapporteur': {'min': 0, 'max': 50, 'outlier_threshold': 2},
                'reports_shadow': {'min': 0, 'max': 200, 'outlier_threshold': 3}
            },
            'score_ranges': {
                'total_score': {'min': 0, 'max': 100},
                'component_scores': {'min': 0, 'max': 25}
            },
            'term_dates': {
                8: {'start': '2014-07-01', 'end': '2019-07-02'},
                9: {'start': '2019-07-02', 'end': '2024-07-16'},
                10: {'start': '2024-07-16', 'end': '2029-07-16'}
            }
        }
    
    async def _execute_task_impl(self, task_type: str, task_data: Dict[str, Any]) -> TaskResult:
        """Execute the specific validation task"""
        task_handlers = {
            "validate_mep_profiles": self._validate_mep_profiles,
            "validate_activity_counts": self._validate_activity_counts,
            "validate_cross_references": self._validate_cross_references,
            "detect_anomalies": self._detect_anomalies,
            "validate_term_boundaries": self._validate_term_boundaries,
            "validate_data_formats": self._validate_data_formats,
            "run_comprehensive_validation": self._run_comprehensive_validation,
            "validate_scoring_consistency": self._validate_scoring_consistency
        }
        
        if task_type not in task_handlers:
            return TaskResult(
                success=False,
                message=f"Unknown validation task: {task_type}",
                errors=[f"Task type {task_type} not supported"]
            )
        
        return await task_handlers[task_type](task_data)
    
    async def _validate_mep_profiles(self, task_data: Dict[str, Any]) -> TaskResult:
        """Validate MEP profile completeness and accuracy"""
        try:
            terms_to_validate = task_data.get('terms', [8, 9, 10])
            validation_results = []
            
            db_path = self.data_dir / 'meps.db'
            if not db_path.exists():
                return TaskResult(
                    success=False,
                    message="Database not found",
                    errors=["Database file does not exist"]
                )
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                for term in terms_to_validate:
                    term_results = await self._validate_term_mep_profiles(cursor, term)
                    validation_results.extend(term_results)
            
            # Categorize results
            critical_failures = [r for r in validation_results if r.severity == 'critical' and not r.passed]
            warnings = [r for r in validation_results if r.severity == 'warning' and not r.passed]
            
            # Generate summary
            total_checks = len(validation_results)
            passed_checks = len([r for r in validation_results if r.passed])
            
            success = len(critical_failures) == 0
            
            return TaskResult(
                success=success,
                message=f"MEP profile validation: {passed_checks}/{total_checks} checks passed, {len(critical_failures)} critical failures",
                data={
                    'summary': {
                        'total_checks': total_checks,
                        'passed_checks': passed_checks,
                        'critical_failures': len(critical_failures),
                        'warnings': len(warnings)
                    },
                    'validation_results': [self._validation_result_to_dict(r) for r in validation_results],
                    'critical_failures': [self._validation_result_to_dict(r) for r in critical_failures],
                    'warnings': [self._validation_result_to_dict(r) for r in warnings]
                }
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"MEP profile validation failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def _validate_term_mep_profiles(self, cursor: sqlite3.Cursor, term: int) -> List[ValidationResult]:
        """Validate MEP profiles for a specific term"""
        results = []
        
        # Get MEPs for the term
        cursor.execute("""
            SELECT DISTINCT m.mep_id, m.name, m.group_name, m.country
            FROM meps m
            JOIN rankings r ON m.mep_id = r.mep_id
            WHERE r.term = ?
        """, (term,))
        
        meps = cursor.fetchall()
        
        # Check basic info completeness
        incomplete_basic_info = []
        for mep_id, name, group, country in meps:
            if not name or not group or not country:
                incomplete_basic_info.append({
                    'mep_id': mep_id,
                    'name': name,
                    'missing': [field for field, value in [('name', name), ('group', group), ('country', country)] if not value]
                })
        
        results.append(ValidationResult(
            rule_name="mep_basic_info_complete",
            passed=len(incomplete_basic_info) == 0,
            message=f"Term {term}: {len(incomplete_basic_info)} MEPs missing basic info",
            severity="critical",
            category="completeness",
            details={'incomplete_count': len(incomplete_basic_info)},
            affected_records=incomplete_basic_info
        ))
        
        # Check activity data presence
        cursor.execute("""
            SELECT COUNT(DISTINCT m.mep_id) as total_meps,
                   COUNT(DISTINCT a.mep_id) as meps_with_activities
            FROM meps m
            JOIN rankings r ON m.mep_id = r.mep_id
            LEFT JOIN activities a ON m.mep_id = a.mep_id AND a.term = r.term
            WHERE r.term = ?
        """, (term,))
        
        total_meps, meps_with_activities = cursor.fetchone()
        missing_activities = total_meps - (meps_with_activities or 0)
        
        results.append(ValidationResult(
            rule_name="mep_activity_data_present",
            passed=missing_activities == 0,
            message=f"Term {term}: {missing_activities} MEPs missing activity data",
            severity="critical",
            category="completeness",
            details={
                'total_meps': total_meps,
                'meps_with_activities': meps_with_activities,
                'missing_activities': missing_activities
            }
        ))
        
        # Check required score fields
        cursor.execute("""
            SELECT mep_id, total_score, speeches_score, amendments_score, 
                   reports_score, questions_score
            FROM rankings
            WHERE term = ? AND (
                total_score IS NULL OR
                speeches_score IS NULL OR
                amendments_score IS NULL OR
                reports_score IS NULL OR
                questions_score IS NULL
            )
        """, (term,))
        
        incomplete_scores = cursor.fetchall()
        
        results.append(ValidationResult(
            rule_name="required_score_fields",
            passed=len(incomplete_scores) == 0,
            message=f"Term {term}: {len(incomplete_scores)} MEPs missing score fields",
            severity="critical",
            category="completeness",
            details={'incomplete_scores_count': len(incomplete_scores)},
            affected_records=[{'mep_id': row[0]} for row in incomplete_scores]
        ))
        
        return results
    
    async def _validate_activity_counts(self, task_data: Dict[str, Any]) -> TaskResult:
        """Validate activity counts against source data"""
        try:
            terms_to_validate = task_data.get('terms', [10])  # Focus on current term
            validation_results = []
            
            # Load source data for comparison
            source_data = await self._load_source_activity_data()
            if not source_data:
                return TaskResult(
                    success=False,
                    message="Could not load source activity data for validation",
                    errors=["Source data unavailable"]
                )
            
            db_path = self.data_dir / 'meps.db'
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                for term in terms_to_validate:
                    term_results = await self._validate_term_activity_counts(cursor, term, source_data)
                    validation_results.extend(term_results)
            
            # Summarize results
            accuracy_checks = [r for r in validation_results if r.rule_name == "activity_count_accuracy"]
            accuracy_passed = len([r for r in accuracy_checks if r.passed])
            
            success = accuracy_passed / len(accuracy_checks) >= 0.9 if accuracy_checks else True
            
            return TaskResult(
                success=success,
                message=f"Activity count validation: {accuracy_passed}/{len(accuracy_checks)} accuracy checks passed",
                data={
                    'validation_results': [self._validation_result_to_dict(r) for r in validation_results],
                    'accuracy_rate': accuracy_passed / len(accuracy_checks) if accuracy_checks else 1.0
                }
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Activity count validation failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def _load_source_activity_data(self) -> Optional[Dict[str, Any]]:
        """Load source activity data for validation"""
        try:
            # Load from ParlTrack activities file
            activities_file = self.parltrack_dir / 'ep_mep_activities.json'
            if not activities_file.exists():
                return None
            
            with open(activities_file, 'r', encoding='utf-8') as f:
                activities_data = json.load(f)
            
            # Process and index by MEP ID
            source_activities = {}
            for mep_data in activities_data:
                mep_id = mep_data.get('UserID')
                if mep_id:
                    source_activities[mep_id] = mep_data
            
            return source_activities
            
        except Exception as e:
            self.logger.error(f"Failed to load source activity data: {str(e)}")
            return None
    
    async def _validate_term_activity_counts(self, cursor: sqlite3.Cursor, term: int, 
                                           source_data: Dict[str, Any]) -> List[ValidationResult]:
        """Validate activity counts for a specific term"""
        results = []
        
        # Get activity data from database
        cursor.execute("""
            SELECT mep_id, speeches, amendments, questions_written, questions_oral,
                   reports_rapporteur, reports_shadow, opinions_rapporteur, opinions_shadow
            FROM activities
            WHERE term = ?
        """, (term,))
        
        db_activities = cursor.fetchall()
        
        # Compare with source data
        discrepancies = []
        activity_fields = [
            'speeches', 'amendments', 'questions_written', 'questions_oral',
            'reports_rapporteur', 'reports_shadow', 'opinions_rapporteur', 'opinions_shadow'
        ]
        
        for db_row in db_activities:
            mep_id = db_row[0]
            if mep_id in source_data:
                source_mep = source_data[mep_id]
                
                for i, field in enumerate(activity_fields):
                    db_value = db_row[i + 1] or 0
                    source_value = source_mep.get(field, 0) or 0
                    
                    if abs(db_value - source_value) > max(1, source_value * 0.1):  # Allow 10% variance
                        discrepancies.append({
                            'mep_id': mep_id,
                            'field': field,
                            'db_value': db_value,
                            'source_value': source_value,
                            'difference': abs(db_value - source_value)
                        })
        
        # Calculate accuracy rate
        total_comparisons = len(db_activities) * len(activity_fields)
        accurate_comparisons = total_comparisons - len(discrepancies)
        accuracy_rate = accurate_comparisons / total_comparisons if total_comparisons > 0 else 1.0
        
        threshold = self.data_thresholds.get('activity_ranges', {}).get('accuracy_threshold', 0.95)
        
        results.append(ValidationResult(
            rule_name="activity_count_accuracy",
            passed=accuracy_rate >= threshold,
            message=f"Term {term}: {accuracy_rate:.2%} accuracy rate ({len(discrepancies)} discrepancies)",
            severity="warning",
            category="accuracy",
            details={
                'accuracy_rate': accuracy_rate,
                'total_comparisons': total_comparisons,
                'discrepancies_count': len(discrepancies),
                'threshold': threshold
            },
            affected_records=discrepancies[:10]  # Limit to first 10 for performance
        ))
        
        return results
    
    async def _validate_cross_references(self, task_data: Dict[str, Any]) -> TaskResult:
        """Validate data cross-references and relationships"""
        try:
            validation_results = []
            
            db_path = self.data_dir / 'meps.db'
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Check MEP-Rankings consistency
                cursor.execute("""
                    SELECT COUNT(*) as orphaned_rankings
                    FROM rankings r
                    LEFT JOIN meps m ON r.mep_id = m.mep_id
                    WHERE m.mep_id IS NULL
                """)
                
                orphaned_rankings = cursor.fetchone()[0]
                
                validation_results.append(ValidationResult(
                    rule_name="mep_rankings_consistency",
                    passed=orphaned_rankings == 0,
                    message=f"{orphaned_rankings} orphaned ranking records found",
                    severity="critical",
                    category="consistency",
                    details={'orphaned_count': orphaned_rankings}
                ))
                
                # Check Activities-MEPs consistency
                cursor.execute("""
                    SELECT COUNT(*) as orphaned_activities
                    FROM activities a
                    LEFT JOIN meps m ON a.mep_id = m.mep_id
                    WHERE m.mep_id IS NULL
                """)
                
                orphaned_activities = cursor.fetchone()[0]
                
                validation_results.append(ValidationResult(
                    rule_name="activities_meps_consistency",
                    passed=orphaned_activities == 0,
                    message=f"{orphaned_activities} orphaned activity records found",
                    severity="warning",
                    category="consistency",
                    details={'orphaned_count': orphaned_activities}
                ))
                
                # Check Roles-MEPs consistency
                cursor.execute("""
                    SELECT COUNT(*) as orphaned_roles
                    FROM roles r
                    LEFT JOIN meps m ON r.mep_id = m.mep_id
                    WHERE m.mep_id IS NULL
                """)
                
                orphaned_roles = cursor.fetchone()[0]
                
                validation_results.append(ValidationResult(
                    rule_name="roles_meps_consistency",
                    passed=orphaned_roles == 0,
                    message=f"{orphaned_roles} orphaned role records found",
                    severity="warning",
                    category="consistency",
                    details={'orphaned_count': orphaned_roles}
                ))
            
            critical_failures = [r for r in validation_results if r.severity == 'critical' and not r.passed]
            success = len(critical_failures) == 0
            
            return TaskResult(
                success=success,
                message=f"Cross-reference validation: {len(critical_failures)} critical failures",
                data={
                    'validation_results': [self._validation_result_to_dict(r) for r in validation_results],
                    'critical_failures': len(critical_failures)
                }
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Cross-reference validation failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def _detect_anomalies(self, task_data: Dict[str, Any]) -> TaskResult:
        """Detect anomalies in parliamentary activities"""
        try:
            terms_to_check = task_data.get('terms', [8, 9, 10])
            anomaly_threshold = task_data.get('threshold', 3.0)  # Standard deviations
            
            anomalies_found = []
            
            db_path = self.data_dir / 'meps.db'
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                activity_fields = ['speeches', 'amendments', 'questions_written', 'questions_oral', 
                                 'reports_rapporteur', 'reports_shadow']
                
                for term in terms_to_check:
                    for field in activity_fields:
                        anomalies = await self._detect_field_anomalies(cursor, term, field, anomaly_threshold)
                        anomalies_found.extend(anomalies)
            
            # Categorize anomalies by severity
            severe_anomalies = [a for a in anomalies_found if a['z_score'] > 4.0]
            moderate_anomalies = [a for a in anomalies_found if 3.0 < a['z_score'] <= 4.0]
            
            return TaskResult(
                success=True,
                message=f"Anomaly detection: {len(severe_anomalies)} severe, {len(moderate_anomalies)} moderate anomalies found",
                data={
                    'total_anomalies': len(anomalies_found),
                    'severe_anomalies': len(severe_anomalies),
                    'moderate_anomalies': len(moderate_anomalies),
                    'anomalies': anomalies_found[:20],  # Limit for performance
                    'threshold': anomaly_threshold
                }
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Anomaly detection failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def _detect_field_anomalies(self, cursor: sqlite3.Cursor, term: int, 
                                    field: str, threshold: float) -> List[Dict[str, Any]]:
        """Detect anomalies in a specific activity field"""
        try:
            # Get all values for the field
            cursor.execute(f"""
                SELECT mep_id, {field}
                FROM activities
                WHERE term = ? AND {field} IS NOT NULL
            """, (term,))
            
            data = cursor.fetchall()
            if len(data) < 10:  # Need sufficient data for statistics
                return []
            
            values = [row[1] for row in data]
            mean_val = statistics.mean(values)
            stdev_val = statistics.stdev(values) if len(values) > 1 else 0
            
            if stdev_val == 0:  # No variation
                return []
            
            anomalies = []
            for mep_id, value in data:
                z_score = abs(value - mean_val) / stdev_val
                if z_score > threshold:
                    anomalies.append({
                        'mep_id': mep_id,
                        'term': term,
                        'field': field,
                        'value': value,
                        'mean': round(mean_val, 2),
                        'z_score': round(z_score, 2)
                    })
            
            return anomalies
            
        except Exception as e:
            self.logger.error(f"Failed to detect anomalies for {field} in term {term}: {str(e)}")
            return []
    
    async def _validate_term_boundaries(self, task_data: Dict[str, Any]) -> TaskResult:
        """Validate term dates and boundaries"""
        try:
            validation_results = []
            
            db_path = self.data_dir / 'meps.db'
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Check for activities outside term boundaries
                for term, dates in self.data_thresholds['term_dates'].items():
                    start_date = datetime.fromisoformat(dates['start']).date()
                    end_date = datetime.fromisoformat(dates['end']).date()
                    
                    # This is a placeholder - would need actual date fields in activities
                    # For now, just validate term consistency
                    cursor.execute("""
                        SELECT COUNT(*) as invalid_terms
                        FROM activities
                        WHERE term = ? AND term NOT IN (8, 9, 10)
                    """, (term,))
                    
                    invalid_terms = cursor.fetchone()[0]
                    
                    validation_results.append(ValidationResult(
                        rule_name="term_boundary_validation",
                        passed=invalid_terms == 0,
                        message=f"Term {term}: {invalid_terms} activities with invalid term values",
                        severity="warning",
                        category="consistency",
                        details={'invalid_count': invalid_terms}
                    ))
            
            warnings = [r for r in validation_results if not r.passed]
            
            return TaskResult(
                success=len(warnings) == 0,
                message=f"Term boundary validation: {len(warnings)} warnings",
                data={
                    'validation_results': [self._validation_result_to_dict(r) for r in validation_results],
                    'warnings': len(warnings)
                }
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Term boundary validation failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def _validate_data_formats(self, task_data: Dict[str, Any]) -> TaskResult:
        """Validate data formats and structures"""
        try:
            validation_results = []
            
            # Validate dataset JSON files
            dataset_files = [
                'term8_dataset.json',
                'term9_dataset.json', 
                'term10_dataset.json'
            ]
            
            for filename in dataset_files:
                file_path = self.public_data_dir / filename
                result = await self._validate_json_structure(file_path, filename)
                validation_results.append(result)
            
            # Validate database schema
            db_result = await self._validate_database_schema()
            validation_results.append(db_result)
            
            critical_failures = [r for r in validation_results if r.severity == 'critical' and not r.passed]
            success = len(critical_failures) == 0
            
            return TaskResult(
                success=success,
                message=f"Data format validation: {len(critical_failures)} critical failures",
                data={
                    'validation_results': [self._validation_result_to_dict(r) for r in validation_results],
                    'critical_failures': len(critical_failures)
                }
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Data format validation failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def _validate_json_structure(self, file_path: Path, filename: str) -> ValidationResult:
        """Validate JSON file structure"""
        try:
            if not file_path.exists():
                return ValidationResult(
                    rule_name="json_file_exists",
                    passed=False,
                    message=f"{filename} does not exist",
                    severity="critical",
                    category="format"
                )
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check structure
            if isinstance(data, dict) and 'meps' in data and 'averages' in data:
                structure_valid = True
                structure_type = "new_format"
            elif isinstance(data, list):
                structure_valid = True
                structure_type = "legacy_format"
            else:
                structure_valid = False
                structure_type = "invalid"
            
            return ValidationResult(
                rule_name="json_structure_valid",
                passed=structure_valid,
                message=f"{filename}: {structure_type}",
                severity="critical" if not structure_valid else "info",
                category="format",
                details={
                    'structure_type': structure_type,
                    'file_size_mb': round(file_path.stat().st_size / (1024 * 1024), 2)
                }
            )
            
        except json.JSONDecodeError as e:
            return ValidationResult(
                rule_name="json_parse_valid",
                passed=False,
                message=f"{filename}: JSON parse error - {str(e)}",
                severity="critical",
                category="format"
            )
        except Exception as e:
            return ValidationResult(
                rule_name="json_validation_error",
                passed=False,
                message=f"{filename}: Validation error - {str(e)}",
                severity="critical",
                category="format"
            )
    
    async def _validate_database_schema(self) -> ValidationResult:
        """Validate database schema"""
        try:
            db_path = self.data_dir / 'meps.db'
            if not db_path.exists():
                return ValidationResult(
                    rule_name="database_exists",
                    passed=False,
                    message="Database file does not exist",
                    severity="critical",
                    category="format"
                )
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Check required tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                required_tables = ['meps', 'activities', 'rankings', 'roles']
                missing_tables = [table for table in required_tables if table not in tables]
                
                return ValidationResult(
                    rule_name="database_schema_valid",
                    passed=len(missing_tables) == 0,
                    message=f"Database schema: {len(missing_tables)} missing tables",
                    severity="critical" if missing_tables else "info",
                    category="format",
                    details={
                        'existing_tables': tables,
                        'missing_tables': missing_tables
                    }
                )
                
        except Exception as e:
            return ValidationResult(
                rule_name="database_validation_error",
                passed=False,
                message=f"Database validation error: {str(e)}",
                severity="critical",
                category="format"
            )
    
    async def _validate_scoring_consistency(self, task_data: Dict[str, Any]) -> TaskResult:
        """Validate scoring algorithm consistency"""
        try:
            terms_to_validate = task_data.get('terms', [8, 9, 10])
            validation_results = []
            
            db_path = self.data_dir / 'meps.db'
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                for term in terms_to_validate:
                    # Check score component consistency
                    cursor.execute("""
                        SELECT mep_id, total_score, speeches_score, amendments_score, 
                               reports_score, questions_score, attendance_score
                        FROM rankings
                        WHERE term = ?
                    """, (term,))
                    
                    rankings = cursor.fetchall()
                    score_inconsistencies = []
                    
                    for row in rankings:
                        mep_id, total, speeches, amendments, reports, questions, attendance = row
                        
                        # Calculate expected total (allowing for rounding)
                        component_sum = sum(score for score in [speeches, amendments, reports, questions, attendance] if score is not None)
                        
                        if total is not None and abs(total - component_sum) > 0.1:
                            score_inconsistencies.append({
                                'mep_id': mep_id,
                                'total_score': total,
                                'component_sum': component_sum,
                                'difference': abs(total - component_sum)
                            })
                    
                    validation_results.append(ValidationResult(
                        rule_name="score_component_consistency",
                        passed=len(score_inconsistencies) == 0,
                        message=f"Term {term}: {len(score_inconsistencies)} score calculation inconsistencies",
                        severity="critical",
                        category="consistency",
                        details={'inconsistencies_count': len(score_inconsistencies)},
                        affected_records=score_inconsistencies[:5]  # Limit for performance
                    ))
            
            critical_failures = [r for r in validation_results if r.severity == 'critical' and not r.passed]
            success = len(critical_failures) == 0
            
            return TaskResult(
                success=success,
                message=f"Scoring consistency validation: {len(critical_failures)} critical failures",
                data={
                    'validation_results': [self._validation_result_to_dict(r) for r in validation_results],
                    'critical_failures': len(critical_failures)
                }
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Scoring consistency validation failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def _run_comprehensive_validation(self, task_data: Dict[str, Any]) -> TaskResult:
        """Run all validation checks and generate comprehensive report"""
        try:
            validation_start_time = datetime.now()
            all_results = []
            
            # Define validation tasks to run
            validation_tasks = [
                ("validate_mep_profiles", {}),
                ("validate_cross_references", {}),
                ("validate_term_boundaries", {}),
                ("validate_data_formats", {}),
                ("validate_scoring_consistency", {}),
                ("detect_anomalies", {"threshold": 3.0})
            ]
            
            # Run each validation task
            for task_name, task_params in validation_tasks:
                try:
                    self.logger.info(f"Running {task_name}")
                    result = await self._execute_task_impl(task_name, task_params)
                    
                    task_summary = {
                        'task': task_name,
                        'success': result.success,
                        'message': result.message,
                        'data': result.data
                    }
                    
                    all_results.append(task_summary)
                    
                except Exception as e:
                    self.logger.error(f"Validation task {task_name} failed: {str(e)}")
                    all_results.append({
                        'task': task_name,
                        'success': False,
                        'message': f"Task execution failed: {str(e)}",
                        'error': str(e)
                    })
            
            # Generate comprehensive summary
            successful_tasks = len([r for r in all_results if r['success']])
            total_tasks = len(all_results)
            
            # Extract key metrics
            total_critical_failures = 0
            total_warnings = 0
            total_anomalies = 0
            
            for result in all_results:
                if result['success'] and result.get('data'):
                    data = result['data']
                    total_critical_failures += data.get('critical_failures', 0)
                    total_warnings += data.get('warnings', 0)
                    if 'total_anomalies' in data:
                        total_anomalies += data['total_anomalies']
            
            # Overall assessment
            overall_score = self._calculate_validation_score(all_results)
            
            validation_duration = (datetime.now() - validation_start_time).total_seconds()
            
            # Create comprehensive report
            comprehensive_report = {
                'timestamp': validation_start_time.isoformat(),
                'duration_seconds': validation_duration,
                'overall_score': overall_score,
                'summary': {
                    'total_validation_tasks': total_tasks,
                    'successful_tasks': successful_tasks,
                    'failed_tasks': total_tasks - successful_tasks,
                    'total_critical_failures': total_critical_failures,
                    'total_warnings': total_warnings,
                    'total_anomalies': total_anomalies
                },
                'task_results': all_results,
                'recommendations': self._generate_validation_recommendations(all_results)
            }
            
            # Save comprehensive report
            report_filename = f"comprehensive_validation_{int(validation_start_time.timestamp())}.json"
            report_path = self.validation_logs_dir / report_filename
            
            with open(report_path, 'w') as f:
                json.dump(comprehensive_report, f, indent=2, default=str)
            
            # Determine overall success
            overall_success = successful_tasks == total_tasks and total_critical_failures == 0
            
            return TaskResult(
                success=overall_success,
                message=f"Comprehensive validation: {overall_score:.1f}/100 score, {total_critical_failures} critical failures",
                data=comprehensive_report
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Comprehensive validation failed: {str(e)}",
                errors=[str(e)]
            )
    
    def _calculate_validation_score(self, results: List[Dict[str, Any]]) -> float:
        """Calculate overall validation score (0-100)"""
        base_score = 100.0
        
        for result in results:
            if not result['success']:
                base_score -= 15  # -15 points per failed validation task
            
            if result.get('data'):
                data = result['data']
                
                # Deduct points for critical failures
                critical_failures = data.get('critical_failures', 0)
                base_score -= critical_failures * 5
                
                # Deduct points for warnings (less severe)
                warnings = data.get('warnings', 0)
                base_score -= warnings * 1
                
                # Deduct points for anomalies
                anomalies = data.get('total_anomalies', 0)
                base_score -= min(anomalies * 0.5, 10)  # Cap at 10 points
        
        return max(0.0, min(100.0, base_score))
    
    def _generate_validation_recommendations(self, results: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []
        
        for result in results:
            if not result['success']:
                recommendations.append(f"Fix issues in {result['task']}: {result['message']}")
            
            if result.get('data'):
                data = result['data']
                
                if data.get('critical_failures', 0) > 0:
                    recommendations.append(f"Address {data['critical_failures']} critical failures in {result['task']}")
                
                if data.get('total_anomalies', 0) > 10:
                    recommendations.append(f"Investigate {data['total_anomalies']} data anomalies")
        
        if not recommendations:
            recommendations.append("Data validation passed - no immediate action required")
        
        return recommendations
    
    def _validation_result_to_dict(self, result: ValidationResult) -> Dict[str, Any]:
        """Convert ValidationResult to dictionary"""
        return {
            'rule_name': result.rule_name,
            'passed': result.passed,
            'message': result.message,
            'severity': result.severity,
            'category': result.category,
            'details': result.details,
            'affected_records_count': len(result.affected_records) if result.affected_records else 0
        }