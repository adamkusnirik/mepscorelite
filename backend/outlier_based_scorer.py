#!/usr/bin/env python3
"""
Outlier-Based MEP Activity Scoring System
Implements IQR-based outlier detection with logarithmic scoring (0-4 points)
"""

import math
import statistics
from typing import List, Tuple, Dict, Optional
try:
    import numpy as np
except ImportError:
    # Fallback to statistics module if numpy is not available
    import statistics
    np = None


class OutlierBasedScorer:
    """
    Implements outlier-based scoring system using IQR method and logarithmic scaling
    """
    
    def __init__(self):
        """Initialize the outlier-based scorer"""
        self.outlier_stats = {}  # Store outlier statistics per term/indicator
    
    def calculate_quartiles(self, values: List[float]) -> Tuple[float, float, float]:
        """
        Calculate Q1, Q3, and IQR for a dataset
        
        Args:
            values: List of numeric values
            
        Returns:
            Tuple of (Q1, Q3, IQR)
        """
        if not values or len(values) == 0:
            return 0.0, 0.0, 0.0
        
        # Remove None values and convert to float
        clean_values = [float(v) for v in values if v is not None]
        
        if len(clean_values) == 0:
            return 0.0, 0.0, 0.0
        
        if len(clean_values) == 1:
            val = clean_values[0]
            return val, val, 0.0
        
        # Calculate quartiles using numpy or fallback method
        if np is not None:
            q1 = np.percentile(clean_values, 25)
            q3 = np.percentile(clean_values, 75)
        else:
            # Fallback method using statistics
            sorted_values = sorted(clean_values)
            n = len(sorted_values)
            q1_index = int(n * 0.25)
            q3_index = int(n * 0.75)
            q1 = sorted_values[q1_index] if q1_index < n else sorted_values[-1]
            q3 = sorted_values[q3_index] if q3_index < n else sorted_values[-1]
        
        iqr = q3 - q1
        
        return q1, q3, iqr
    
    def detect_outliers(self, values: List[float]) -> Tuple[float, float, List[float]]:
        """
        Detect outliers using IQR method and return bounds and clean data
        
        Args:
            values: List of numeric values
            
        Returns:
            Tuple of (lower_bound, upper_bound, clean_values_within_bounds)
        """
        if not values or len(values) == 0:
            return 0.0, 0.0, []
        
        # Calculate quartiles
        q1, q3, iqr = self.calculate_quartiles(values)
        
        # Calculate outlier bounds
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        # Get values within normal range (non-outliers)
        clean_values = []
        for v in values:
            if v is not None:
                val = float(v)
                if lower_bound <= val <= upper_bound:
                    clean_values.append(val)
        
        return lower_bound, upper_bound, clean_values
    
    def normalize_values(self, values: List[float], min_val: float = None, max_val: float = None) -> List[float]:
        """
        Normalize values to 0-1 range using min-max normalization
        
        Args:
            values: List of numeric values
            min_val: Override minimum value (uses data min if None)
            max_val: Override maximum value (uses data max if None)
            
        Returns:
            List of normalized values (0-1)
        """
        if not values or len(values) == 0:
            return []
        
        clean_values = [float(v) for v in values if v is not None]
        
        if len(clean_values) == 0:
            return []
        
        if len(clean_values) == 1:
            return [0.0]  # Single value normalizes to 0
        
        # Use provided min/max or calculate from data
        data_min = min_val if min_val is not None else min(clean_values)
        data_max = max_val if max_val is not None else max(clean_values)
        
        # Handle case where min == max
        if data_max == data_min:
            return [0.0] * len(clean_values)
        
        # Normalize to 0-1 range
        normalized = []
        for val in clean_values:
            norm_val = (val - data_min) / (data_max - data_min)
            # Ensure bounds
            norm_val = max(0.0, min(1.0, norm_val))
            normalized.append(norm_val)
        
        return normalized
    
    def logarithmic_score(self, normalized_value: float) -> float:
        """
        Calculate score using logarithmic function: score = log2(1 + normalized) × 4
        
        Args:
            normalized_value: Value normalized to 0-1 range
            
        Returns:
            Score from 0 to 4 points
        """
        if normalized_value < 0:
            normalized_value = 0.0
        elif normalized_value > 1:
            normalized_value = 1.0
        
        # Apply logarithmic scaling: log2(1 + x) × 4
        # This gives smooth growth from 0 to 4 points
        score = math.log2(1 + normalized_value) * 4
        
        # Ensure bounds (should be automatic, but for safety)
        return max(0.0, min(4.0, score))
    
    def score_indicator_outlier_based(self, all_values: List[float], mep_value: float, 
                                    term: int, indicator: str) -> Dict:
        """
        Score a single MEP's indicator value using outlier-based method
        
        Args:
            all_values: All MEPs' values for this indicator in this term
            mep_value: The specific MEP's value to score
            term: Parliamentary term number
            indicator: Name of the indicator (for statistics storage)
            
        Returns:
            Dict with score, bounds, normalization info, and statistics
        """
        if mep_value is None:
            mep_value = 0.0
        
        mep_value = float(mep_value)
        
        # Detect outliers and get bounds
        lower_bound, upper_bound, clean_values = self.detect_outliers(all_values)
        
        # Store statistics for transparency
        stats_key = f"term_{term}_{indicator}"
        q1, q3, iqr = self.calculate_quartiles(all_values)
        
        self.outlier_stats[stats_key] = {
            'term': term,
            'indicator': indicator,
            'total_meps': len([v for v in all_values if v is not None]),
            'q1': q1,
            'q3': q3,
            'iqr': iqr,
            'lower_bound': lower_bound,
            'upper_bound': upper_bound,
            'clean_values_count': len(clean_values),
            'outliers_count': len([v for v in all_values if v is not None]) - len(clean_values)
        }
        
        # Apply scoring rules
        if mep_value < lower_bound:
            # Below lower bound → 0 points
            score = 0.0
            status = "below_outlier_threshold"
            normalized = 0.0
        elif mep_value > upper_bound:
            # Above upper bound → 4 points
            score = 4.0
            status = "above_outlier_threshold"
            normalized = 1.0
        else:
            # Within normal range → logarithmic scaling
            if len(clean_values) <= 1:
                # Edge case: insufficient data for normalization
                score = 2.0  # Default middle score
                normalized = 0.5
                status = "insufficient_data"
            else:
                min_clean = min(clean_values)
                max_clean = max(clean_values)
                
                if max_clean == min_clean:
                    # All clean values are the same
                    score = 2.0
                    normalized = 0.5
                    status = "uniform_data"
                else:
                    # Normal case: normalize and apply logarithmic scoring
                    normalized = (mep_value - min_clean) / (max_clean - min_clean)
                    score = self.logarithmic_score(normalized)
                    status = "normal_range"
        
        return {
            'score': round(score, 3),
            'normalized_value': round(normalized, 3),
            'status': status,
            'lower_bound': round(lower_bound, 2),
            'upper_bound': round(upper_bound, 2),
            'mep_value': mep_value,
            'statistics': self.outlier_stats[stats_key]
        }
    
    def get_outlier_statistics(self, term: int = None, indicator: str = None) -> Dict:
        """
        Get stored outlier statistics
        
        Args:
            term: Filter by term (optional)
            indicator: Filter by indicator (optional)
            
        Returns:
            Dictionary of statistics
        """
        if term is None and indicator is None:
            return self.outlier_stats
        
        filtered_stats = {}
        for key, stats in self.outlier_stats.items():
            if term and stats['term'] != term:
                continue
            if indicator and stats['indicator'] != indicator:
                continue
            filtered_stats[key] = stats
        
        return filtered_stats
    
    def validate_scoring_system(self, test_values: List[float]) -> Dict:
        """
        Validate the scoring system with test data
        
        Args:
            test_values: Test dataset
            
        Returns:
            Validation results
        """
        if not test_values:
            return {'error': 'No test values provided'}
        
        # Test outlier detection
        lower_bound, upper_bound, clean_values = self.detect_outliers(test_values)
        
        # Test normalization
        if clean_values:
            normalized = self.normalize_values(clean_values)
            
            # Test logarithmic scoring
            scores = [self.logarithmic_score(norm) for norm in normalized]
            
            return {
                'input_count': len(test_values),
                'clean_count': len(clean_values),
                'outlier_count': len(test_values) - len(clean_values),
                'bounds': {'lower': lower_bound, 'upper': upper_bound},
                'score_range': {'min': min(scores) if scores else 0, 'max': max(scores) if scores else 0},
                'sample_scores': scores[:5] if len(scores) >= 5 else scores,
                'validation': 'passed'
            }
        else:
            return {'error': 'No clean values after outlier removal'}