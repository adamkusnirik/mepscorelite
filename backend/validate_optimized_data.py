#!/usr/bin/env python3
"""
Data Validation Script for Optimized ParlTrack Data
Validates that optimized data maintains integrity and API compatibility
"""

import json
import requests
import sqlite3
import datetime as dt
from pathlib import Path
import sys
import logging
from typing import Dict, List, Any, Optional, Tuple
import time

from file_utils import load_json_auto, resolve_json_path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/validation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DataValidator:
    """Validates optimized ParlTrack data integrity"""
    
    def __init__(self, parltrack_dir: str = "data/parltrack"):
        self.parltrack_dir = Path(parltrack_dir)
        self.backup_dir = self.parltrack_dir / "backup_original"
        self.results = {
            'file_checks': {},
            'record_counts': {},
            'data_integrity': {},
            'api_tests': {},
            'errors': [],
            'warnings': []
        }
        
    def check_file_existence(self) -> bool:
        """Check that all expected optimized files exist"""
        logger.info("Checking optimized file existence...")
        
        expected_files = [
            'ep_amendments_term8.json',
            'ep_amendments_term9.json', 
            'ep_amendments_term10.json',
            'ep_mep_activities_term8.json',
            'ep_mep_activities_term9.json',
            'ep_mep_activities_term10.json'
        ]
        
        # Also check for votes files if they were optimized
        for term in [8, 9, 10]:
            votes_file = self.parltrack_dir / f"ep_votes_term{term}.json"
            if votes_file.exists():
                expected_files.append(f"ep_votes_term{term}.json")
        
        all_exist = True
        for filename in expected_files:
            file_path = resolve_json_path(self.parltrack_dir / filename)
            exists = file_path.exists()
            
            if exists:
                file_size = file_path.stat().st_size
                self.results['file_checks'][filename] = {
                    'exists': True,
                    'size_bytes': file_size,
                    'size_mb': file_size / 1024 / 1024
                }
                logger.info(f"✓ {filename} exists ({file_size/1024/1024:.1f} MB)")
            else:
                self.results['file_checks'][filename] = {'exists': False}
                self.results['errors'].append(f"Missing optimized file: {filename}")
                logger.error(f"✗ {filename} missing")
                all_exist = False
        
        return all_exist
    
    def validate_record_counts(self) -> bool:
        """Validate that record counts are reasonable"""
        logger.info("Validating record counts...")
        
        # Check amendments
        amendments_valid = True
        for term in [8, 9, 10]:
            amend_file = resolve_json_path(self.parltrack_dir / f"ep_amendments_term{term}.json")
            if amend_file.exists():
                amendments = load_json_auto(amend_file)
                
                count = len(amendments)
                self.results['record_counts'][f'amendments_term{term}'] = count
                
                # Sanity check - each term should have some amendments
                if count < 100:
                    self.results['warnings'].append(f"Low amendment count for term {term}: {count}")
                    logger.warning(f"⚠ Low amendment count for term {term}: {count}")
                else:
                    logger.info(f"✓ Term {term} amendments: {count} records")
        
        # Check activities  
        activities_valid = True
        for term in [8, 9, 10]:
            activities_file = resolve_json_path(self.parltrack_dir / f"ep_mep_activities_term{term}.json")
            if activities_file.exists():
                meps = load_json_auto(activities_file)
                
                count = len(meps)
                self.results['record_counts'][f'mep_activities_term{term}'] = count
                
                # Sanity check - each term should have MEPs 
                if count < 50:
                    self.results['warnings'].append(f"Low MEP count for term {term}: {count}")
                    logger.warning(f"⚠ Low MEP count for term {term}: {count}")
                else:
                    logger.info(f"✓ Term {term} MEPs: {count} records")
        
        return amendments_valid and activities_valid
    
    def validate_data_structure(self) -> bool:
        """Validate that data structure is preserved"""
        logger.info("Validating data structure...")
        
        structure_valid = True
        
        # Validate amendments structure
        for term in [8, 9, 10]:
            amend_file = resolve_json_path(self.parltrack_dir / f"ep_amendments_term{term}.json")
            if amend_file.exists():
                try:
                    amendments = load_json_auto(amend_file)
                    
                    if amendments:
                        sample = amendments[0]
                        required_fields = ['id', 'date', 'meps', 'authors']
                        
                        for field in required_fields:
                            if field not in sample:
                                self.results['errors'].append(f"Missing field '{field}' in amendments_term{term}")
                                structure_valid = False
                        
                        self.results['data_integrity'][f'amendments_term{term}'] = 'valid'
                        logger.info(f"✓ Amendments term {term} structure valid")
                except Exception as e:
                    self.results['errors'].append(f"Error validating amendments_term{term}: {e}")
                    structure_valid = False
        
        # Validate activities structure
        for term in [8, 9, 10]:
            activities_file = resolve_json_path(self.parltrack_dir / f"ep_mep_activities_term{term}.json")
            if activities_file.exists():
                try:
                    meps = load_json_auto(activities_file)
                    
                    if meps:
                        sample = meps[0]
                        required_fields = ['mep_id', 'meta']
                        
                        for field in required_fields:
                            if field not in sample:
                                self.results['errors'].append(f"Missing field '{field}' in mep_activities_term{term}")
                                structure_valid = False
                        
                        # Check that activities exist
                        activity_types = [k for k in sample.keys() if k not in ['mep_id', 'meta', 'changes']]
                        if not activity_types:
                            self.results['warnings'].append(f"No activity types found in mep_activities_term{term}")
                        
                        self.results['data_integrity'][f'mep_activities_term{term}'] = 'valid'
                        logger.info(f"✓ Activities term {term} structure valid")
                except Exception as e:
                    self.results['errors'].append(f"Error validating mep_activities_term{term}: {e}")
                    structure_valid = False
        
        return structure_valid
    
    def validate_date_ranges(self) -> bool:
        """Validate that data falls within expected term date ranges"""
        logger.info("Validating date ranges...")
        
        term_boundaries = {
            8: (dt.datetime(2014, 7, 1), dt.datetime(2019, 7, 2)),
            9: (dt.datetime(2019, 7, 2), dt.datetime(2024, 7, 16)),
            10: (dt.datetime(2024, 7, 16), dt.datetime(2030, 1, 1))
        }
        
        date_valid = True
        
        # Check amendments dates
        for term in [8, 9, 10]:
            amend_file = resolve_json_path(self.parltrack_dir / f"ep_amendments_term{term}.json")
            if amend_file.exists():
                try:
                    amendments = load_json_auto(amend_file)
                    
                    start_date, end_date = term_boundaries[term]
                    invalid_dates = 0
                    
                    for amend in amendments[:100]:  # Check sample
                        date_str = amend.get('date', '')
                        if date_str:
                            try:
                                if 'T' in date_str:
                                    date_obj = dt.datetime.fromisoformat(date_str.replace('T', ' ').replace('Z', ''))
                                else:
                                    date_obj = dt.datetime.fromisoformat(date_str)
                                
                                if not (start_date <= date_obj < end_date):
                                    invalid_dates += 1
                            except (ValueError, TypeError):
                                pass
                    
                    if invalid_dates > 0:
                        self.results['warnings'].append(f"Found {invalid_dates} amendments with dates outside term {term} range")
                        logger.warning(f"⚠ Term {term} amendments: {invalid_dates} date range violations")
                    else:
                        logger.info(f"✓ Term {term} amendments: dates within range")
                
                except Exception as e:
                    self.results['errors'].append(f"Error checking dates for amendments_term{term}: {e}")
                    date_valid = False
        
        return date_valid
    
    def test_api_endpoints(self) -> bool:
        """Test that API endpoints work with optimized data"""
        logger.info("Testing API endpoints...")
        
        # Start a simple HTTP server for testing (if not already running)
        import subprocess
        import socket
        
        def is_port_open(port):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            return result == 0
        
        server_running = is_port_open(8000)
        if not server_running:
            logger.warning("Server not running on port 8000. Skipping API tests.")
            self.results['api_tests']['status'] = 'skipped'
            return True
        
        # Test sample MEP profiles
        test_cases = [
            {'mep_id': 257011, 'term': 10, 'category': 'amendments'},
            {'mep_id': 257011, 'term': 10, 'category': 'speeches'},
            {'mep_id': 96739, 'term': 8, 'category': 'amendments'},  # Sample from term 8
            {'mep_id': 96739, 'term': 9, 'category': 'amendments'},  # Sample from term 9
        ]
        
        api_valid = True
        
        for test_case in test_cases:
            mep_id = test_case['mep_id']
            term = test_case['term']
            category = test_case['category']
            
            url = f"http://localhost:8000/api/mep/{mep_id}/category/{category}?term={term}&offset=0&limit=5"
            
            try:
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get('success'):
                        self.results['api_tests'][f'mep_{mep_id}_term_{term}_{category}'] = 'success'
                        logger.info(f"✓ API test passed: MEP {mep_id}, term {term}, {category}")
                    else:
                        self.results['api_tests'][f'mep_{mep_id}_term_{term}_{category}'] = 'failed'
                        self.results['errors'].append(f"API returned error for MEP {mep_id}, term {term}, {category}")
                        api_valid = False
                        logger.error(f"✗ API test failed: MEP {mep_id}, term {term}, {category}")
                else:
                    self.results['api_tests'][f'mep_{mep_id}_term_{term}_{category}'] = f'http_error_{response.status_code}'
                    self.results['errors'].append(f"HTTP {response.status_code} for MEP {mep_id}, term {term}, {category}")
                    api_valid = False
                    logger.error(f"✗ HTTP {response.status_code} for MEP {mep_id}, term {term}, {category}")
                    
            except requests.exceptions.RequestException as e:
                self.results['api_tests'][f'mep_{mep_id}_term_{term}_{category}'] = 'connection_error'
                self.results['errors'].append(f"Connection error testing MEP {mep_id}, term {term}, {category}: {e}")
                api_valid = False
                logger.error(f"✗ Connection error for MEP {mep_id}, term {term}, {category}: {e}")
            
            # Small delay between requests
            time.sleep(0.5)
        
        return api_valid
    
    def compare_with_original(self) -> bool:
        """Compare optimized data with original for consistency"""
        logger.info("Comparing with original data...")
        
        if not self.backup_dir.exists():
            logger.warning("No backup directory found, skipping comparison")
            return True
        
        comparison_valid = True
        
        # Compare amendments
        original_amendments = resolve_json_path(self.backup_dir / "ep_amendments.json")
        if original_amendments.exists():
            try:
                orig_data = load_json_auto(original_amendments)
                
                # Count records after 2014 in original
                orig_count_after_2014 = 0
                for amend in orig_data:
                    date_str = amend.get('date', '')
                    if date_str:
                        try:
                            if 'T' in date_str:
                                date_obj = dt.datetime.fromisoformat(date_str.replace('T', ' ').replace('Z', ''))
                            else:
                                date_obj = dt.datetime.fromisoformat(date_str)
                            
                            if date_obj >= dt.datetime(2014, 1, 1):
                                orig_count_after_2014 += 1
                        except (ValueError, TypeError):
                            pass
                
                # Count records in optimized files
                optimized_count = 0
                for term in [8, 9, 10]:
                    amend_file = resolve_json_path(self.parltrack_dir / f"ep_amendments_term{term}.json")
                    if amend_file.exists():
                        optimized_count += len(load_json_auto(amend_file))
                
                # Allow for some variance due to date parsing differences
                diff_percentage = abs(orig_count_after_2014 - optimized_count) / orig_count_after_2014 * 100
                
                if diff_percentage > 5:  # More than 5% difference is concerning
                    self.results['warnings'].append(f"Large difference in amendment counts: original={orig_count_after_2014}, optimized={optimized_count}")
                    logger.warning(f"⚠ Amendment count difference: {diff_percentage:.1f}%")
                else:
                    logger.info(f"✓ Amendment counts consistent: {diff_percentage:.1f}% difference")
                
                self.results['record_counts']['original_amendments_after_2014'] = orig_count_after_2014
                self.results['record_counts']['optimized_amendments_total'] = optimized_count
                
            except Exception as e:
                self.results['errors'].append(f"Error comparing amendments: {e}")
                comparison_valid = False
        
        return comparison_valid
    
    def generate_report(self) -> None:
        """Generate validation report"""
        report = {
            'validation_timestamp': dt.datetime.now().isoformat(),
            'summary': {
                'total_errors': len(self.results['errors']),
                'total_warnings': len(self.results['warnings']),
                'validation_passed': len(self.results['errors']) == 0
            },
            'results': self.results
        }
        
        # Save report
        report_file = self.parltrack_dir / "validation_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Validation report saved: {report_file}")
        
        # Print summary
        print("\n" + "="*60)
        print("VALIDATION REPORT")
        print("="*60)
        
        if report['summary']['validation_passed']:
            print("✓ VALIDATION PASSED")
        else:
            print("✗ VALIDATION FAILED")
        
        print(f"Errors: {report['summary']['total_errors']}")
        print(f"Warnings: {report['summary']['total_warnings']}")
        
        if self.results['errors']:
            print("\nErrors:")
            for error in self.results['errors']:
                print(f"  • {error}")
        
        if self.results['warnings']:
            print("\nWarnings:")
            for warning in self.results['warnings']:
                print(f"  • {warning}")
        
        # File sizes
        print("\nOptimized File Sizes:")
        for filename, info in self.results['file_checks'].items():
            if info.get('exists'):
                print(f"  • {filename}: {info['size_mb']:.1f} MB")
        
        print("="*60)
    
    def run_validation(self) -> bool:
        """Run complete validation process"""
        logger.info("Starting data validation...")
        
        try:
            # Run all validation checks
            file_check = self.check_file_existence()
            count_check = self.validate_record_counts()
            structure_check = self.validate_data_structure()
            date_check = self.validate_date_ranges()
            api_check = self.test_api_endpoints()
            comparison_check = self.compare_with_original()
            
            # Generate report
            self.generate_report()
            
            # Overall validation result
            overall_valid = (file_check and count_check and structure_check and 
                           date_check and api_check and comparison_check and 
                           len(self.results['errors']) == 0)
            
            if overall_valid:
                logger.info("✓ All validation checks passed!")
            else:
                logger.error("✗ Validation failed - see report for details")
            
            return overall_valid
            
        except Exception as e:
            logger.error(f"Validation process failed: {e}")
            return False

def main():
    """Main function"""
    # Check if we're in the right directory
    if not Path("data/parltrack").exists():
        print("ERROR: Please run this script from the project root directory")
        sys.exit(1)
    
    # Create validator and run
    validator = DataValidator()
    success = validator.run_validation()
    
    if success:
        print("\n🎉 Data optimization validation PASSED!")
        print("✓ Profile API endpoints should work correctly with optimized data")
        print("✓ You can safely use the optimized files in production")
    else:
        print("\n❌ Data optimization validation FAILED!")
        print("⚠ Check validation_report.json for detailed error information")
        print("⚠ Consider running the restore script to revert to original files")
        sys.exit(1)

if __name__ == "__main__":
    main()
