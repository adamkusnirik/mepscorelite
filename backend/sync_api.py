#!/usr/bin/env python3
"""
Synchronization API
Provides real-time data synchronization endpoints
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from data_sync_service import DataSyncService
import logging

app = Flask(__name__)
CORS(app)

sync_service = DataSyncService()

@app.route('/api/sync/status', methods=['GET'])
def get_sync_status():
    """Get current synchronization status"""
    try:
        sync_status = sync_service.check_sync_needed()
        metadata = sync_service.load_sync_metadata()
        
        return jsonify({
            'success': True,
            'sync_needed': any([
                sync_status['backend_changed'],
                sync_status['database_changed'], 
                sync_status['never_synced']
            ]),
            'backend_changed': sync_status['backend_changed'],
            'database_changed': sync_status['database_changed'],
            'never_synced': sync_status['never_synced'],
            'last_sync': metadata.get('last_sync_timestamp', 0),
            'sync_count': metadata.get('sync_count', 0),
            'terms_available': metadata.get('terms_generated', [])
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/sync/perform', methods=['POST'])
def perform_sync():
    """Perform full synchronization"""
    try:
        success = sync_service.full_sync()
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Synchronization completed successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Synchronization failed'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/sync/validate/<int:term>', methods=['GET'])
def validate_term_data(term):
    """Validate consistency of a specific term's data"""
    try:
        validation = sync_service.validate_dataset_consistency(term)
        
        return jsonify({
            'success': True,
            'term': term,
            'consistent': validation.get('consistent', False),
            'exists': validation.get('exists', False),
            'inconsistencies': validation.get('inconsistencies', []),
            'metadata': validation.get('metadata', {})
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/sync/regenerate/<int:term>', methods=['POST']) 
def regenerate_term(term):
    """Regenerate dataset for a specific term"""
    try:
        success = sync_service.regenerate_term_dataset(term)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Term {term} dataset regenerated successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to regenerate term {term} dataset'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5002)