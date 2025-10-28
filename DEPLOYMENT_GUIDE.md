# MEPScore Deployment Guide

## Quick Reference

### Production Server
- **URL**: https://mepscore.eu
- **Server**: 108.128.29.141 (AWS Lightsail)
- **Location**: `/var/www/mepscore/`
- **User**: ubuntu
- **SSH Key**: `LightsailDefaultKey-eu-west-1(3).pem`

### GitHub Repository
- **URL**: https://github.com/adamkusnirik/mepscore
- **Username**: adamkusnirik
- **Token**: _store in a personal access token (PAT) environment variable_

## Deployment Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Internet      │───▶│   Nginx          │───▶│   Python        │
│   (HTTPS:443)   │    │   (Reverse       │    │   serve.py      │
│                 │    │    Proxy)        │    │   (Port 8000)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │   Static Files   │
                       │   /var/www/      │
                       │   mepscore/      │
                       │   public/        │
                       └──────────────────┘
```

## Standard Deployment Process

### 1. Connect to Server

```bash
ssh -i "C:\Users\adamk\Downloads\LightsailDefaultKey-eu-west-1(3).pem" ubuntu@108.128.29.141
```

### 2. Navigate to Application Directory

```bash
cd /var/www/mepscore
```

### 3. Check Current Status

```bash
# Check server process
ps aux | grep python

# Check git status
git status

# Check server logs
tail -20 server.log
```

### 4. Deploy New Code

```bash
# Pull latest changes
git pull origin development

# Restart server if needed
sudo pkill -f python
nohup python3 serve.py >> server.log 2>&1 &
```

### 5. Verify Deployment

```bash
# Test API health
curl -s http://localhost:8000/api/health

# Check if server is running
ps aux | grep serve.py
```

## Emergency Procedures

### Server Not Responding

1. **Check Process Status**:
   ```bash
   ps aux | grep python
   ss -tulnp | grep 8000
   ```

2. **Restart Server**:
   ```bash
   sudo pkill -f python
   cd /var/www/mepscore
   nohup python3 serve.py >> server.log 2>&1 &
   ```

3. **Check Logs**:
   ```bash
   tail -50 /var/log/nginx/error.log
   tail -50 /var/www/mepscore/server.log
   ```

### Nginx Issues

1. **Check Nginx Status**:
   ```bash
   sudo systemctl status nginx
   ```

2. **Restart Nginx**:
   ```bash
   sudo systemctl restart nginx
   ```

3. **Test Configuration**:
   ```bash
   sudo nginx -t
   ```

### SSL Certificate Issues

1. **Check Certificate Status**:
   ```bash
   sudo certbot certificates
   ```

2. **Renew Certificate**:
   ```bash
   sudo certbot renew
   sudo systemctl reload nginx
   ```

## Data Management

### Updating Datasets (Development Only)

⚠️ **Warning**: Only run on development environment, not production

```bash
# Full data update
python run_update.py

# Individual steps
python backend/ingest_parltrack.py
python backend/build_term_dataset.py
```

### Backup Procedures

1. **Create Backup**:
   ```bash
   cd /var/www
   tar --exclude='mepscore/data/parltrack/*.json' \
       --exclude='mepscore/data/*.db' \
       -czf mepscore_backup_$(date +%Y%m%d).tar.gz mepscore/
   ```

2. **Download Backup**:
   ```bash
   scp -i "LightsailDefaultKey.pem" \
       ubuntu@108.128.29.141:/var/www/mepscore_backup_*.tar.gz ./
   ```

## File Permissions

### Standard Permissions

```bash
# Application files
sudo chown -R ubuntu:ubuntu /var/www/mepscore
sudo chmod -R 755 /var/www/mepscore

# Data files (if they exist)
sudo chown -R www-data:www-data /var/www/mepscore/data
sudo chmod -R 644 /var/www/mepscore/data

# Executable scripts
sudo chmod +x /var/www/mepscore/serve.py
sudo chmod +x /var/www/mepscore/deployment/*.sh
```

## Monitoring and Logs

### Log Locations

- **Application Logs**: `/var/www/mepscore/server.log`
- **Nginx Access**: `/var/log/nginx/access.log`
- **Nginx Error**: `/var/log/nginx/error.log`
- **System Logs**: `/var/log/syslog`

### Health Checks

```bash
# API Health
curl -s https://mepscore.eu/api/health

# Website Status
curl -s -o /dev/null -w "%{http_code}" https://mepscore.eu

# Server Resources
df -h
free -h
top -n1
```

## Development Workflow

### Local Development

1. **Setup Environment**:
   ```bash
   cd "C:\Users\adamk\mepscore 3.0"
   python serve.py
   ```

2. **Access Application**:
   - Local: http://localhost:8000
   - Profile: http://localhost:8000/profile.html?mep_id=88882&term=10

### Sync with Production

1. **Download from Server**:
   ```bash
   # Create archive on server
   ssh ubuntu@108.128.29.141 "cd /var/www && tar -czf mepscore_source.tar.gz mepscore/"
   
   # Download archive
   scp ubuntu@108.128.29.141:/var/www/mepscore_source.tar.gz ./
   
   # Extract locally
   tar -xzf mepscore_source.tar.gz --strip-components=1
   ```

2. **Upload to Server**:
   ```bash
   # Upload specific files
   scp -r public/js/ ubuntu@108.128.29.141:/var/www/mepscore/public/
   
   # Or use git push/pull workflow
   git push origin development
   # Then on server: git pull origin development
   ```

## Configuration Files

### Nginx Configuration

Location: `/etc/nginx/sites-available/mepscore`

Key sections:
- SSL certificate paths
- Reverse proxy to port 8000
- Static file serving
- Security headers

### Python Server Configuration

File: `serve.py`

Key settings:
- Port: 8000
- Directory: "public"
- Cache TTL: 1800 seconds
- Max cache size: 3 files

## Troubleshooting Common Issues

### Issue: Activity Details Not Loading

**Symptoms**: "Detailed Data Not Available" message

**Solution**:
1. Check API server is running: `ps aux | grep serve.py`
2. Test health endpoint: `curl localhost:8000/api/health`
3. Verify frontend logic in `public/js/profile.js` line 1178

### Issue: High Memory Usage

**Symptoms**: Server slow or unresponsive

**Solution**:
1. Check memory: `free -h`
2. Restart server: `sudo pkill -f python; nohup python3 serve.py &`
3. Clear cache if needed

### Issue: SSL Certificate Expired

**Symptoms**: Browser security warnings

**Solution**:
1. Check expiry: `sudo certbot certificates`
2. Renew: `sudo certbot renew`
3. Reload nginx: `sudo systemctl reload nginx`

## Security Considerations

### Access Control

- SSH key-based authentication only
- No root login via SSH
- Firewall configured for ports 22, 80, 443 only

### Data Protection

- No sensitive data in frontend code
- Database files excluded from git
- Regular security updates applied

### SSL/TLS

- Let's Encrypt certificates
- HSTS headers enabled
- Modern TLS protocols only

## Performance Optimization

### Frontend

- Static file caching headers
- Gzip compression enabled
- Optimized dataset files
- Lazy loading for detailed data

### Backend

- In-memory caching for API responses
- Efficient database queries
- Pagination for large datasets

### Infrastructure

- CDN not currently used (consider for future)
- Server specs adequate for current load
- Monitor performance metrics regularly

## Disaster Recovery

### Complete Server Rebuild

1. **Provision New Server**
2. **Install Dependencies**:
   ```bash
   sudo apt update
   sudo apt install nginx python3 python3-pip git certbot
   ```

3. **Clone Repository**:
   ```bash
   cd /var/www
   git clone https://github.com/adamkusnirik/mepscore.git
   ```

4. **Configure Nginx** (copy from backup)
5. **Setup SSL Certificates**
6. **Start Application**

### Data Recovery

- Static datasets are in git repository
- Large data files need to be re-downloaded from ParlTrack
- Database can be rebuilt from raw data files

## Contact and Support

### Repository Information
- **GitHub**: https://github.com/adamkusnirik/mepscore
- **Issues**: Create GitHub issues for bugs/features
- **Documentation**: See `APPLICATION_DOCUMENTATION.md`

### Server Access
- **SSH Key Location**: `C:\Users\adamk\Downloads\LightsailDefaultKey-eu-west-1(3).pem`
- **Server IP**: 108.128.29.141
- **Domain**: mepscore.eu

### Emergency Contacts
- **AWS Console**: Check Lightsail dashboard for server status
- **Domain**: Check DNS settings if site unreachable
- **SSL**: Let's Encrypt renewal process automated
