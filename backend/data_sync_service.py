#!/usr/bin/env python3
"""
Data Synchronization Service
Ensures frontend data stays in sync with backend scoring changes
"""

import os
import json
import hashlib
import time
from pathlib import Path
from typing import Dict, List, Optional
import logging
from mep_score_scorer import MEPScoreScorer

class DataSyncService:
    def __init__(self, db_path: str = "data/meps.db"):
        self.db_path = db_path
        self.scorer = MEPScoreScorer(db_path)
        self.sync_metadata_file = Path("data/sync_metadata.json")
        self.frontend_data_dir = Path("public/data")
        self.backend_files = [
            "backend/mep_score_scorer.py",
            "backend/scoring_system.py", 
            "backend/build_term_dataset.py"
        ]
        
        # Setup logging
        logging.basicConfig(
            format="%(asctime)s | %(levelname)-8s | %(message)s",
            level=logging.INFO,
            datefmt="%H:%M:%S"
        )
        self.logger = logging.getLogger(__name__)
    
    def get_backend_files_hash(self) -> str:
        """Calculate hash of all backend scoring files to detect changes"""
        combined_content = ""
        
        for file_path in self.backend_files:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    combined_content += f.read()
        
        return hashlib.md5(combined_content.encode()).hexdigest()
    
    def get_database_hash(self) -> str:
        """Calculate hash of database file to detect data changes"""
        if os.path.exists(self.db_path):
            with open(self.db_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        return ""
    
    def load_sync_metadata(self) -> Dict:
        """Load synchronization metadata"""
        if self.sync_metadata_file.exists():
            try:
                with open(self.sync_metadata_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            "last_backend_hash": "",
            "last_database_hash": "",
            "last_sync_timestamp": 0,
            "sync_count": 0,
            "terms_generated": []
        }
    
    def save_sync_metadata(self, metadata: Dict):
        """Save synchronization metadata"""
        with open(self.sync_metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def check_sync_needed(self) -> Dict[str, bool]:
        """Check if synchronization is needed"""
        metadata = self.load_sync_metadata()
        current_backend_hash = self.get_backend_files_hash()
        current_database_hash = self.get_database_hash()
        
        return {
            "backend_changed": current_backend_hash != metadata.get("last_backend_hash", ""),
            "database_changed": current_database_hash != metadata.get("last_database_hash", ""),
            "never_synced": metadata.get("sync_count", 0) == 0,
            "current_backend_hash": current_backend_hash,
            "current_database_hash": current_database_hash
        }
    
    def regenerate_term_dataset(self, term: int) -> bool:
        """Regenerate dataset for a specific term"""
        try:
            self.logger.info(f"Regenerating dataset for term {term}")
            
            # Calculate new scores
            results = self.scorer.score_all_meps(term)
            
            if not results:
                self.logger.warning(f"No data found for term {term}")
                return False
            
            # Create dataset structure
            dataset = {
                "meps": results,
                "averages": self._calculate_averages(results),
                "metadata": {
                    "term": term,
                    "generated_at": time.time(),
                    "total_meps": len(results),
                    "backend_hash": self.get_backend_files_hash(),
                    "database_hash": self.get_database_hash()
                }
            }
            
            # Save dataset
            output_file = self.frontend_data_dir / f"term{term}_dataset.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(dataset, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Generated {output_file} with {len(results)} MEPs")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to regenerate term {term} dataset: {e}")
            return False
    
    def _calculate_averages(self, meps_data: List[Dict]) -> Dict:
        """Calculate averages for comparison purposes"""
        if not meps_data:
            return {"ep": {}, "groups": {}, "countries": {}}
        
        # Activity fields to calculate averages for
        activity_fields = [
            'speeches', 'explanations', 'amendments', 'questions_written',
            'reports_rapporteur', 'reports_shadow', 'opinions_rapporteur', 
            'opinions_shadow', 'attendance_rate', 'final_score'
        ]
        
        averages = {"ep": {}, "groups": {}, "countries": {}}
        
        # EP-wide averages
        for field in activity_fields:
            values = [mep.get(field, 0) for mep in meps_data if mep.get(field) is not None]
            averages["ep"][field] = sum(values) / len(values) if values else 0
        
        # Group averages
        groups = set(mep.get('group') for mep in meps_data if mep.get('group'))
        for group in groups:
            group_meps = [mep for mep in meps_data if mep.get('group') == group]
            averages["groups"][group] = {}
            
            for field in activity_fields:
                values = [mep.get(field, 0) for mep in group_meps if mep.get(field) is not None]
                averages["groups"][group][field] = sum(values) / len(values) if values else 0
        
        # Country averages
        countries = set(mep.get('country') for mep in meps_data if mep.get('country'))
        for country in countries:
            country_meps = [mep for mep in meps_data if mep.get('country') == country]
            averages["countries"][country] = {}
            
            for field in activity_fields:
                values = [mep.get(field, 0) for mep in country_meps if mep.get(field) is not None]
                averages["countries"][country][field] = sum(values) / len(values) if values else 0
        
        return averages
    
    def full_sync(self) -> bool:
        """Perform full synchronization of all datasets"""
        self.logger.info("Starting full synchronization...")
        
        sync_status = self.check_sync_needed()
        
        if not any([sync_status["backend_changed"], sync_status["database_changed"], sync_status["never_synced"]]):
            self.logger.info("No synchronization needed - all data is up to date")
            return True
        
        # Regenerate datasets for all available terms
        terms_to_sync = [8, 9, 10]  # Known terms
        successful_terms = []
        
        for term in terms_to_sync:
            if self.regenerate_term_dataset(term):
                successful_terms.append(term)
        
        if successful_terms:
            # Update metadata
            metadata = self.load_sync_metadata()
            metadata.update({
                "last_backend_hash": sync_status["current_backend_hash"],
                "last_database_hash": sync_status["current_database_hash"],
                "last_sync_timestamp": time.time(),
                "sync_count": metadata.get("sync_count", 0) + 1,
                "terms_generated": successful_terms
            })
            self.save_sync_metadata(metadata)
            
            self.logger.info(f"Synchronization completed successfully for terms: {successful_terms}")
            return True
        else:
            self.logger.error("Synchronization failed - no terms were successfully generated")
            return False
    
    def validate_dataset_consistency(self, term: int) -> Dict[str, bool]:
        """Validate that frontend dataset matches backend calculation"""
        try:
            # Load frontend dataset
            dataset_file = self.frontend_data_dir / f"term{term}_dataset.json"
            if not dataset_file.exists():
                return {"exists": False, "consistent": False}
            
            with open(dataset_file, 'r', encoding='utf-8') as f:
                frontend_data = json.load(f)
            
            # Get fresh backend calculation
            backend_results = self.scorer.score_all_meps(term)
            
            if not backend_results:
                return {"exists": True, "consistent": False, "error": "No backend data"}
            
            # Compare a sample of results (first 5 MEPs)
            frontend_meps = frontend_data.get("meps", [])[:5]
            backend_sample = backend_results[:5]
            
            inconsistencies = []
            for i, (frontend_mep, backend_mep) in enumerate(zip(frontend_meps, backend_sample)):
                if frontend_mep.get("final_score") != backend_mep.get("final_score"):
                    inconsistencies.append({
                        "mep": frontend_mep.get("full_name"),
                        "frontend_score": frontend_mep.get("final_score"),
                        "backend_score": backend_mep.get("final_score")
                    })
            
            return {
                "exists": True,
                "consistent": len(inconsistencies) == 0,
                "inconsistencies": inconsistencies,
                "metadata": frontend_data.get("metadata", {})
            }
            
        except Exception as e:
            return {"exists": True, "consistent": False, "error": str(e)}

if __name__ == "__main__":
    sync_service = DataSyncService()
    
    # Check if sync is needed
    sync_status = sync_service.check_sync_needed()
    
    print("=== Data Synchronization Status ===")
    print(f"Backend files changed: {sync_status['backend_changed']}")
    print(f"Database changed: {sync_status['database_changed']}")
    print(f"Never synced: {sync_status['never_synced']}")
    
    if any([sync_status["backend_changed"], sync_status["database_changed"], sync_status["never_synced"]]):
        print("\n=== Performing Full Synchronization ===")
        success = sync_service.full_sync()
        print(f"Synchronization {'successful' if success else 'failed'}")
    
    # Validate datasets
    print("\n=== Dataset Validation ===")
    for term in [8, 9, 10]:
        validation = sync_service.validate_dataset_consistency(term)
        print(f"Term {term}: {'✓' if validation.get('consistent') else '✗'} {'Consistent' if validation.get('consistent') else 'Inconsistent'}")
        if not validation.get('consistent') and 'inconsistencies' in validation:
            for issue in validation['inconsistencies'][:3]:  # Show first 3 issues
                print(f"  - {issue['mep']}: Frontend={issue['frontend_score']}, Backend={issue['backend_score']}")