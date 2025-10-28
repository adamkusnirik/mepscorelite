#!/usr/bin/env python3
"""
European Parliament Member Scoring System
Based on 4-axis scoring with customizable weights
"""

import sqlite3
import json
import math
from typing import Dict, List, Tuple, Optional

class EPScoringSystem:
    def __init__(self, db_path: str = "data/meps.db"):
        self.db_path = db_path
        
        # Default axis weights (sum = 1)
        self.axis_weights = {
            "legislative_production": 0.40,
            "control_transparency": 0.15,
            "engagement_presence": 0.25,
            "institutional_roles": 0.20
        }
        
        # Metric weights removed - no double weighting
        # Individual metrics are scored directly with per_unit_points
        # and then summed for axis totals
        
        # Points per unit
        self.per_unit_points = {
            "reports_rap": 5.0,
            "reports_shadow": 3.0,
            "opinions_rap": 2.0,
            "opinions_shadow": 1.0,
            "speech": 0.04,
            "question": 0.10,
            "motion": 0.10,
            "explanation": 0.05
        }
        
        # Maximum points caps
        self.caps = {
            "amendments_max_points": 6,
            "questions_max_points": 3,
            "motions_max_points": 3,
            "explanations_max_points": 4,
            "speeches_max_points": 4,
            "votes_max_points": 2
        }
        
        # Role coefficients
        self.roles_coefficients = {
            "ep_president": 1.2,
            "ep_vice_president": 0.8,
            "quaestor": 0.5,
            "committee_chair": 1.0,
            "delegation_chair": 0.8,
            "committee_vice_chair": 0.8,
            "delegation_vice_chair": 0.6,
            "committee_member": 0.5,
            "delegation_member": 0.4,
            "committee_substitute": 0.3,
            "delegation_substitute": 0.3
        }
        
        self.roles_max_coeff = 1.2
    
    def update_weights(self, axis_weights: Optional[Dict] = None):
        """Update axis weights (no normalization - allow negative weights)"""
        if axis_weights:
            # No normalization - allow any values including negative
            self.axis_weights = axis_weights.copy()
    
    def get_mep_data(self, term: int = 10) -> List[Dict]:
        """Get MEP data with activities and roles for scoring"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get MEPs with activities for specific term only
        query = """
        SELECT 
            m.mep_id, m.full_name, m.country, m.current_party_group,
            a.speeches, a.reports_rapporteur, a.reports_shadow, 
            a.amendments, a.questions_written, a.questions_oral, a.questions_major,
            a.motions, a.motions_individual, a.opinions_rapporteur, a.opinions_shadow,
            a.explanations
        FROM meps m
        INNER JOIN activities a ON m.mep_id = a.mep_id AND a.term = ?
        WHERE a.term = ?
        """
        
        cursor.execute(query, (term, term))
        meps_data = []
        
        for row in cursor.fetchall():
            mep = {
                'mep_id': row[0],
                'full_name': row[1],
                'country': row[2],
                'group': row[3],
                'speeches': row[4] or 0,
                'reports_rap': row[5] or 0,
                'reports_shadow': row[6] or 0,
                'amendments': row[7] or 0,
                'questions': (row[8] or 0) + (row[9] or 0) + (row[10] or 0),  # All question types
                'motions': (row[11] or 0) + (row[12] or 0),  # All motion types
                'opinions_rap': row[13] or 0,
                'opinions_shadow': row[14] or 0,
                'explanations': row[15] or 0,
                'votes_attended': 0,  # Will be calculated from votes table if available
                'votes_total': 0,
                'roles': []
            }
            meps_data.append(mep)
        
        # Get roles for each MEP
        for mep in meps_data:
            cursor.execute("""
                SELECT role_type, role, organization
                FROM roles 
                WHERE mep_id = ? AND term = ?
            """, (mep['mep_id'], term))
            
            roles = cursor.fetchall()
            mep['roles'] = [{'type': r[0], 'role': r[1], 'org': r[2]} for r in roles]
        
        # Try to get voting data from the compact summary tables
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='mep_vote_summary'")
            has_summary = cursor.fetchone() is not None
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='term_vote_totals'")
            has_totals = cursor.fetchone() is not None

            total_votes = 0
            if has_totals:
                cursor.execute("SELECT votes_total FROM term_vote_totals WHERE term = ?", (term,))
                total_row = cursor.fetchone()
                total_votes = (total_row[0] or 0) if total_row else 0

            if has_summary and has_totals:
                cursor.execute(
                    "SELECT mep_id, votes_attended FROM mep_vote_summary WHERE term = ?",
                    (term,),
                )
                votes_map = {row[0]: row[1] or 0 for row in cursor.fetchall()}

                for mep in meps_data:
                    mep['votes_attended'] = votes_map.get(mep['mep_id'], 0)
                    mep['votes_total'] = total_votes
        except sqlite3.Error:
            pass  # Votes summary not available
        
        conn.close()
        return meps_data
    
    def calculate_individual_scores(self, mep: Dict, max_amendments: int) -> Dict:
        """Calculate individual metric scores for a MEP"""
        scores = {}
        
        # Direct scoring
        scores['score_reports_rap'] = mep['reports_rap'] * self.per_unit_points['reports_rap']
        scores['score_reports_shadow'] = mep['reports_shadow'] * self.per_unit_points['reports_shadow']
        scores['score_opinions_rap'] = mep['opinions_rap'] * self.per_unit_points['opinions_rap']
        scores['score_opinions_shadow'] = mep['opinions_shadow'] * self.per_unit_points['opinions_shadow']
        
        # Amendments (logarithmic scale)
        if max_amendments > 0:
            scores['score_amend'] = min(
                self.caps['amendments_max_points'] * math.log(1 + mep['amendments']) / math.log(1 + max_amendments),
                self.caps['amendments_max_points']
            )
        else:
            scores['score_amend'] = 0
        
        # Capped scores
        scores['score_questions'] = min(mep['questions'] * self.per_unit_points['question'], self.caps['questions_max_points'])
        scores['score_motions'] = min(mep['motions'] * self.per_unit_points['motion'], self.caps['motions_max_points'])
        scores['score_explanations'] = min(mep['explanations'] * self.per_unit_points['explanation'], self.caps['explanations_max_points'])
        scores['score_speeches'] = min(mep['speeches'] * self.per_unit_points['speech'], self.caps['speeches_max_points'])
        
        # Voting attendance
        if mep['votes_total'] > 0:
            attendance_rate = mep['votes_attended'] / mep['votes_total']
            scores['score_votes'] = min(attendance_rate * self.caps['votes_max_points'], self.caps['votes_max_points'])
        else:
            scores['score_votes'] = 0
        
        # Roles - find highest coefficient
        top_role_coeff = 0
        top_role = None
        
        for role in mep['roles']:
            role_key = self._get_role_key(role)
            if role_key and role_key in self.roles_coefficients:
                coeff = self.roles_coefficients[role_key]
                if coeff > top_role_coeff:
                    top_role_coeff = coeff
                    top_role = role_key
        
        scores['role_score_raw'] = top_role_coeff / self.roles_max_coeff
        scores['top_role_used'] = top_role
        scores['top_role_coeff'] = top_role_coeff
        
        return scores
    
    def _get_role_key(self, role: Dict) -> Optional[str]:
        """Convert role information to scoring key"""
        role_type = role['type'].lower()
        role_name = role['role'].lower()
        
        # EP Leadership
        if 'president' in role_name and 'vice' not in role_name:
            return 'ep_president'
        elif 'vice' in role_name and 'president' in role_name:
            return 'ep_vice_president'
        elif 'quaestor' in role_name:
            return 'quaestor'
        
        # Committee roles
        elif role_type == 'committee':
            if 'chair' in role_name and 'vice' not in role_name:
                return 'committee_chair'
            elif 'vice' in role_name and 'chair' in role_name:
                return 'committee_vice_chair'
            elif 'substitute' in role_name:
                return 'committee_substitute'
            else:
                return 'committee_member'
        
        # Delegation roles
        elif role_type == 'delegation':
            if 'chair' in role_name and 'vice' not in role_name:
                return 'delegation_chair'
            elif 'vice' in role_name and 'chair' in role_name:
                return 'delegation_vice_chair'
            elif 'substitute' in role_name:
                return 'delegation_substitute'
            else:
                return 'delegation_member'
        
        return None
    
    def calculate_axis_scores(self, scores: Dict) -> Dict:
        """Calculate axis scores by summing individual metric scores (no double weighting)"""
        axis_scores = {}
        
        # Legislative Production - simple sum of individual scores
        axis_scores['legislative_raw'] = (
            scores['score_reports_rap'] +
            scores['score_reports_shadow'] +
            scores['score_opinions_rap'] +
            scores['score_opinions_shadow'] +
            scores['score_amend']
        )
        
        # Control & Transparency - simple sum of individual scores
        axis_scores['control_raw'] = (
            scores['score_questions'] +
            scores['score_motions'] +
            scores['score_explanations']
        )
        
        # Engagement & Presence - simple sum of individual scores
        axis_scores['engagement_raw'] = (
            scores['score_speeches'] +
            scores['score_votes']
        )
        
        # Institutional Roles
        axis_scores['roles_raw'] = scores['role_score_raw']
        
        return axis_scores
    
    def calculate_final_score(self, axis_scores: Dict) -> float:
        """Calculate final weighted score"""
        return (
            axis_scores['legislative_raw'] * self.axis_weights['legislative_production'] +
            axis_scores['control_raw'] * self.axis_weights['control_transparency'] +
            axis_scores['engagement_raw'] * self.axis_weights['engagement_presence'] +
            axis_scores['roles_raw'] * self.axis_weights['institutional_roles']
        )
    
    def score_all_meps(self, term: int = 10) -> List[Dict]:
        """Score all MEPs and return normalized results"""
        meps_data = self.get_mep_data(term)
        
        if not meps_data:
            return []
        
        # Find max amendments for logarithmic scaling
        max_amendments = max(mep['amendments'] for mep in meps_data)
        
        results = []
        final_scores = []
        
        # Calculate scores for all MEPs
        for mep in meps_data:
            individual_scores = self.calculate_individual_scores(mep, max_amendments)
            axis_scores = self.calculate_axis_scores(individual_scores)
            final_raw = self.calculate_final_score(axis_scores)
            
            result = {
                'mep_id': mep['mep_id'],
                'full_name': mep['full_name'],
                'country': mep['country'],
                'group': mep['group'],
                'final_raw': final_raw,
                **individual_scores,
                **axis_scores
            }
            
            results.append(result)
            final_scores.append(final_raw)
        
        # Normalize to 0-100 scale
        max_final = max(final_scores) if final_scores else 1
        
        for result in results:
            result['final_score'] = 100 * result['final_raw'] / max_final if max_final > 0 else 0
        
        # Sort by final score
        results.sort(key=lambda x: x['final_score'], reverse=True)
        
        # Add rankings
        for i, result in enumerate(results):
            result['rank'] = i + 1
        
        return results
    
    def get_scoring_config(self) -> Dict:
        """Get current scoring configuration"""
        return {
            'axis_weights': self.axis_weights,
            'per_unit_points': self.per_unit_points,
            'caps': self.caps,
            'roles_coefficients': self.roles_coefficients
        }

if __name__ == "__main__":
    # Test the scoring system
    scorer = EPScoringSystem()
    results = scorer.score_all_meps(term=10)
    
    print(f"Scored {len(results)} MEPs")
    print("\nTop 10:")
    for i, mep in enumerate(results[:10]):
        try:
            name = mep['full_name'][:23] if len(mep['full_name']) > 23 else mep['full_name']
            print(f"{i+1:2d}. {name:<25} {mep['final_score']:.1f}")
        except UnicodeEncodeError:
            print(f"{i+1:2d}. [Unicode name] {mep['final_score']:.1f}")
        
    # Export sample results to JSON
    with open('public/data/sample_scoring.json', 'w', encoding='utf-8') as f:
        json.dump(results[:50], f, indent=2, ensure_ascii=False)
