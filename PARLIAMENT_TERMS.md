# European Parliament Terms

This document defines the official European Parliament legislative term dates used throughout the MEP Ranking application.

## Term Definitions

| Term | Term Duration | Start Date | End Date |
|------|---------------|------------|----------|
| 8th  | July 1, 2014 – July 1, 2019 | 2014-07-01 | 2019-07-01 |
| 9th  | July 2, 2019 – July 15, 2024 | 2019-07-02 | 2024-07-15 |
| 10th | July 16, 2024 – 2029 (expected) | 2024-07-16 | 2029-07-15* |

*Expected end date for 10th term

## Implementation Notes

### Date Filtering Logic

The application uses these exact date boundaries for filtering parliamentary activities (amendments, speeches, reports, etc.) by term:

- **Term 8**: `2014-07-01 <= date < 2019-07-02`
- **Term 9**: `2019-07-02 <= date < 2024-07-16` 
- **Term 10**: `2024-07-16 <= date`

### Code References

These term dates are implemented consistently across:

1. **Database Ingestion** (`backend/ingest_parltrack.py`)
   ```python
   def get_term_for_date(date_str):
       if dt.datetime(2014, 7, 1) <= date < dt.datetime(2019, 7, 2):
           return 8
       elif dt.datetime(2019, 7, 2) <= date < dt.datetime(2024, 7, 16):
           return 9
       elif dt.datetime(2024, 7, 16) <= date:
           return 10
   ```

2. **Data Processing** (`backend/process_data.py`)
   ```python
   TERM_DATES = {
       '8': ('2014-07-01', '2019-07-01'),
       '9': ('2019-07-02', '2024-07-15'),
       '10': ('2024-07-16', '2029-07-15'),
   }
   ```

3. **API Server** (`run_api_server.py`)
   - Uses same date boundaries for amendments filtering
   - Ensures consistent term filtering across frontend and backend

## Data Consistency

All parliamentary activities are filtered using these term boundaries to ensure:

- **Amendment counts** match between profile data and detailed views
- **Activity metrics** are calculated using consistent time periods
- **Rankings** are based on activities within the correct term dates
- **API responses** return data filtered by the same term logic

## Important Notes

1. **Exclusive End Dates**: Term boundaries use exclusive end dates (date < end_date)
2. **Transition Dates**: 
   - Term 8 ends July 1, 2019 (exclusive)
   - Term 9 starts July 2, 2019 (inclusive)
   - Term 9 ends July 15, 2024 (inclusive in data, July 16 exclusive in code)
   - Term 10 starts July 16, 2024 (inclusive)

3. **Date Format**: All dates use ISO format (YYYY-MM-DD)
4. **Timezone**: Dates are processed in UTC/local European time

## Maintenance

When updating term dates:

1. Update `backend/ingest_parltrack.py` - `get_term_for_date()` function
2. Update `backend/process_data.py` - `TERM_DATES` dictionary  
3. Update `run_api_server.py` - term filtering logic
4. Update this documentation
5. Re-run data ingestion and processing to ensure consistency

## References

- European Parliament official term information
- ParlTrack data structure and dating conventions
- Application database schema and activity filtering logic