# AWS Lightsail Deployment Guide - MEP Score Application

## Server Connection Details

### AWS Lightsail Instance
- **Public IP**: `108.128.29.141`
- **Instance Name**: MEP Score Production Server
- **Region**: EU West (Ireland)
- **Key File**: `C:\Users\adamk\Downloads\LightsailDefaultKey-eu-west-1(1).pem`

### SSH Connection Command
```bash
ssh -i "C:\Users\adamk\Downloads\LightsailDefaultKey-eu-west-1(1).pem" ubuntu@108.128.29.141
```

## GitHub Repository Details

- **Repository**: `https://github.com/adamkusnirik/mepscore.git`
- **Branch**: `master`
- **Latest Commit**: `87be585` - Production fixes and optimizations

## Quick Deployment Commands

### 1. Connect to Server
```bash
ssh -i "C:\Users\adamk\Downloads\LightsailDefaultKey-eu-west-1(1).pem" ubuntu@108.128.29.141
```

### 2. Navigate to Application Directory
```bash
cd /var/www/mepscore
```

### 3. Pull Latest Changes from GitHub
```bash
git pull origin master
```

### 4. Install Dependencies (if needed)
```bash
pip3 install ijson flask flask-cors
```

### 5. Start/Restart Server
```bash
# Stop existing server
pkill -f "python3 serve.py"

# Start new server
python3 serve.py
```

### 6. Verify Server is Running
```bash
curl http://localhost:8000/api/health
```

## Critical File Locations on Server

### Application Files
- **Main Server**: `/var/www/mepscore/serve.py`
- **Frontend**: `/var/www/mepscore/public/`
- **Database**: `/var/www/mepscore/data/meps.db`

### Data Files Structure
```
/var/www/mepscore/data/parltrack/
├── ep_amendments.json (current term)
├── ep_mep_activities.json (current term)
├── 8th term/
│   └── ep_mep_activities-2019-07-03.json
└── 9th term/
    └── ep_mep_activities-2024-07-02.json
```

## Troubleshooting Commands

### Check Server Status
```bash
# Check if server is running
ps aux | grep "python3 serve.py"

# Check port 8000 usage
netstat -tlnp | grep :8000

# Check server logs (if running in background)
tail -f /var/log/mepscore.log
```

### Restart Server Process
```bash
# Kill existing process
pkill -f "python3 serve.py"

# Start server in background
nohup python3 serve.py > /var/log/mepscore.log 2>&1 &
```

### Verify Data Files
```bash
# Check database exists
ls -la /var/www/mepscore/data/meps.db

# Check JSON data files
ls -la /var/www/mepscore/data/parltrack/

# Check file sizes
du -h /var/www/mepscore/data/parltrack/*.json
```

## Data Update Process

### From Local Development to Server

1. **Update local data** (run locally):
```bash
python run_update.py
```

2. **Commit and push changes**:
```bash
git add .
git commit -m "Update parliamentary data - $(date)"
git push origin master
```

3. **Deploy to server**:
```bash
ssh -i "C:\Users\adamk\Downloads\LightsailDefaultKey-eu-west-1(1).pem" ubuntu@108.128.29.141
cd /var/www/mepscore
git pull origin master
pkill -f "python3 serve.py"
python3 serve.py
```

## Key Technical Fixes Applied

### 1. Streaming JSON Processing
- **File**: `serve.py`
- **Purpose**: Handle large JSON files (86MB+) without memory exhaustion
- **Implementation**: Uses `ijson` library for streaming

### 2. Date Extraction from Parliamentary References
- **Function**: `extract_date_from_reference()`
- **Patterns**: Handles `CRE-PROV`, `CRE-REV`, and `CRE` formats
- **Purpose**: Extract real dates from corrupted Term 8 data

### 3. File Path Fallback Logic
- **Purpose**: Support legacy term data structure
- **Fallback order**: Current files → Term directories → Legacy structure

### 4. Frontend Static Mode Fix
- **File**: `public/js/profile.js`
- **Fix**: Corrected static mode detection for public IP access

## Backup and Recovery

### Create Server Backup
```bash
# On server - backup application
tar -czf mepscore_backup_$(date +%Y%m%d).tar.gz /var/www/mepscore

# Download backup to local
scp -i "C:\Users\adamk\Downloads\LightsailDefaultKey-eu-west-1(1).pem" ubuntu@108.128.29.141:/home/ubuntu/mepscore_backup_*.tar.gz ./
```

### Restore from GitHub
```bash
# Complete fresh deployment
cd /var/www/
sudo rm -rf mepscore
sudo git clone https://github.com/adamkusnirik/mepscore.git
sudo chown -R ubuntu:ubuntu mepscore
cd mepscore
pip3 install -r requirements.txt  # if requirements.txt exists
python3 serve.py
```

## Monitoring and Health Checks

### API Health Check
```bash
# HTTPS (recommended)
curl -k https://108.128.29.141/api/health

# HTTP (redirects to HTTPS)
curl http://108.128.29.141/api/health
```

### Test MEP Profile Loading
```bash
# Test current term MEP (HTTPS)
curl -k "https://108.128.29.141/api/mep/88882/category/amendments?term=10&offset=0&limit=5"

# Test legacy term MEP (HTTPS)
curl -k "https://108.128.29.141/api/mep/28372/category/speeches?term=8&offset=0&limit=5"

# Note: Use -k flag to ignore self-signed certificate warnings
```

### Frontend Access
- **Main Page**: `https://108.128.29.141/` (HTTPS with automatic redirect)
- **Profile Example**: `https://108.128.29.141/profile.html?mep_id=88882&term=10`
- **Legacy HTTP**: `http://108.128.29.141/` (automatically redirects to HTTPS)

## Emergency Contacts and Notes

### Known Working MEP IDs for Testing
- **Victor NEGRESCU**: `88882` (Term 10) - Speeches, Amendments
- **Ryszard CZARNECKI**: `28372` (Terms 8, 9) - Historical data

### Critical Dependencies
- **Python**: 3.8+
- **Required packages**: `ijson`, `flask`, `flask-cors`
- **Database**: SQLite (`meps.db`)

### Performance Notes
- Server handles concurrent requests with streaming processing
- Memory usage optimized for large JSON files
- Response times typically under 350ms

## HTTPS Configuration

### Current Setup
- ✅ **Nginx reverse proxy** installed and configured
- ✅ **Self-signed SSL certificate** for immediate HTTPS support
- ✅ **Automatic HTTP to HTTPS redirect** configured
- ✅ **Security headers** implemented (HSTS, X-Frame-Options, etc.)

### SSL Certificate Details
- **Type**: Self-signed certificate (development/testing)
- **Location**: `/etc/ssl/mepscore/`
- **Valid for**: 365 days from creation
- **Common Name**: `108.128.29.141`

### Nginx Configuration
- **HTTP (Port 80)**: Redirects to HTTPS
- **HTTPS (Port 443)**: Serves application with SSL
- **Proxy**: Forwards to Python server on `localhost:8000`

### Security Features
- TLS 1.2 and 1.3 support
- Strong cipher suites
- HSTS (HTTP Strict Transport Security)
- Anti-clickjacking headers
- Content type sniffing protection

### Upgrading to Trusted Certificate

For production use with a domain name, replace self-signed certificate:

```bash
# If you have a domain (e.g., mepscore.example.com)
# 1. Update DNS to point to 108.128.29.141
# 2. Update Nginx server_name directive
sudo nano /etc/nginx/sites-available/mepscore
# Change: server_name 108.128.29.141;
# To: server_name mepscore.example.com;

# 3. Obtain Let's Encrypt certificate
sudo certbot --nginx -d mepscore.example.com
```

### HTTPS Troubleshooting

```bash
# Check SSL certificate
openssl x509 -in /etc/ssl/mepscore/mepscore.crt -text -noout

# Test HTTPS connectivity
curl -k -v https://108.128.29.141/

# Check Nginx SSL configuration
sudo nginx -T | grep ssl

# Verify redirect works
curl -I http://108.128.29.141/
```

## Quick Reference Commands

```bash
# Complete deployment refresh
ssh -i "C:\Users\adamk\Downloads\LightsailDefaultKey-eu-west-1(1).pem" ubuntu@108.128.29.141 "cd /var/www/mepscore && git pull origin master && pkill -f 'python3 serve.py' && python3 serve.py &"

# Health check (HTTPS)
curl -k https://108.128.29.141/api/health

# View server processes
ssh -i "C:\Users\adamk\Downloads\LightsailDefaultKey-eu-west-1(1).pem" ubuntu@108.128.29.141 "ps aux | grep python"
```

---

**Last Updated**: August 15, 2025  
**Server Status**: ✅ Operational with HTTPS and all fixes applied  
**GitHub Status**: ✅ All changes backed up to master branch  
**HTTPS Status**: ✅ Self-signed certificate active, HTTP redirects to HTTPS