#!/usr/bin/env python3
"""
MEP Activity Scoring System
Updated methodology with 4 categories: Legislative Production, Control & Transparency, 
Engagement & Presence, and Institutional Roles

Now using outlier-based logarithmic scoring (IQR method) for all activity indicators
"""

import sqlite3
import json
import math
from typing import Dict, List, Tuple, Optional
from outlier_based_scorer import OutlierBasedScorer

class MEPRankingScorer:
    def __init__(self, db_path: str = "data/meps.db"):
        self.db_path = db_path
        
        # Initialize outlier-based scorer
        self.outlier_scorer = OutlierBasedScorer()
        
        # Activity indicators for outlier-based scoring
        self.activity_indicators = [
            'amendments',
            'written_questions', 
            'oral_questions',
            'explanations',
            'speeches',
            'motions'
        ]
        
        # Legacy ranges - will be replaced by outlier-based scoring
        self.amendment_ranges = []
        self.amendments_max_points = 6
        
        # Initialize ranges for Control & Transparency and Engagement & Presence categories
        self.statements_ranges = {
            'speeches': [],
            'explanations': [],
            'written_questions': [],  # Range-based scoring for written questions
            'oral_questions': []  # Range-based scoring for oral questions
        }
        
        self.statements_max_points = {
            'speeches': 4,
            'explanations': 4, 
            'written_questions': 4,  # Max 4 points for written questions (same as explanations)
            'oral_questions': 4  # Max 4 points for oral questions (same as explanations)
        }
        
        # Motions ranges for Engagement & Presence category
        self.motions_ranges = []
        self.motions_max_points = 4
        
        # Official MEP Ranking methodology role multipliers (October 2017)
        self.roles_coefficients = {
            'ep_president': 1.0,        # +100% - EP President (official methodology)
            'ep_vice_president': 0.25,  # +25% - EP Vice-President (official methodology)
            'committee_chair': 0.15,    # +15% - Committee Chair (official methodology)
            'committee_vice_chair': 0.15, # +15% - Committee Vice-Chair (estimated, methodology says "coordinator" but we use vice-chair)
            'ep_quaestor': 0.25,        # +25% - Quaestor (estimated based on VP level)
            'delegation_chair': 0.10,   # +10% - Delegation Chair (estimated, lower than committee)
            'delegation_vice_chair': 0.075, # +7.5% - Delegation Vice-Chair (official range 7.5-15%)
        }
        
        # Reports scoring using MEP Ranking methodology values
        # Since we don't have report type classification, use own-initiative as baseline
        self.reports_scoring = {
            'rapporteur': 4.0,      # Own-initiative rapporteur score
            'shadow': 1.0,          # Own-initiative shadow score  
            'opinion_rapporteur': 1.0,  # Own-initiative opinion rapporteur
            'opinion_shadow': 0.5       # Own-initiative opinion shadow
        }
        
        # Attendance penalty thresholds (MEP Ranking methodology)
        self.attendance_penalties = [
            (0.75, 0.75),  # Below 75% -> multiply by 0.75
            (0.55, 0.50)   # Below 55% -> multiply by 0.50
        ]
    
    def calculate_dynamic_ranges(self, term: int = 10) -> None:
        """Set term-specific scoring ranges for new 4-category methodology"""
        
        # Term-specific ranges based on quartile analysis and methodology documentation
        if term == 8:
            # 8th Term (2014-2019) ranges - Based on actual data: Written max=618, Oral max=63
            self.amendment_ranges = [(0, 300, 1), (301, 605, 2), (606, 1200, 3), (1201, float('inf'), 4)]
            self.statements_ranges = {
                'speeches': [(78, 156, 1), (157, 250, 2), (251, 400, 3), (401, float('inf'), 4)],
                'explanations': [(54, 107, 1), (108, 180, 2), (181, 300, 3), (301, float('inf'), 4)],
                'written_questions': [(0, 0, 0), (1, 35, 1), (36, 70, 2), (71, 120, 3), (121, float('inf'), 4)],  # 0-4 range based on data
                'oral_questions': [(0, 0, 0), (1, 6, 1), (7, 12, 2), (13, 25, 3), (26, float('inf'), 4)]  # 0-4 range based on data
            }
            self.motions_ranges = [(10, 20, 1), (21, 40, 2), (41, 80, 3), (81, float('inf'), 4)]
            
        elif term == 9:
            # 9th Term (2019-2024) ranges - Based on actual data: Written max=349, Oral max=20
            self.amendment_ranges = [(0, 400, 1), (401, 801, 2), (802, 1600, 3), (1601, float('inf'), 4)]
            self.statements_ranges = {
                'speeches': [(15, 29, 1), (30, 60, 2), (61, 120, 3), (121, float('inf'), 4)],
                'explanations': [(31, 61, 1), (62, 120, 2), (121, 250, 3), (251, float('inf'), 4)],
                'written_questions': [(0, 0, 0), (1, 35, 1), (36, 70, 2), (71, 120, 3), (121, float('inf'), 4)],  # 0-4 range based on data
                'oral_questions': [(0, 0, 0), (1, 3, 1), (4, 6, 2), (7, 12, 3), (13, float('inf'), 4)]  # 0-4 range based on data
            }
            self.motions_ranges = [(8, 16, 1), (17, 32, 2), (33, 64, 3), (64, float('inf'), 4)]
            
        else:  # term == 10 or default
            # 10th Term (2024-2029) ranges - Based on actual data: Written max=79, Oral max=9
            self.amendment_ranges = [(0, 84, 1), (85, 168, 2), (169, 335, 3), (336, float('inf'), 4)]
            self.statements_ranges = {
                'speeches': [(5, 10, 1), (11, 20, 2), (21, 40, 3), (41, float('inf'), 4)],
                'explanations': [(1, 2, 1), (3, 8, 2), (9, 20, 3), (21, float('inf'), 4)],
                'written_questions': [(0, 0, 0), (1, 12, 1), (13, 27, 2), (28, 50, 3), (51, float('inf'), 4)],  # 0-4 range based on data
                'oral_questions': [(0, 0, 0), (1, 1, 1), (2, 2, 2), (3, 5, 3), (6, float('inf'), 4)]  # 0-4 range based on data
            }
            self.motions_ranges = [(2, 4, 1), (5, 10, 2), (11, 20, 3), (20, float('inf'), 4)]
    
    def _calculate_ranges_from_average(self, average: float, num_ranges: int) -> List[Tuple[float, float, int]]:
        """Calculate scoring ranges based on average value"""
        if average <= 0:
            return [(0, 10, 1), (11, 20, 2), (21, float('inf'), 3)]
        
        ranges = []
        range_size = average / num_ranges
        
        for i in range(num_ranges):
            min_val = i * range_size
            max_val = (i + 1) * range_size if i < num_ranges - 1 else float('inf')
            points = i + 1
            ranges.append((min_val, max_val, points))
        
        return ranges
    
    def _set_default_ranges(self) -> None:
        """Set default ranges when no data is available"""
        self.amendment_ranges = [(1, 66, 1), (67, 133, 2), (134, 200, 3), (201, float('inf'), 4)]
        self.statements_ranges = {
            'speeches': [(250, 500, 1), (501, 750, 2), (751, 1000, 3), (1001, float('inf'), 4)],
            'explanations': [(140, 280, 1), (281, 420, 2), (421, 560, 3), (561, float('inf'), 4)],
            'written_questions': [(0, 0, 0), (1, 35, 1), (36, 70, 2), (71, 120, 3), (121, float('inf'), 4)],
            'oral_questions': [(0, 0, 0), (1, 6, 1), (7, 12, 2), (13, 25, 3), (26, float('inf'), 4)]
        }
        self.motions_ranges = [(5, 10, 1), (11, 20, 2), (21, 40, 3), (41, float('inf'), 4)]
    
    def get_mep_data(self, term: int = 10) -> List[Dict]:
        """Get MEP data using optimized queries"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get total votes for this term
        cursor.execute("""
            SELECT votes_total
            FROM term_vote_totals
            WHERE term = ?
        """, (term,))
        total_votes_result = cursor.fetchone()
        total_votes = total_votes_result[0] if total_votes_result else 0
        
        # Main query for MEP data and activities
        query = """
        SELECT 
            m.mep_id, m.full_name, m.country, m.current_party_group, m.current_party,
            a.speeches, a.reports_rapporteur, a.reports_shadow, 
            a.amendments, a.questions_written, a.questions_oral, a.questions_major,
            a.motions, a.motions_individual, a.opinions_rapporteur, a.opinions_shadow,
            a.explanations, a.declarations,
            COALESCE(va.votes_attended, 0) as votes_attended
        FROM meps m
        INNER JOIN activities a ON m.mep_id = a.mep_id
            LEFT JOIN (
                SELECT mep_id, votes_attended
                FROM mep_vote_summary
                WHERE term = ?
            ) va ON m.mep_id = va.mep_id
        WHERE a.term = ?
        """
        
        cursor.execute(query, (term, term))
        meps_data = {}
        
        for row in cursor.fetchall():
            mep_id = row[0]
            meps_data[mep_id] = {
                'mep_id': mep_id,
                'full_name': row[1] or 'Unknown',
                'country': row[2] or 'Unknown',
                'group': row[3] or 'Unknown',
                'national_party': row[4] or 'Unknown',
                'speeches': row[5] or 0,
                'reports_rapporteur': row[6] or 0,
                'reports_shadow': row[7] or 0,
                'amendments': row[8] or 0,
                'questions_written': row[9] or 0,
                'questions_oral': row[10] or 0,
                'questions_major': row[11] or 0,
                'motions': (row[12] or 0) + (row[13] or 0),
                'opinions_rapporteur': row[14] or 0,
                'opinions_shadow': row[15] or 0,
                'explanations': row[16] or 0,
                'declarations': row[17] or 0,
                'votes_attended': row[18] or 0,
                'votes_total': 0,
                'roles': []
            }
        
        # Get all roles in one query
        mep_ids = list(meps_data.keys())
        if mep_ids:
            placeholders = ','.join('?' * len(mep_ids))
            cursor.execute(f"""
                SELECT mep_id, role_type, role, organization
                FROM roles 
                WHERE mep_id IN ({placeholders}) AND term = ?
            """, mep_ids + [term])
            
            for row in cursor.fetchall():
                mep_id = row[0]
                if mep_id in meps_data:
                    meps_data[mep_id]['roles'].append({
                        'type': row[1], 'role': row[2], 'org': row[3]
                    })
        
        # Update votes_total for all MEPs
        for mep_data in meps_data.values():
            mep_data['votes_total'] = total_votes
        
        conn.close()
        return list(meps_data.values())
    
    def get_all_indicator_values(self, term: int, indicator: str) -> List[float]:
        """
        Get all MEP values for a specific indicator in a term for outlier analysis
        
        Args:
            term: Parliamentary term number
            indicator: Name of the indicator (amendments, written_questions, etc.)
            
        Returns:
            List of all MEP values for this indicator
        """
        meps_data = self.get_mep_data(term)
        
        # Map indicator to correct field name
        field_mapping = {
            'amendments': 'amendments',
            'written_questions': 'questions_written',
            'oral_questions': 'questions_oral', 
            'explanations': 'explanations',
            'speeches': 'speeches',
            'motions': 'motions'
        }
        
        field_name = field_mapping.get(indicator, indicator)
        values = []
        
        for mep in meps_data:
            value = mep.get(field_name, 0)
            values.append(float(value) if value is not None else 0.0)
        
        return values
    
    def calculate_outlier_based_scores(self, mep: Dict, term: int) -> Dict:
        """
        Calculate outlier-based scores for all activity indicators
        
        Args:
            mep: MEP data dictionary
            term: Parliamentary term number
            
        Returns:
            Dictionary with scores and statistics for each indicator
        """
        scores = {}
        
        # Field mapping for MEP data
        field_mapping = {
            'amendments': 'amendments',
            'written_questions': 'questions_written',
            'oral_questions': 'questions_oral',
            'explanations': 'explanations', 
            'speeches': 'speeches',
            'motions': 'motions'
        }
        
        for indicator in self.activity_indicators:
            # Get all values for this indicator/term for outlier analysis
            all_values = self.get_all_indicator_values(term, indicator)
            
            # Get this MEP's value
            field_name = field_mapping.get(indicator, indicator)
            mep_value = mep.get(field_name, 0)
            if mep_value is None:
                mep_value = 0.0
            
            # Calculate outlier-based score
            result = self.outlier_scorer.score_indicator_outlier_based(
                all_values=all_values,
                mep_value=float(mep_value),
                term=term,
                indicator=indicator
            )
            
            # Store score and metadata
            scores[f"{indicator}_score"] = result['score']
            scores[f"{indicator}_info"] = {
                'value': result['mep_value'],
                'normalized': result['normalized_value'],
                'status': result['status'],
                'bounds': {
                    'lower': result['lower_bound'],
                    'upper': result['upper_bound']
                }
            }
        
        return scores
    
    def calculate_reports_score(self, mep: Dict) -> Dict:
        """Calculate Reports category score using MEP Ranking methodology"""
        
        # Apply MEP Ranking scoring values to available data
        rapporteur_score = mep['reports_rapporteur'] * self.reports_scoring['rapporteur']
        shadow_score = mep['reports_shadow'] * self.reports_scoring['shadow']
        opinion_rap_score = mep['opinions_rapporteur'] * self.reports_scoring['opinion_rapporteur']
        opinion_shadow_score = mep['opinions_shadow'] * self.reports_scoring['opinion_shadow']
        
        return {
            'reports_rapporteur_score': rapporteur_score,
            'reports_shadow_score': shadow_score,
            'opinions_rapporteur_score': opinion_rap_score,
            'opinions_shadow_score': opinion_shadow_score,
            'reports_total': rapporteur_score + shadow_score + opinion_rap_score + opinion_shadow_score
        }
    
    def calculate_amendments_score(self, mep: Dict) -> float:
        """Calculate Amendments score using term-specific range-based system"""
        amendments_count = mep['amendments']
        
        # Use term-specific amendment ranges
        amendments_score = 0
        for min_val, max_val, points in self.amendment_ranges:
            if min_val <= amendments_count <= max_val:
                amendments_score = points
                break
            elif amendments_count > max_val and max_val != float('inf'):
                # Continue checking higher ranges
                continue
            elif max_val == float('inf') and amendments_count >= min_val:
                amendments_score = points
                break
            
        return amendments_score
    
    def calculate_control_transparency_score(self, mep: Dict) -> Dict:
        """Calculate Control & Transparency category score (questions and explanations)"""
        scores = {}
        
        # Written questions - using term-specific ranges
        written_questions_score = 0
        written_questions_count = mep['questions_written']
        for min_val, max_val, points in self.statements_ranges['written_questions']:
            if min_val <= written_questions_count <= max_val:
                written_questions_score = points
                break
            elif written_questions_count > max_val and max_val != float('inf'):
                # Continue checking higher ranges
                continue
            elif max_val == float('inf') and written_questions_count >= min_val:
                written_questions_score = points
                break
        scores['written_questions_score'] = min(written_questions_score, self.statements_max_points['written_questions'])
        
        # Oral questions - using term-specific ranges
        oral_questions_score = 0
        oral_questions_count = mep['questions_oral']
        for min_val, max_val, points in self.statements_ranges['oral_questions']:
            if min_val <= oral_questions_count <= max_val:
                oral_questions_score = points
                break
            elif oral_questions_count > max_val and max_val != float('inf'):
                # Continue checking higher ranges
                continue
            elif max_val == float('inf') and oral_questions_count >= min_val:
                oral_questions_score = points
                break
        scores['oral_questions_score'] = min(oral_questions_score, self.statements_max_points['oral_questions'])
        
        # Explanations of vote - using term-specific ranges 
        explanations_score = 0
        explanations_count = mep['explanations']
        for min_val, max_val, points in self.statements_ranges['explanations']:
            if min_val <= explanations_count <= max_val:
                explanations_score = points
                break
            elif explanations_count > max_val and max_val != float('inf'):
                # Continue checking higher ranges
                continue
            elif max_val == float('inf') and explanations_count >= min_val:
                explanations_score = points
                break
        scores['explanations_score'] = min(explanations_score, self.statements_max_points['explanations'])
        
        scores['control_transparency_total'] = sum(scores.values())
        return scores
    
    def calculate_engagement_presence_score(self, mep: Dict) -> Dict:
        """Calculate Engagement & Presence category score (speeches and motions - official methodology)
        
        Note: Official MEP Ranking methodology includes both speeches and motions for resolutions.
        """
        scores = {}
        
        # Speeches - using term-specific ranges (official methodology)
        speeches_score = 0
        speeches_count = mep['speeches']
        for min_val, max_val, points in self.statements_ranges['speeches']:
            if min_val <= speeches_count <= max_val:
                speeches_score = points
                break
            elif speeches_count > max_val and max_val != float('inf'):
                # Continue checking higher ranges
                continue
            elif max_val == float('inf') and speeches_count >= min_val:
                speeches_score = points
                break
        scores['speeches_score'] = min(speeches_score, self.statements_max_points['speeches'])
        
        # Motions for Resolutions - using term-specific ranges (official methodology)
        motions_score = 0
        motions_count = mep['motions']
        for min_val, max_val, points in self.motions_ranges:
            if min_val <= motions_count <= max_val:
                motions_score = points
                break
            elif motions_count > max_val and max_val != float('inf'):
                # Continue checking higher ranges
                continue
            elif max_val == float('inf') and motions_count >= min_val:
                motions_score = points
                break
        scores['motions_score'] = min(motions_score, self.motions_max_points)
        
        # Voting attendance will be handled as penalty in final calculation
        # Here we just track the attendance rate for reference
        if mep['votes_total'] > 0:
            scores['attendance_rate'] = mep['votes_attended'] / mep['votes_total']
        else:
            scores['attendance_rate'] = 0.0
        
        # Speeches and motions count for engagement & presence score (official methodology)
        scores['engagement_presence_total'] = scores['speeches_score'] + scores['motions_score']
        return scores
    
    def calculate_roles_score(self, mep: Dict) -> Dict:
        """Calculate Roles score as percentage multiplier"""
        roles_multiplier = 0.0
        top_role = None
        
        for role in mep['roles']:
            role_key = self._get_role_key(role)
            if role_key and role_key in self.roles_coefficients:
                coefficient = self.roles_coefficients[role_key]
                if coefficient > roles_multiplier:
                    roles_multiplier = coefficient
                    top_role = role_key
        
        return {
            'roles_multiplier': roles_multiplier,
            'top_role': top_role,
            'roles_percentage': roles_multiplier * 100
        }
    
    def _get_role_key(self, role: Dict) -> Optional[str]:
        """Convert role information to scoring key for new 4-category methodology"""
        role_type = role['type'].lower()
        role_name = role['role'].lower()
        
        # EP Leadership
        if 'president' in role_name and 'vice' not in role_name:
            return 'ep_president'
        elif 'vice' in role_name and 'president' in role_name:
            return 'ep_vice_president'
        elif 'quaestor' in role_name:
            return 'ep_quaestor'
        
        # Committee roles
        elif role_type == 'committee':
            if 'chair' in role_name and 'vice' not in role_name:
                return 'committee_chair'
            elif 'vice' in role_name and 'chair' in role_name:
                return 'committee_vice_chair'
        
        # Delegation roles
        elif role_type == 'delegation':
            if 'chair' in role_name and 'vice' not in role_name:
                return 'delegation_chair'
            elif 'vice' in role_name and 'chair' in role_name:
                return 'delegation_vice_chair'
        
        return None
    
    def calculate_attendance_penalty(self, mep: Dict) -> float:
        """Calculate attendance penalty multiplier using MEP Ranking methodology
        
        Note: Only EP Chair and Vice Chair are exempt from attendance penalties as they
        cannot vote when presiding over plenary sessions. Committee/Delegation chairs 
        are NOT exempt as they only preside over committee meetings, not plenary votes.
        """
        if mep['votes_total'] == 0:
            return 1.0  # No penalty if no voting data
        
        # Exempt only EP Chair and Vice Chair from attendance penalties
        # They cannot vote when presiding over EP sessions, so low attendance is not indicative of poor performance
        # Committee/Delegation chairs are NOT exempt as they only preside over committee meetings, not plenary votes
        if (mep.get('ep_president', 0) > 0 or 
            mep.get('ep_vice_president', 0) > 0):
            return 1.0  # No attendance penalty for EP presiding officers only
        
        attendance_rate = mep['votes_attended'] / mep['votes_total']
        
        # MEP Ranking methodology: penalties applied in order of severity
        # Below 55% -> multiply by 0.5 (50% penalty)
        if attendance_rate < 0.55:
            return 0.5
        # Below 75% -> multiply by 0.75 (25% penalty)  
        elif attendance_rate < 0.75:
            return 0.75
        # 75% and above -> no penalty
        else:
            return 1.0
    
    def score_mep(self, mep: Dict, term: int) -> Dict:
        """Calculate complete MEP score using new outlier-based methodology"""
        
        # Validation: Check for required fields
        required_fields = ['mep_id', 'full_name']
        for field in required_fields:
            if field not in mep or mep[field] is None:
                print(f"WARNING: MEP missing {field}: {mep}")
        
        # NEW OUTLIER-BASED METHODOLOGY
        
        # Calculate outlier-based scores for all 6 activity indicators
        outlier_scores = self.calculate_outlier_based_scores(mep, term)
        
        # Extract individual scores
        amendments_score = outlier_scores['amendments_score']
        written_questions_score = outlier_scores['written_questions_score']
        oral_questions_score = outlier_scores['oral_questions_score'] 
        explanations_score = outlier_scores['explanations_score']
        speeches_score = outlier_scores['speeches_score']
        motions_score = outlier_scores['motions_score']
        
        # 1. Legislative Production (Reports + Amendments)
        reports_scores = self.calculate_reports_score(mep)
        reports_total = reports_scores['reports_total']
        legislative_production_score = reports_total + amendments_score
        
        # 2. Control & Transparency (Questions + Explanations)
        control_transparency_total = written_questions_score + oral_questions_score + explanations_score
        
        # 3. Engagement & Presence (Speeches + Motions)
        engagement_presence_total = speeches_score + motions_score
        
        # 4. Calculate base score (sum of all categories)
        base_score = legislative_production_score + control_transparency_total + engagement_presence_total
        
        # 5. Institutional Roles (as percentage multiplier)
        roles_scores = self.calculate_roles_score(mep)
        roles_multiplier = 1.0 + roles_scores['roles_multiplier']  # Add percentage to base
        
        # 6. Apply roles multiplier
        score_with_roles = base_score * roles_multiplier
        
        # 7. Apply attendance penalty
        attendance_penalty = self.calculate_attendance_penalty(mep)
        final_score = score_with_roles * attendance_penalty
        
        result = {
            'mep_id': mep['mep_id'],
            'full_name': mep['full_name'],
            'country': mep['country'],
            'group': mep['group'],
            # New 4-category scores
            'legislative_production_score': legislative_production_score,
            'control_transparency_score': control_transparency_total,
            'engagement_presence_score': engagement_presence_total,
            'institutional_roles_multiplier': roles_multiplier,
            # Individual outlier-based activity scores
            'amendments_score': amendments_score,
            'written_questions_score': written_questions_score,
            'oral_questions_score': oral_questions_score,
            'explanations_score': explanations_score,
            'speeches_score': speeches_score,
            'motions_score': motions_score,
            # Reports score (still using legacy method)
            'reports_score': reports_total,
            'base_score': base_score,
            'roles_multiplier': roles_multiplier,
            'score_with_roles': score_with_roles,
            'attendance_penalty': attendance_penalty,
            'final_score': final_score,
            'attendance_rate': mep['votes_attended'] / mep['votes_total'] if mep['votes_total'] > 0 else 0,
            # Include original activity counts for frontend display
            'speeches': mep['speeches'],
            'explanations': mep['explanations'],
            'amendments': mep['amendments'],
            'questions_written': mep['questions_written'],
            'questions_oral': mep['questions_oral'],
            'motions': mep.get('motions', 0),
            'reports_rapporteur': mep['reports_rapporteur'],
            'reports_shadow': mep['reports_shadow'],
            'opinions_rapporteur': mep['opinions_rapporteur'],
            'opinions_shadow': mep['opinions_shadow'],
            'votes_attended': mep['votes_attended'],
            'votes_total': mep['votes_total'],
            'national_party': mep['national_party'],
            # Include detailed breakdowns
            **reports_scores,
            **roles_scores,
            # Include outlier-based score metadata
            'score_breakdown': {
                'amendments': outlier_scores['amendments_info'],
                'written_questions': outlier_scores['written_questions_info'],
                'oral_questions': outlier_scores['oral_questions_info'],
                'explanations': outlier_scores['explanations_info'], 
                'speeches': outlier_scores['speeches_info'],
                'motions': outlier_scores['motions_info']
            }
        }
        
        # Ensure roles_multiplier is the correct full multiplier
        result['roles_multiplier'] = roles_multiplier
        
        return result
    
    def score_mep_optimized(self, mep: Dict, term: int, outlier_data: Dict) -> Dict:
        """Optimized version of score_mep that uses pre-calculated outlier data"""
        
        # Validation: Check for required fields
        required_fields = ['mep_id', 'full_name']
        for field in required_fields:
            if field not in mep or mep[field] is None:
                print(f"WARNING: MEP missing {field}: {mep}")
        
        # Calculate outlier-based scores using pre-calculated data
        outlier_scores = self.calculate_outlier_based_scores_optimized(mep, term, outlier_data)
        
        # Extract individual scores
        amendments_score = outlier_scores['amendments_score']
        written_questions_score = outlier_scores['written_questions_score']
        oral_questions_score = outlier_scores['oral_questions_score'] 
        explanations_score = outlier_scores['explanations_score']
        speeches_score = outlier_scores['speeches_score']
        motions_score = outlier_scores['motions_score']
        
        # 1. Legislative Production (Reports + Amendments)
        reports_scores = self.calculate_reports_score(mep)
        reports_total = reports_scores['reports_total']
        legislative_production_score = reports_total + amendments_score
        
        # 2. Control & Transparency (Questions + Explanations)
        control_transparency_total = written_questions_score + oral_questions_score + explanations_score
        
        # 3. Engagement & Presence (Speeches + Motions)
        engagement_presence_total = speeches_score + motions_score
        
        # 4. Calculate base score (sum of all categories)
        base_score = legislative_production_score + control_transparency_total + engagement_presence_total
        
        # 5. Institutional Roles (as percentage multiplier)
        roles_scores = self.calculate_roles_score(mep)
        roles_multiplier = 1.0 + roles_scores['roles_multiplier']  # Add percentage to base
        
        # 6. Apply roles multiplier
        score_with_roles = base_score * roles_multiplier
        
        # 7. Apply attendance penalty
        attendance_penalty = self.calculate_attendance_penalty(mep)
        final_score = score_with_roles * attendance_penalty
        
        result = {
            'mep_id': mep['mep_id'],
            'full_name': mep['full_name'],
            'country': mep['country'],
            'group': mep['group'],
            # New 4-category scores
            'legislative_production_score': legislative_production_score,
            'control_transparency_score': control_transparency_total,
            'engagement_presence_score': engagement_presence_total,
            'institutional_roles_multiplier': roles_multiplier,
            # Individual outlier-based activity scores
            'amendments_score': amendments_score,
            'written_questions_score': written_questions_score,
            'oral_questions_score': oral_questions_score,
            'explanations_score': explanations_score,
            'speeches_score': speeches_score,
            'motions_score': motions_score,
            # Reports score (still using legacy method)
            'reports_score': reports_total,
            'base_score': base_score,
            'roles_multiplier': roles_multiplier,
            'score_with_roles': score_with_roles,
            'attendance_penalty': attendance_penalty,
            'final_score': final_score,
            'attendance_rate': mep['votes_attended'] / mep['votes_total'] if mep['votes_total'] > 0 else 0,
            # Include original activity counts for frontend display
            'speeches': mep['speeches'],
            'explanations': mep['explanations'],
            'amendments': mep['amendments'],
            'questions_written': mep['questions_written'],
            'questions_oral': mep['questions_oral'],
            'motions': mep.get('motions', 0),
            'reports_rapporteur': mep['reports_rapporteur'],
            'reports_shadow': mep['reports_shadow'],
            'opinions_rapporteur': mep['opinions_rapporteur'],
            'opinions_shadow': mep['opinions_shadow'],
            'votes_attended': mep['votes_attended'],
            'votes_total': mep['votes_total'],
            'national_party': mep['national_party'],
            # Include detailed breakdowns
            **reports_scores,
            **roles_scores,
            # Include outlier-based score metadata
            'score_breakdown': {
                'amendments': outlier_scores['amendments_info'],
                'written_questions': outlier_scores['written_questions_info'],
                'oral_questions': outlier_scores['oral_questions_info'],
                'explanations': outlier_scores['explanations_info'], 
                'speeches': outlier_scores['speeches_info'],
                'motions': outlier_scores['motions_info']
            }
        }
        
        # Ensure roles_multiplier is the correct full multiplier
        result['roles_multiplier'] = roles_multiplier
        
        return result
    
    def calculate_outlier_based_scores_optimized(self, mep: Dict, term: int, outlier_data: Dict) -> Dict:
        """Optimized version using pre-calculated outlier data"""
        scores = {}
        
        # Field mapping for MEP data
        field_mapping = {
            'amendments': 'amendments',
            'written_questions': 'questions_written',
            'oral_questions': 'questions_oral',
            'explanations': 'explanations', 
            'speeches': 'speeches',
            'motions': 'motions'
        }
        
        for indicator in self.activity_indicators:
            # Get this MEP's value
            field_name = field_mapping.get(indicator, indicator)
            mep_value = mep.get(field_name, 0)
            if mep_value is None:
                mep_value = 0.0
            
            # Use pre-calculated outlier data
            all_values = outlier_data[indicator]['all_values']
            
            # Calculate outlier-based score
            result = self.outlier_scorer.score_indicator_outlier_based(
                all_values=all_values,
                mep_value=float(mep_value),
                term=term,
                indicator=indicator
            )
            
            # Store score and metadata
            scores[f"{indicator}_score"] = result['score']
            scores[f"{indicator}_info"] = {
                'value': result['mep_value'],
                'normalized': result['normalized_value'],
                'status': result['status'],
                'bounds': {
                    'lower': result['lower_bound'],
                    'upper': result['upper_bound']
                }
            }
        
        return scores
    
    def score_all_meps(self, term: int = 10) -> List[Dict]:
        """Score all MEPs using new 4-category methodology with optimized outlier calculation"""
        # Calculate dynamic ranges based on term data before scoring
        self.calculate_dynamic_ranges(term)
        
        meps_data = self.get_mep_data(term)
        
        if not meps_data:
            return []
        
        print(f"Scoring {len(meps_data)} MEPs for term {term}...")
        
        # PRE-CALCULATE ALL OUTLIER STATISTICS ONCE (Performance optimization)
        print("Pre-calculating outlier statistics for all indicators...")
        outlier_data = {}
        
        for indicator in self.activity_indicators:
            print(f"  Calculating outliers for {indicator}...")
            all_values = self.get_all_indicator_values(term, indicator)
            outlier_data[indicator] = {
                'all_values': all_values,
                'outlier_stats': None  # Will be calculated by outlier_scorer when first used
            }
        
        # Score each MEP using pre-calculated outlier data
        results = []
        for i, mep in enumerate(meps_data):
            if i % 100 == 0:
                print(f"  Scoring MEP {i+1}/{len(meps_data)}...")
            
            result = self.score_mep_optimized(mep, term, outlier_data)
            results.append(result)
        
        # Sort by final score
        results.sort(key=lambda x: x['final_score'], reverse=True)
        
        # Add rankings
        for i, result in enumerate(results):
            result['rank'] = i + 1
        
        print(f"Completed scoring {len(results)} MEPs")
        return results

if __name__ == "__main__":
    try:
        # Test the new 4-category MEP scoring system
        print("Initializing MEP Activity Scorer (4-category methodology)...")
        scorer = MEPRankingScorer()
        
        print("Scoring MEPs...")
        results = scorer.score_all_meps(term=10)
        
        print(f"Scored {len(results)} MEPs using new 4-category methodology")
        print("Categories: Legislative Production, Control & Transparency, Engagement & Presence, Institutional Roles")
        print("\nTop 10:")
        for i, mep in enumerate(results[:10]):
            try:
                name = mep['full_name'][:30] if len(mep['full_name']) > 30 else mep['full_name']
                print(f"{i+1:2d}. {name:<30} {mep['final_score']:.1f}")
            except (KeyError, UnicodeEncodeError) as e:
                print(f"{i+1:2d}. [Error displaying name] {mep.get('final_score', 0):.1f}")
        
        # Export results
        import os
        os.makedirs('public/data', exist_ok=True)
        with open('public/data/mep_ranking_scores.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print("\nResults saved to public/data/mep_ranking_scores.json")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
