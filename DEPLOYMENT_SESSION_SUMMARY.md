# AWS Lightsail Deployment & Fixes - Session Summary

**Date**: August 15, 2025  
**Objective**: Deploy MEP Score app to AWS Lightsail and fix data loading issues  
**Status**: ✅ COMPLETED - All fixes deployed and backed up to GitHub

## Key Issues Fixed

### 1. Speech Data Loading ("Detailed Data Not Available")
- **Problem**: Missing database and activity files on server
- **Fix**: Copied `meps.db` and activity JSON files to `/var/www/mepscore/data/`

### 2. Amendment JSON Parsing Errors  
- **Problem**: Server crashing on 86MB amendment files (memory exhaustion)
- **Fix**: Implemented streaming JSON processing using `ijson` library in `serve.py`

### 3. Terms 8/9 Activity Data Missing
- **Problem**: File path mismatches for legacy term data
- **Fix**: Updated file paths to use term-specific directories (`8th term/`, `9th term/`)

### 4. Incorrect Activity Dates (All showing Nov 22, 2016)
- **Problem**: Corrupted date fields in Term 8 data
- **Fix**: Added regex date extraction from parliamentary references:
  ```python
  patterns = [
      r'CRE-PROV\((\d{4})\)(\d{2})-(\d{2})',  # CRE-PROV(YYYY)MM-DD
      r'CRE-REV\((\d{4})\)(\d{2})-(\d{2})',   # CRE-REV(YYYY)MM-DD  
      r'CRE\((\d{4})\)(\d{2})-(\d{2})'        # CRE(YYYY)MM-DD
  ]
  ```

### 5. Load More Pagination Date Issues
- **Problem**: Subsequent pages showed wrong dates
- **Fix**: Extended regex patterns to handle all parliamentary reference formats

### 6. Frontend Static Mode Detection
- **Problem**: API calls failing when accessing via public IP
- **Fix**: Modified `profile.js` static detection logic

## Technical Implementation

### Streaming JSON Processing (`serve.py`)
```python
def get_amendments_detailed(mep_id, term, offset=0, limit=5):
    # Stream large JSON files instead of loading into memory
    for amendment in ijson.items(file, 'item'):
        if amendment.get('mep_id') == mep_id:
            # Process incrementally
```

### Date Extraction System
```python
def extract_date_from_reference(reference):
    patterns = [
        r'CRE-PROV\((\d{4})\)(\d{2})-(\d{2})',
        r'CRE-REV\((\d{4})\)(\d{2})-(\d{2})', 
        r'CRE\((\d{4})\)(\d{2})-(\d{2})'
    ]
    # Extract real dates from parliamentary reference strings
```

## Files Modified
- `/var/www/mepscore/serve.py` - Main server with streaming & date fixes
- `/var/www/mepscore/public/js/profile.js` - Frontend static mode fix
- Data file reorganization in `/var/www/mepscore/data/parltrack/`

## Deployment Steps Completed
1. ✅ SSH connection to AWS Lightsail (108.128.29.141)
2. ✅ Git clone from repository 
3. ✅ Installed dependencies (`ijson` for streaming)
4. ✅ Fixed all data loading issues
5. ✅ Committed and pushed all fixes to GitHub
6. ✅ Server running successfully with all functionality

## Verified Working
- ✅ Speech details loading for all MEPs
- ✅ Amendment details with pagination
- ✅ Chronological sorting across all pages
- ✅ Terms 8, 9, 10 activity data loading
- ✅ Correct date extraction and display
- ✅ Load More functionality working properly

## Final Status
Server deployed at AWS Lightsail with all improvements backed up to GitHub. All MEP profile functionality working correctly across all parliamentary terms.

**GitHub Commit**: `87be585` - "Fix production API server configuration and add diagnostic tools"