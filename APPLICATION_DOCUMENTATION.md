# MEPScore Application Documentation

## Overview

MEPScore is a comprehensive web application that provides transparent analysis and ranking of European Parliament (EP) members' activities. The application tracks parliamentary activities across multiple terms and provides detailed breakdowns of MEP performance across various categories.

## Architecture

### Frontend (Static Web Application)
- **Technology**: HTML5, CSS3 (Tailwind CSS), Vanilla JavaScript
- **Location**: `public/` directory
- **Main Pages**:
  - `index.html` - Activity Explorer with filtering and search
  - `profile.html` - Individual MEP profile pages
  - `custom_ranking.html` - Custom ranking interface
  - `about.html` - About page
  - `methodology.html` - Methodology explanation

### Backend (Python API Server)
- **Technology**: Python 3.10+, HTTP server, SQLite
- **Main Server**: `serve.py` - Handles both static file serving and API endpoints
- **Data Processing**: `backend/` directory contains data ingestion and processing scripts

### Data Layer
- **Static Datasets**: `public/data/term{X}_dataset.json` - Pre-computed MEP rankings and activities
- **Raw Data**: `data/parltrack/` - ParlTrack JSON files (large files, not in git)
- **Database**: `data/meps.db` - SQLite database with normalized data (not in git)

## Key Components

### 1. Profile System (`public/js/profile.js`)
**Purpose**: Individual MEP profile pages with detailed activity breakdowns

**Key Features**:
- Dynamic MEP data loading from static datasets
- Activity details modal with pagination
- Score breakdown visualization
- Comparative analysis with averages

**API Integration**:
- Automatically detects if API server is available
- Falls back to static mode if API unavailable
- Supports detailed activity loading via API endpoints

### 2. Activity Explorer (`public/js/explorer.js`)
**Purpose**: Searchable, filterable table of all MEPs

**Key Features**:
- Real-time search and filtering
- Sortable columns
- Country and group filtering
- Export functionality

### 3. Custom Ranking (`public/js/custom-ranking.js`)
**Purpose**: Interactive ranking with adjustable category weights

**Key Features**:
- Real-time score recalculation
- Interactive weight sliders
- Dynamic ranking updates
- Export capabilities

### 4. API Server (`serve.py`)
**Purpose**: Serves static files and provides API endpoints for detailed data

**API Endpoints**:
- `/api/health` - Server health check
- `/api/mep/{id}/category/{category}` - Detailed activity data
- `/api/mep/{id}/profile` - Individual MEP profile data
- `/api/dataset/term{X}` - Dynamic dataset generation

## Data Flow

### Static Mode (Production)
1. Frontend loads from `public/data/term{X}_dataset.json`
2. Basic activity counts displayed
3. No detailed activity data available

### API Mode (Development/Enhanced)
1. Frontend checks `/api/health` to detect API availability
2. If available, loads detailed data via API endpoints
3. Provides clickable activity details with pagination
4. Real-time data loading and caching

## Deployment Architecture

### Production Deployment (mepscore.eu)
- **Web Server**: Nginx (reverse proxy)
- **Application Server**: Python serve.py on port 8000
- **SSL**: Let's Encrypt certificates
- **Static Files**: Served via Nginx with caching headers
- **API**: Proxied through Nginx to backend server

### Development Environment
- **Server**: `python serve.py` on localhost:8000
- **Data**: Local JSON files and SQLite database
- **API**: Full API functionality available

## Scoring Methodology

The application implements the official **MEP Score methodology (October 2017)**:

### Core Categories (4 main areas):
1. **Reports** - Rapporteur and shadow rapporteur roles
2. **Statements** - Speeches, explanations, oral questions
3. **Roles** - Committee and delegation positions with multipliers
4. **Attendance** - Voting attendance with penalties

### Scoring Features:
- **Range-based scoring**: Prevents extreme outliers
- **Role multipliers**: Leadership positions get percentage bonuses
- **Attendance penalties**: Poor attendance reduces overall score
- **Threshold-based**: Minimum activity requirements for scoring

## File Structure

```
mepscore/
├── public/                     # Frontend static files
│   ├── js/                    # JavaScript modules
│   │   ├── profile.js        # MEP profile functionality
│   │   ├── explorer.js       # Activity explorer
│   │   ├── custom-ranking.js # Custom ranking system
│   │   └── utilities.js      # Shared utilities
│   ├── css/                  # Stylesheets
│   ├── data/                 # Static datasets
│   └── *.html               # Main pages
├── backend/                   # Data processing
│   ├── ingest_parltrack.py  # Data ingestion
│   ├── build_term_dataset.py # Dataset generation
│   └── scoring_system.py    # Scoring logic
├── data/                     # Data storage
│   ├── parltrack/           # Raw ParlTrack data (excluded)
│   └── meps.db             # SQLite database (excluded)
├── serve.py                 # Main application server
└── deployment/              # Deployment scripts
```

## Environment Configuration

### Required Environment Variables
- None (application uses relative paths)

### Required Python Packages
```
# From requirements.txt
requests
sqlite3 (built-in)
json (built-in)
http.server (built-in)
```

### Data Requirements
- **Development**: Full dataset in `data/parltrack/`
- **Production**: Minimal datasets in `public/data/`

## Common Operations

### Starting the Server
```bash
cd /path/to/mepscore
python serve.py
```

### Updating Data (Development)
```bash
# Full data update pipeline
python run_update.py

# Individual steps
python backend/ingest_parltrack.py
python backend/build_term_dataset.py
```

### Deploying to Production
```bash
# Upload source code
./deployment/upload_files.sh

# Restart server
./deployment/redeploy_from_github.sh
```

## Browser Compatibility

### Supported Browsers
- Chrome 80+
- Firefox 75+
- Safari 13+
- Edge 80+

### Required Features
- ES6 modules
- Fetch API
- CSS Grid
- Flexbox

## Performance Considerations

### Frontend Optimization
- Static dataset files for fast loading
- Lazy loading of detailed data
- Client-side caching
- Responsive design for mobile

### Backend Optimization
- In-memory caching with TTL
- Optimized database queries
- Pagination for large datasets
- Gzip compression

## Security Features

### Data Protection
- No sensitive data in frontend
- SQLite database access restricted
- Static file serving with headers

### Network Security
- HTTPS enforcement
- HSTS headers
- Content type validation
- CORS configuration

## Troubleshooting

### Common Issues

1. **Activity Details Not Loading**
   - Check if API server is running
   - Verify `/api/health` endpoint responds
   - Ensure frontend detects API availability correctly

2. **Data Not Loading**
   - Verify dataset files exist in `public/data/`
   - Check file permissions
   - Validate JSON syntax

3. **Server Not Starting**
   - Check port 8000 availability
   - Verify Python dependencies
   - Check file permissions

### Debug Mode
- Add `?debug=1` to URLs for console logging
- Check browser developer tools
- Monitor server logs

## Future Enhancements

### Planned Features
- Real-time data synchronization
- Advanced analytics dashboard
- Multi-language support
- Enhanced mobile experience

### Technical Improvements
- React/Vue.js migration
- WebSocket integration
- Advanced caching strategies
- Automated testing suite