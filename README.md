# MEP Score

A web application that displays activity scores for Members of European Parliament.

## Core Features

- **MEP Score** - View predefined scores of MEPs based on their parliamentary activities.
- **Activity Explorer** – View and sort raw counts for every activity and role.
- **Custom Ranking** – Adjust weights for each activity/role and generate your own ranking instantly in the browser.

## Frontend Dependencies

* **Papa Parse 5.4** – CSV parsing in the browser (loaded via CDN)
* **Tailwind CSS 3.4** - Utility-first CSS framework (loaded via CDN)

## Project Structure

The project uses static JSON files generated from ParlTrack data so the frontend can run on Netlify / GitHub Pages without a server.

### Main Pages

- `index.html` - Data-grid view of raw counts for every activity/role (Activity Explorer)
- `activity_explorer.html` - Data-grid view of raw counts for every activity/role
- `custom_ranking.html` - Create custom rankings by assigning weights to different activities

## Backend Dependencies

* **Flask** – Python web framework
* **SQLite** – Database for storing MEP data
* **SQLAlchemy** – ORM for interacting with the SQLite database
* **Requests** – Python library for making HTTP requests
* **BeautifulSoup** – Python library for parsing HTML content
* **Flask-Login** – Authentication library for Flask
* **Flask-WTF** – Forms library for Flask
* **Flask-SQLAlchemy** – SQLAlchemy integration for Flask
* **Flask-Bootstrap** – Bootstrap integration for Flask
* **Flask-Gravatar** – Gravatar integration for Flask
* **Flask-Mail** – Email integration for Flask
* **Flask-Script** – Command-line utility for Flask
* **Flask-Testing** – Testing library for Flask
* **Flask-Migrate** – Database migration library for Flask
* **Flask-HTTPAuth** – HTTP authentication library for Flask
* **Flask-RESTful** – RESTful API library for Flask
* **Flask-CORS** – Cross-origin resource sharing library for Flask
* **Flask-JWT** – JSON Web Token library for Flask
* **Flask-Bcrypt** – Bcrypt hashing library for Flask
* **Flask-Session** – Session management library for Flask
* **Flask-Admin** – Admin interface library for Flask
* **Flask-Admin-SQLAlchemy** – SQLAlchemy integration for Flask-Admin

## Data Update Process (10th Term Focus)

**⚠️ IMPORTANT**: This application focuses on the **10th parliamentary term (2024-2029)**. Updates should primarily target current Term 10 data.

### Data Update Folder Structure

All new ParlTrack data files must be placed in:
```
\data\parltrack\
```

### Required ParlTrack Files

The following files are needed for a complete data update:
- `ep_mep_activities.json.zst` - MEP activities (speeches, amendments, etc.)
- `ep_amendments.json.zst` - Amendment details
- `ep_votes.json.zst` - Voting records
- `ep_meps.json.zst` - MEP biographical and political information

### Data Update Process

#### For Non-Technical Maintainers

1. **Download Latest ParlTrack Data**
   - Visit [parltrack.org](https://parltrack.org)
   - Download the latest compressed files (.zst format)
   - Place them in `\data\parltrack\` folder

2. **Update MEP List** (Critical Step)
   - Cross-check against the official MEP full list XML
   - Ensure all current 10th term MEPs are included
   - Remove MEPs who are no longer active

3. **Run Data Update**
   ```bash
   # Windows
   python run_update.py
   
   # Or use the batch file
   run_update.bat
   ```

4. **Verify Update Results**
   - Check that Term 10 data has been updated
   - Verify MEP count matches official EP numbers
   - Test profile pages for accuracy

#### What Gets Updated

The update process refreshes:
- **Score Breakdown** - Individual MEP activity scores using 4-category methodology
- **Profile Pages** - Detailed MEP activity histories and comparisons
- **Averages** - EP-wide, group, and country averages
- **Clickable Activity Details** - Drill-down data for speeches, amendments, etc.

#### Technical Commands

```bash
# Full update pipeline
python run_update.py

# Individual steps (advanced users)
python backend/ingest_parltrack.py      # Step 1: Import raw data
python backend/build_term_dataset.py    # Step 2: Generate rankings
```

### Data Processing for Historical Terms (8th and 9th)

The 8th and 9th parliamentary terms are complete and their data is stored in backup files:

1.  **Modify the Ingestion Script**: Open `backend/ingest_parltrack.py` and uncomment the backup file paths.

2.  **Use Backup Data**: Modify the `count_other_activities` function to load from backup files.

3.  **Run Ingestion**: `python backend/ingest_parltrack.py`

## Running the Application

The application is designed to be launched using the provided launcher scripts, which handle both the backend API server and frontend automatically.

### Quick Start (Recommended)

#### Windows Users
- **Double-click** `launch_app.bat` or `launch_app.ps1`
- Or run `python launch_app.py` in Command Prompt/PowerShell

#### Mac/Linux Users
- Run `python launch_app.py` in Terminal

### What the Launcher Does

The launcher automatically:
1. **Checks Requirements** - Verifies all necessary files exist
2. **Kills Existing Processes** - Stops any server already running on port 8000
3. **Starts API Server** - Launches the backend server (`working_api_server.py`)
4. **Opens Browser** - Automatically opens the application in your default browser
5. **Monitors Server** - Keeps the launcher running to monitor the server process

### Server Details

- **Backend Server**: Flask API server (`run_api_server.py`)
- **Port**: 8000
- **Frontend**: Served from `public/` directory
- **API Endpoints**: Available at `http://localhost:8000/api/`

### URLs

- **Main Application**: http://localhost:8000
- **Profile Page**: http://localhost:8000/profile.html
- **API Base**: http://localhost:8000/api/

### Stopping the Server

- Press `Ctrl+C` in the terminal/command prompt where the launcher is running
- The launcher will automatically stop the Flask server

### Manual Launch (Alternative)

If you prefer to launch manually, you need to have Python 3 installed:

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run the Flask Application**:
    ```bash
    python run_api_server.py
    ```

3.  **View the Application**: Open your web browser and go to `http://localhost:8000`.

### Troubleshooting

#### Port Already in Use
The launcher automatically kills existing processes on port 8000. If you still get port conflicts:
- Manually kill processes: `netstat -aon | findstr :8000` (Windows) or `lsof -i:8000` (Mac/Linux)
- Or change the port in `launch_app.py` and `run_api_server.py`

#### Missing Files
The launcher checks for required files:
- `run_api_server.py`
- `public/index.html`
- `public/profile.html`
- `data/parltrack/ep_mep_activities.json`
- `data/parltrack/ep_amendments.json`
- `data/meps.db`

#### Python Not Found
Make sure Python is installed and in your PATH:
- Windows: Download from python.org
- Mac: Install via Homebrew or python.org
- Linux: Use package manager (apt, yum, etc.)