#!/usr/bin/env python3
"""
ParlTrack Data Optimization Script
Optimizes large ParlTrack JSON files by:
1. Removing data entries before 2014-01-01
2. Splitting large files by EP terms (8th: 2014-2019, 9th: 2019-2024, 10th: 2024+)
3. Maintaining exact data structure for API compatibility
4. Generating optimization metadata and logs
"""

import json
import os
import shutil
import datetime as dt
from pathlib import Path
import sys
import logging
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/optimization.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# EP Term boundaries
TERM_BOUNDARIES = {
    8: {
        'start': dt.datetime(2014, 7, 1),
        'end': dt.datetime(2019, 7, 2),
        'name': '8th'
    },
    9: {
        'start': dt.datetime(2019, 7, 2), 
        'end': dt.datetime(2024, 7, 16),
        'name': '9th'
    },
    10: {
        'start': dt.datetime(2024, 7, 16),
        'end': dt.datetime(2030, 1, 1),  # Future end date
        'name': '10th'
    }
}

CUTOFF_DATE = dt.datetime(2014, 1, 1)
LARGE_FILE_THRESHOLD = 150 * 1024 * 1024  # 150MB in bytes

class ParlTrackOptimizer:
    """Main class for optimizing ParlTrack data files"""
    
    def __init__(self, parltrack_dir: str = "data/parltrack"):
        self.parltrack_dir = Path(parltrack_dir)
        self.backup_dir = self.parltrack_dir / "backup_original"
        self.optimized_dir = self.parltrack_dir / "optimized"
        self.stats = {
            'original_files': {},
            'optimized_files': {},
            'records_removed': {},
            'records_by_term': {},
            'file_sizes': {}
        }
        
    def create_backup(self) -> None:
        """Create backup of original files"""
        logger.info("Creating backup of original files...")
        self.backup_dir.mkdir(exist_ok=True)
        
        for json_file in self.parltrack_dir.glob("*.json"):
            if json_file.name.startswith(('ep_amendments', 'ep_mep_activities', 'ep_votes')):
                backup_path = self.backup_dir / json_file.name
                if not backup_path.exists():
                    logger.info(f"Backing up {json_file.name}")
                    shutil.copy2(json_file, backup_path)
                    self.stats['original_files'][json_file.name] = json_file.stat().st_size
                else:
                    logger.info(f"Backup already exists for {json_file.name}")
    
    def parse_date(self, date_str: str) -> Optional[dt.datetime]:
        """Parse various date formats from ParlTrack data"""
        if not date_str:
            return None
            
        try:
            # Handle ISO format with T and Z
            if 'T' in date_str:
                clean_date = date_str.replace('T', ' ').replace('Z', '')
                return dt.datetime.fromisoformat(clean_date)
            else:
                return dt.datetime.fromisoformat(date_str)
        except (ValueError, TypeError):
            # Try other common formats
            for fmt in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S']:
                try:
                    return dt.datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            logger.warning(f"Could not parse date: {date_str}")
            return None
    
    def get_term_for_date(self, date_obj: dt.datetime) -> Optional[int]:
        """Determine EP term for a given date"""
        for term, boundaries in TERM_BOUNDARIES.items():
            if boundaries['start'] <= date_obj < boundaries['end']:
                return term
        return None
    
    def optimize_amendments(self) -> None:
        """Optimize ep_amendments.json file"""
        amendments_file = self.parltrack_dir / "ep_amendments.json"
        
        if not amendments_file.exists():
            logger.warning("ep_amendments.json not found")
            return
            
        logger.info("Optimizing amendments data...")
        
        with open(amendments_file, 'r', encoding='utf-8') as f:
            all_amendments = json.load(f)
        
        logger.info(f"Original amendments count: {len(all_amendments)}")
        
        # Split by terms
        amendments_by_term = {8: [], 9: [], 10: []}
        removed_count = 0
        
        for amend in all_amendments:
            date_str = amend.get('date', '')
            date_obj = self.parse_date(date_str)
            
            if not date_obj:
                continue
                
            # Remove data before cutoff
            if date_obj < CUTOFF_DATE:
                removed_count += 1
                continue
                
            term = self.get_term_for_date(date_obj)
            if term and term in amendments_by_term:
                amendments_by_term[term].append(amend)
        
        # Save optimized files
        for term, amendments in amendments_by_term.items():
            if amendments:
                output_file = self.parltrack_dir / f"ep_amendments_term{term}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(amendments, f, ensure_ascii=False, separators=(',', ':'))
                
                file_size = output_file.stat().st_size
                self.stats['optimized_files'][f"ep_amendments_term{term}.json"] = file_size
                self.stats['records_by_term'][f"amendments_term{term}"] = len(amendments)
                
                logger.info(f"Created ep_amendments_term{term}.json with {len(amendments)} records ({file_size/1024/1024:.1f} MB)")
        
        self.stats['records_removed']['amendments'] = removed_count
        logger.info(f"Removed {removed_count} amendments before {CUTOFF_DATE.strftime('%Y-%m-%d')}")
    
    def optimize_activities(self) -> None:
        """Optimize ep_mep_activities.json file"""
        activities_file = self.parltrack_dir / "ep_mep_activities.json"
        
        if not activities_file.exists():
            logger.warning("ep_mep_activities.json not found")
            return
            
        logger.info("Optimizing activities data...")
        
        with open(activities_file, 'r', encoding='utf-8') as f:
            all_meps = json.load(f)
        
        logger.info(f"Original MEP count: {len(all_meps)}")
        
        # Split by terms
        meps_by_term = {8: [], 9: [], 10: []}
        removed_activities_count = 0
        
        for mep_data in all_meps:
            # Process each MEP's activities by term
            for term in [8, 9, 10]:
                term_boundaries = TERM_BOUNDARIES[term]
                filtered_mep_data = {
                    'mep_id': mep_data.get('mep_id'),
                    'meta': mep_data.get('meta', {}),
                    'changes': mep_data.get('changes', {})
                }
                
                has_activities_in_term = False
                
                # Process each activity type
                for activity_type, activities in mep_data.items():
                    if activity_type in ['mep_id', 'meta', 'changes']:
                        continue
                        
                    if not isinstance(activities, list):
                        continue
                    
                    filtered_activities = []
                    
                    for activity in activities:
                        date_str = activity.get('date', '')
                        date_obj = self.parse_date(date_str)
                        
                        if not date_obj:
                            continue
                            
                        # Remove data before cutoff
                        if date_obj < CUTOFF_DATE:
                            removed_activities_count += 1
                            continue
                            
                        # Check if activity belongs to this term
                        if term_boundaries['start'] <= date_obj < term_boundaries['end']:
                            filtered_activities.append(activity)
                            has_activities_in_term = True
                    
                    if filtered_activities:
                        filtered_mep_data[activity_type] = filtered_activities
                
                # Only add MEP to term if they have activities in that term
                if has_activities_in_term:
                    meps_by_term[term].append(filtered_mep_data)
        
        # Save optimized files
        for term, mep_list in meps_by_term.items():
            if mep_list:
                output_file = self.parltrack_dir / f"ep_mep_activities_term{term}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(mep_list, f, ensure_ascii=False, separators=(',', ':'))
                
                file_size = output_file.stat().st_size
                self.stats['optimized_files'][f"ep_mep_activities_term{term}.json"] = file_size
                self.stats['records_by_term'][f"mep_activities_term{term}"] = len(mep_list)
                
                logger.info(f"Created ep_mep_activities_term{term}.json with {len(mep_list)} MEPs ({file_size/1024/1024:.1f} MB)")
        
        self.stats['records_removed']['activities'] = removed_activities_count
        logger.info(f"Removed {removed_activities_count} activities before {CUTOFF_DATE.strftime('%Y-%m-%d')}")
    
    def optimize_votes(self) -> None:
        """Optimize ep_votes.json file if it's large"""
        votes_file = self.parltrack_dir / "ep_votes.json"
        
        if not votes_file.exists():
            logger.warning("ep_votes.json not found")
            return
        
        file_size = votes_file.stat().st_size
        if file_size < LARGE_FILE_THRESHOLD:
            logger.info(f"ep_votes.json ({file_size/1024/1024:.1f} MB) is below threshold, skipping optimization")
            return
            
        logger.info("Optimizing votes data...")
        
        with open(votes_file, 'r', encoding='utf-8') as f:
            all_votes = json.load(f)
        
        logger.info(f"Original votes count: {len(all_votes)}")
        
        # Split by terms
        votes_by_term = {8: [], 9: [], 10: []}
        removed_count = 0
        
        for vote in all_votes:
            date_str = vote.get('date', vote.get('ts', ''))
            date_obj = self.parse_date(date_str)
            
            if not date_obj:
                continue
                
            # Remove data before cutoff
            if date_obj < CUTOFF_DATE:
                removed_count += 1
                continue
                
            term = self.get_term_for_date(date_obj)
            if term and term in votes_by_term:
                votes_by_term[term].append(vote)
        
        # Save optimized files
        for term, votes in votes_by_term.items():
            if votes:
                output_file = self.parltrack_dir / f"ep_votes_term{term}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(votes, f, ensure_ascii=False, separators=(',', ':'))
                
                file_size = output_file.stat().st_size
                self.stats['optimized_files'][f"ep_votes_term{term}.json"] = file_size
                self.stats['records_by_term'][f"votes_term{term}"] = len(votes)
                
                logger.info(f"Created ep_votes_term{term}.json with {len(votes)} records ({file_size/1024/1024:.1f} MB)")
        
        self.stats['records_removed']['votes'] = removed_count
        logger.info(f"Removed {removed_count} votes before {CUTOFF_DATE.strftime('%Y-%m-%d')}")
    
    def generate_metadata(self) -> None:
        """Generate optimization metadata and statistics"""
        metadata = {
            'optimization_timestamp': dt.datetime.now().isoformat(),
            'cutoff_date': CUTOFF_DATE.isoformat(),
            'term_boundaries': {str(k): {
                'start': v['start'].isoformat(),
                'end': v['end'].isoformat(),
                'name': v['name']
            } for k, v in TERM_BOUNDARIES.items()},
            'statistics': self.stats,
            'file_mapping': {
                'amendments': {
                    'original': 'ep_amendments.json',
                    'optimized': ['ep_amendments_term8.json', 'ep_amendments_term9.json', 'ep_amendments_term10.json']
                },
                'activities': {
                    'original': 'ep_mep_activities.json',
                    'optimized': ['ep_mep_activities_term8.json', 'ep_mep_activities_term9.json', 'ep_mep_activities_term10.json']
                },
                'votes': {
                    'original': 'ep_votes.json',
                    'optimized': ['ep_votes_term8.json', 'ep_votes_term9.json', 'ep_votes_term10.json']
                }
            }
        }
        
        # Calculate total space savings
        original_total = sum(self.stats['original_files'].values())
        optimized_total = sum(self.stats['optimized_files'].values())
        savings = original_total - optimized_total
        
        metadata['space_savings'] = {
            'original_total_bytes': original_total,
            'optimized_total_bytes': optimized_total,
            'savings_bytes': savings,
            'savings_percentage': (savings / original_total * 100) if original_total > 0 else 0,
            'original_total_mb': original_total / 1024 / 1024,
            'optimized_total_mb': optimized_total / 1024 / 1024,
            'savings_mb': savings / 1024 / 1024
        }
        
        # Save metadata
        metadata_file = self.parltrack_dir / "optimization_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Generated metadata file: {metadata_file}")
        logger.info(f"Space savings: {savings/1024/1024:.1f} MB ({metadata['space_savings']['savings_percentage']:.1f}%)")
    
    def create_restore_script(self) -> None:
        """Create script to restore original files"""
        restore_script = """#!/usr/bin/env python3
\"\"\"
Restore script for ParlTrack data optimization
Restores original files from backup directory
\"\"\"

import shutil
from pathlib import Path
import sys

def restore_original_files():
    parltrack_dir = Path("data/parltrack")
    backup_dir = parltrack_dir / "backup_original"
    
    if not backup_dir.exists():
        print("ERROR: Backup directory not found!")
        sys.exit(1)
    
    # Restore original files
    for backup_file in backup_dir.glob("*.json"):
        original_path = parltrack_dir / backup_file.name
        print(f"Restoring {backup_file.name}...")
        shutil.copy2(backup_file, original_path)
    
    # Remove optimized files
    for optimized_file in parltrack_dir.glob("*_term*.json"):
        print(f"Removing optimized file {optimized_file.name}...")
        optimized_file.unlink()
    
    # Remove metadata
    metadata_file = parltrack_dir / "optimization_metadata.json"
    if metadata_file.exists():
        metadata_file.unlink()
        print("Removed optimization metadata")
    
    print("Original files restored successfully!")

if __name__ == "__main__":
    restore_original_files()
"""
        
        restore_file = self.parltrack_dir / "restore_original_data.py"
        with open(restore_file, 'w', encoding='utf-8') as f:
            f.write(restore_script)
        
        # Make executable on Unix systems
        try:
            restore_file.chmod(0o755)
        except:
            pass
        
        logger.info(f"Created restore script: {restore_file}")
    
    def optimize_all(self) -> None:
        """Run complete optimization process"""
        logger.info("Starting ParlTrack data optimization...")
        logger.info(f"Cutoff date: {CUTOFF_DATE.strftime('%Y-%m-%d')}")
        logger.info(f"Large file threshold: {LARGE_FILE_THRESHOLD/1024/1024:.1f} MB")
        
        try:
            # Create backup
            self.create_backup()
            
            # Optimize each file type
            self.optimize_amendments()
            self.optimize_activities() 
            self.optimize_votes()
            
            # Generate metadata and restore script
            self.generate_metadata()
            self.create_restore_script()
            
            logger.info("Optimization completed successfully!")
            
        except Exception as e:
            logger.error(f"Optimization failed: {e}")
            raise

def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] == '--restore':
        # Run restore process
        exec(open('data/parltrack/restore_original_data.py').read())
        return
    
    # Check if we're in the right directory
    if not Path("data/parltrack").exists():
        print("ERROR: Please run this script from the project root directory")
        sys.exit(1)
    
    # Create optimizer and run
    optimizer = ParlTrackOptimizer()
    optimizer.optimize_all()
    
    print("\n" + "="*60)
    print("OPTIMIZATION COMPLETE")
    print("="*60)
    print("Next steps:")
    print("1. Update serve.py and production_serve.py to use optimized files")
    print("2. Run validation script: python backend/validate_optimized_data.py")  
    print("3. Test profile pages to ensure API endpoints work correctly")
    print("4. To restore original files: python backend/optimize_parltrack_data.py --restore")
    print("="*60)

if __name__ == "__main__":
    main()