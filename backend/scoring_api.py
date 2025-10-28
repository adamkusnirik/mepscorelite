#!/usr/bin/env python3
"""
API endpoint for the scoring system
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from functools import lru_cache
from pathlib import Path

from mep_score_scorer import MEPScoreScorer
from file_utils import load_combined_dataset

app = Flask(__name__)
CORS(app)

scorer = MEPScoreScorer()
PARLTRACK_DIR = Path("../data/parltrack")
TERM_FALLBACKS = [8, 9, 10]

@lru_cache(maxsize=1)
def get_activities_data():
    """Load (and cache) activities data across all terms."""
    return load_combined_dataset(
        PARLTRACK_DIR / "ep_mep_activities.json",
        [PARLTRACK_DIR / f"ep_mep_activities_term{t}.json" for t in TERM_FALLBACKS],
    )

@lru_cache(maxsize=1)
def get_amendments_data():
    """Load (and cache) amendments data across all terms."""
    return load_combined_dataset(
        PARLTRACK_DIR / "ep_amendments.json",
        [PARLTRACK_DIR / f"ep_amendments_term{t}.json" for t in TERM_FALLBACKS],
    )

@app.route('/api/score', methods=['GET', 'POST'])
def get_scores():
    """Get MEP scores using MEP Ranking methodology"""
    try:
        term = int(request.args.get('term', 10))
        
        # MEPScoreScorer doesn't support custom weights - it follows the fixed methodology
        results = scorer.score_all_meps(term)
        
        return jsonify({
            'success': True,
            'count': len(results),
            'data': results,
            'methodology': 'MEP Ranking (October 2017) with term-specific ranges'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/scoring-config', methods=['GET'])
def get_scoring_config():
    """Get current scoring configuration"""
    return jsonify({
        'methodology': 'MEP Ranking (October 2017)',
        'features': [
            'Term-specific activity ranges',
            'Reports scoring (4.0/1.0/1.0/0.5 points)',
            'Range-based statements scoring',
            'Role multipliers (25% for VP, 15% for Committee Chair, etc.)',
            'Attendance penalties (75%/55% thresholds)'
        ]
    })

@app.route('/api/scoring-config', methods=['POST'])
def update_scoring_config():
    """MEP Ranking methodology is fixed - no custom configuration allowed"""
    return jsonify({
        'success': False,
        'error': 'MEP Ranking methodology uses fixed parameters. Custom weights not supported.'
    }), 400

@app.route('/api/mep/<int:mep_id>/category/<category>', methods=['GET'])
def get_mep_category_details(mep_id, category):
    """Get detailed data for a specific MEP category"""
    try:
        term = int(request.args.get('term', 10))
        offset = int(request.args.get('offset', 0))
        limit = int(request.args.get('limit', 15))
        
        # Load ParlTrack data based on category
        if category == 'speeches':
            # Load speeches from activities data
            activities_data = get_activities_data()
            # Find MEP's speeches
            mep_data = next((mep for mep in activities_data if mep.get('mep_id') == mep_id), None)
            if not mep_data:
                return jsonify({'success': False, 'error': 'MEP not found'}), 404
            
            speeches = mep_data.get('CRE', [])
            # Filter speeches (excluding explanations of vote and one-minute speeches)
            filtered_speeches = [
                speech for speech in speeches 
                if 'Explanations of vote' not in speech.get('title', '') 
                and 'One-minute speeches' not in speech.get('title', '')
                and speech.get('term', 0) == term
            ]
            
            # Apply pagination
            paginated_data = filtered_speeches[offset:offset + limit]
            
            return jsonify({
                'success': True,
                'category': 'speeches',
                'mep_id': mep_id,
                'term': term,
                'total_count': len(filtered_speeches),
                'offset': offset,
                'limit': limit,
                'has_more': len(filtered_speeches) > offset + limit,
                'data': paginated_data
            })
        
        elif category == 'amendments':
            # Load amendments from amendments data
            amendments_data = get_amendments_data()
            # Find MEP's amendments and filter by term
            mep_amendments = []
            for amend in amendments_data:
                if mep_id in amend.get('meps', []):
                    # Check if amendment date is in the correct term range
                    amend_date = amend.get('date', '')
                    if amend_date:
                        year = int(amend_date[:4]) if amend_date[:4].isdigit() else 0
                        # Term 10: 2019-2024, Term 9: 2014-2019, etc.
                        if term == 10 and 2019 <= year <= 2024:
                            mep_amendments.append(amend)
                        elif term == 9 and 2014 <= year <= 2019:
                            mep_amendments.append(amend)
                        elif term == 8 and 2009 <= year <= 2014:
                            mep_amendments.append(amend)
            
            # Sort by date (newest first)
            mep_amendments.sort(key=lambda x: x.get('date', ''), reverse=True)
            
            # Apply pagination
            paginated_data = mep_amendments[offset:offset + limit]
            
            return jsonify({
                'success': True,
                'category': 'amendments',
                'mep_id': mep_id,
                'term': term,
                'total_count': len(mep_amendments),
                'offset': offset,
                'limit': limit,
                'has_more': len(mep_amendments) > offset + limit,
                'data': paginated_data
            })
        
        elif category in ['questions', 'questions_written', 'questions_oral', 'motions', 'reports_rapporteur',
                          'reports_shadow', 'opinions_rapporteur', 'opinions_shadow', 'explanations']:
            # Handle different activity types from activities data
            activities_data = get_activities_data()
            mep_data = next((mep for mep in activities_data if mep.get('mep_id') == mep_id), None)
            if not mep_data:
                return jsonify({'success': False, 'error': 'MEP not found'}), 404
            
            if category in ['questions', 'questions_written']:
                # Handle written questions
                questions = mep_data.get('WQ', [])
                filtered_data = [q for q in questions if q.get('term', 0) == term]
                # Sort by date (newest first)
                filtered_data.sort(key=lambda x: x.get('date', ''), reverse=True)

            elif category == 'questions_oral':
                oral_questions = mep_data.get('OQ', [])
                filtered_data = [q for q in oral_questions if q.get('term', 0) == term]
                filtered_data.sort(key=lambda x: x.get('date', ''), reverse=True)
                
            elif category == 'motions':
                # Handle motions - consider multiple activity buckets
                motions = (
                    mep_data.get('MOTION', []) +
                    mep_data.get('IMOTION', []) +
                    mep_data.get('WDECL', [])
                )
                filtered_data = [m for m in motions if m.get('term', 0) == term]
                # Sort by date (newest first) 
                filtered_data.sort(key=lambda x: x.get('Date opened', x.get('date', '')), reverse=True)
                
            elif category == 'explanations':
                # Handle explanations of vote
                speeches = mep_data.get('CRE', [])
                filtered_data = [
                    speech for speech in speeches 
                    if 'Explanations of vote' in speech.get('title', '')
                    and speech.get('term', 0) == term
                ]
                # Sort by date (newest first)
                filtered_data.sort(key=lambda x: x.get('date', ''), reverse=True)
                
            else:
                key_map = {
                    'reports_rapporteur': 'REPORT',
                    'reports_shadow': 'REPORT-SHADOW',
                    'opinions_rapporteur': 'COMPARL',
                    'opinions_shadow': 'COMPARL-SHADOW',
                }
                activity_key = key_map.get(category)
                items = mep_data.get(activity_key, []) if activity_key else []
                filtered_data = [item for item in items if item.get('term', 0) == term]
                filtered_data.sort(key=lambda x: x.get('date', ''), reverse=True)
            
            # Apply pagination
            paginated_data = filtered_data[offset:offset + limit]
            
            return jsonify({
                'success': True,
                'category': category,
                'mep_id': mep_id,
                'term': term,
                'total_count': len(filtered_data),
                'offset': offset,
                'limit': limit,
                'has_more': len(filtered_data) > offset + limit,
                'data': paginated_data
            })
        
        else:
            return jsonify({'success': False, 'error': 'Unknown category'}), 400
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Simple health check endpoint."""
    try:
        # Ensure cached datasets are reachable
        get_activities_data()
        get_amendments_data()
        return jsonify({'success': True, 'status': 'ok'})
    except Exception as exc:
        return jsonify({'success': False, 'status': 'error', 'error': str(exc)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
