# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Plan & Review

### Before starting work
- Always start in plan mode to make a plan
- After creating the plan, write it to `.claude/tasks/TASK_NAME.md`
- The plan should be a detailed implementation plan with reasoning and broken down tasks
- If the task requires external knowledge or certain packages, research to get latest knowledge (use Task tool for research)
- Don't over plan - always think MVP
- Once you write the plan, ask for review and approval before continuing

### While implementing
- Update the plan as you work
- After completing tasks in the plan, update and append detailed descriptions of the changes made
- Document changes for easy handover to other engineers

## Commands

### Data Update Process (10th Term Focus)

#### Full Data Update Pipeline
- `python run_update.py` - **MAIN COMMAND**: Complete data update for Term 10
- `run_update.bat` - Windows batch file for full data update
- `run_update.ps1` - PowerShell script for full data update

#### Individual Data Processing Steps
- `python backend/ingest_parltrack.py` - Step 1: Ingest ParlTrack data into SQLite database (creates `data/meps.db`)
- `python backend/build_term_dataset.py` - Step 2: Build static JSON datasets for frontend from database

#### Data Update Requirements
**Data Folder**: `\data\parltrack\` - All new ParlTrack files must be placed here
**Required Files**:
- `ep_mep_activities.json.zst` - MEP activities (speeches, amendments, etc.)
- `ep_amendments.json.zst` - Amendment details  
- `ep_votes.json.zst` - Voting records
- `ep_meps.json.zst` - MEP biographical and political information

#### What Gets Updated
The data update process refreshes:
- Score breakdown (4-category methodology)
- Profile pages with detailed activity histories
- EP-wide, group, and country averages
- Clickable activity details for drill-down analysis

#### Legacy Commands
- `npm run generate-data` - Same as build_term_dataset command
- `npm run build:data` - Build ranking data for 9th term specifically

### Development Server
- `python serve.py` - Start development server on port 8000 serving `public/` directory
- `npm run dev` - Alternative development server using `serve` package

### Data Management
- `python decompress_parltrack_data.py` - Decompress .zst files in parltrack data

## Architecture

### Data Flow
1. **Raw Data Sources**: ParlTrack JSON files (`data/parltrack/`) containing EP data
2. **Database Layer**: SQLite database (`data/meps.db`) with normalized MEP, activity, and ranking data
3. **Static JSON Generation**: Processed datasets in `public/data/` for frontend consumption
4. **Frontend**: Static HTML/JS application serving ranking interfaces

### Key Components

**Backend Processing (`backend/`)**:
- `ingest_parltrack.py` - Core data ingestion from ParlTrack JSON to SQLite
- `build_term_dataset.py` - Generate static JSON datasets for each EP term
- `activity_metrics.py` - MEP activity scoring and ranking logic
- `scoring_system.py` - Configurable scoring system for MEP activities

**Data Structure**:
- `data/parltrack/` - Raw ParlTrack data (JSON/ZST compressed)
- `data/meps.db` - SQLite database with MEP profiles and activities
- `public/data/term*_dataset.json` - Static datasets for frontend consumption

**Frontend (`public/`)**:
- `index.html` - Activity Explorer (raw activity data grid)
- `custom_ranking.html` - Custom ranking interface with adjustable weights
- `profile.html` - Individual MEP profile pages
- `js/` - Frontend JavaScript modules (utilities, custom-ranking, explorer, etc.)

### Database Schema
The SQLite database contains tables for:
- `meps` - MEP biographical and political information
- `activities` - Parliamentary activity records by MEP and term
- `roles` - Committee and delegation roles
- `rankings` - Calculated rankings by term and scoring method

### Historical Data Processing
For completed 8th and 9th terms, modify `backend/ingest_parltrack.py` to use backup files:
- Uncomment backup file paths for terms 8 and 9
- Modify `count_other_activities()` to load from backup JSON files
- Run ingestion to populate historical data

### Frontend Dependencies
- Papa Parse 5.4 (CSV parsing)
- Tailwind CSS 3.4 (styling)
- Custom JavaScript modules for ranking calculations and UI interactions

### Scoring System
The application implements the official **MEP Score methodology (October 2017)** for evaluating European Parliament member activity. The scoring system includes:

- **4 main categories**: Reports, Statements, Roles, Attendance
- **Range-based scoring**: Prevents extreme outliers while maintaining distinctions
- **Role multipliers**: Leadership positions receive percentage bonuses
- **Attendance penalties**: Reduced scores for poor attendance

**Key Implementation Details:**
- **Statements thresholds**: Speeches (250+ for points), Explanations (140+ for points), Oral Questions (7+ for points)
- **Written Questions**: 0.1 points each, max 20 points
- **Reports**: Rapporteur (4.0pts), Shadow (1.0pts), Opinion roles (1.0/0.5pts)
- **Amendments**: Range-based 1-3 points based on count (0-66, 67-133, 134-200, 200+)

The scoring logic is implemented in `backend/mep_ranking_scorer.py`. For complete methodology details, see `METHODOLOGY.md`.