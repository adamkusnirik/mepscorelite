# MEP Score Professional Deployment System

This directory contains the complete professional deployment infrastructure for the MEP Score application, including automated CI/CD, monitoring, security, and maintenance tools.

## 🏗️ Architecture Overview

```
MEP Score Production Infrastructure
├── Frontend (Static Files)
│   ├── HTML, CSS, JS served by Nginx
│   ├── Optimized JSON datasets
│   └── Cached static assets
├── Backend API (Python)
│   ├── Production server with monitoring
│   ├── SQLite database
│   └── Health check endpoints
├── Web Server (Nginx)
│   ├── SSL/TLS termination
│   ├── Rate limiting & security headers
│   ├── Advanced caching & compression
│   └── Load balancing ready
├── Monitoring & Logging
│   ├── System metrics collection
│   ├── Log analysis & security alerts
│   ├── Performance monitoring
│   └── Web dashboard
└── CI/CD Pipeline
    ├── Automated deployment
    ├── Data optimization
    ├── Health checks & rollback
    └── GitHub Actions integration
```

## 📁 Files Overview

### Core Deployment Files
- **`deploy.sh`** - Main deployment script with monitoring and security
- **`nginx.conf`** - Production-ready web server configuration
- **`mepscore.service`** - Systemd service configuration
- **`production_serve.py`** - Enhanced Python server with monitoring

### Monitoring & Logging
- **`monitoring/system_monitor.py`** - Comprehensive system monitoring
- **`monitoring/log_analyzer.py`** - Access log analysis and security alerts
- **`monitoring/dashboard.py`** - Web-based monitoring dashboard

### Automation
- **`upload_files.sh`** - File upload script for deployments
- **`redeploy_from_github.sh`** - GitHub-based redeployment

## 🚀 Quick Start

### Prerequisites
- Ubuntu 20.04+ server
- Domain pointing to server IP
- SSH access with sudo privileges

### 1. Initial Setup

```bash
# Upload deployment files to server
scp -r deployment/ user@your-server:/tmp/

# Connect to server
ssh user@your-server

# Run deployment script
cd /tmp/deployment
sudo chmod +x deploy.sh
sudo ./deploy.sh
```

### 2. GitHub Actions Setup

Add these secrets to your GitHub repository:

```
LIGHTSAIL_SSH_KEY - Your private SSH key
LIGHTSAIL_HOST - Your server IP address
```

### 3. Configure Environment Variables

```bash
# Email alerts (optional)
export SMTP_SERVER=smtp.gmail.com
export SMTP_PORT=587
export SMTP_USERNAME=your-email@gmail.com
export SMTP_PASSWORD=your-app-password
export ALERT_EMAIL=admin@mepscore.eu
```

## 🛠️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SMTP_SERVER` | SMTP server for alerts | localhost |
| `SMTP_PORT` | SMTP port | 587 |
| `SMTP_USERNAME` | SMTP username | - |
| `SMTP_PASSWORD` | SMTP password | - |
| `ALERT_EMAIL` | Alert recipient email | admin@mepscore.eu |
| `EMAIL` | Let's Encrypt email | admin@mepscore.eu |

### Monitoring Thresholds

Edit thresholds in `monitoring/system_monitor.py`:

```python
ALERT_THRESHOLDS = {
    'cpu_percent': 80,
    'memory_percent': 85,
    'disk_percent': 90,
    'response_time_ms': 2000,
    'error_rate_percent': 5
}
```

## 📊 Monitoring & Alerts

### System Monitoring
- **Frequency**: Every 5 minutes
- **Metrics**: CPU, memory, disk, network, response times
- **Alerts**: Email notifications for critical issues
- **Storage**: SQLite database with 30-day retention

### Log Analysis
- **Frequency**: Hourly
- **Features**: Geographic analysis, bot detection, security alerts
- **Thresholds**: Configurable rate limiting and abuse detection

### Web Dashboard
- **URL**: `http://your-server:9000` (internal only)
- **Features**: Real-time metrics, charts, alert history
- **Auto-refresh**: Every 60 seconds

### Health Checks
- **Internal**: `http://localhost:8000/api/health`
- **External**: `https://mepscore.eu/health`
- **Monitoring**: System resources, API status, database connectivity

## 🔒 Security Features

### SSL/TLS Configuration
- **Protocols**: TLS 1.2, TLS 1.3
- **Ciphers**: Modern cipher suites
- **HSTS**: Enabled with preload
- **OCSP Stapling**: Enabled

### Security Headers
- Content Security Policy (CSP)
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- X-XSS-Protection: 1; mode=block
- Referrer-Policy: strict-origin-when-cross-origin
- Permissions-Policy: restrictive

### Rate Limiting
- **API**: 10 requests/second per IP
- **General**: 30 requests/second per IP
- **Static files**: 50 requests/second per IP

### Fail2ban Protection
- **SSH**: 3 failed attempts = 1 hour ban
- **Web**: 6 suspicious requests = 1 hour ban
- **Bots**: 2 bad bot requests = 24 hour ban

### File Access Protection
- Hidden files (.env, .git) blocked
- Sensitive extensions blocked
- Version control directories blocked

## 🔄 CI/CD Pipeline

### Automated Deployment Triggers
- Push to `main` branch
- Manual workflow dispatch

### Deployment Steps
1. **Test & Validate**
   - Python dependency check
   - Database structure validation
   - Server startup test

2. **Build & Optimize**
   - JSON file minification
   - Static asset compression
   - Archive creation

3. **Deploy**
   - Atomic deployment with rollback
   - Service restart
   - Health verification

4. **Verify**
   - HTTP response checks
   - API health validation
   - Performance verification

### Rollback Strategy
- Automatic backup before deployment
- Immediate rollback on health check failure
- Manual rollback capability

## 📈 Performance Optimizations

### Nginx Optimizations
- **Gzip compression**: Level 6, multiple formats
- **Brotli compression**: Level 6 (if available)
- **Static file caching**: 1 year with immutable headers
- **JSON caching**: 1 hour with revalidation
- **Connection pooling**: HTTP/1.1 with keep-alive

### Application Optimizations
- **JSON minification**: Automated during deployment
- **Database optimization**: Connection pooling, timeouts
- **Response caching**: Strategic cache headers
- **Resource monitoring**: Background health checks

### CDN Ready
- **Immutable assets**: Far-future expires headers
- **Conditional requests**: ETag support
- **Compression**: Pre-compressed files served
- **CORS**: Font files properly configured

## 🛠️ Maintenance

### Daily Tasks (Automated)
- **2:00 AM**: Full system backup
- **2:30 AM**: Log rotation and cleanup
- **3:00 AM**: Database maintenance
- **Various**: Health checks every 5 minutes

### Weekly Tasks
```bash
# Check SSL certificate status
sudo certbot certificates

# Review security logs
sudo journalctl -u fail2ban --since="1 week ago"

# System updates
sudo apt update && sudo apt upgrade -y
```

### Monthly Tasks
```bash
# Review disk usage
df -h
du -sh /var/log/* | sort -hr

# Check for zombie processes
ps aux | awk '$8 ~ /^Z/ { print }'

# Review backup sizes
ls -lah /var/backups/mepscore/
```

## 📊 Monitoring Endpoints

| Endpoint | Description | Access |
|----------|-------------|--------|
| `/health` | Basic health check | Public |
| `/api/health` | Detailed API health | Public |
| `/api/metrics` | Performance metrics | Public |
| `:9000/` | Monitoring dashboard | Internal |
| `:9000/api/alerts` | Recent alerts | Internal |

## 🚨 Troubleshooting

### Common Issues

#### Service Not Starting
```bash
# Check service status
sudo systemctl status mepscore nginx

# Check logs
sudo journalctl -u mepscore -f
sudo tail -f /var/log/nginx/mepscore_error.log
```

#### High Memory Usage
```bash
# Check memory usage
free -h
ps aux --sort=-%mem | head

# Restart service if needed
sudo systemctl restart mepscore
```

#### SSL Certificate Issues
```bash
# Check certificate status
sudo certbot certificates

# Renew certificate
sudo certbot renew --force-renewal

# Test nginx configuration
sudo nginx -t
```

#### Database Locked
```bash
# Check database file
ls -la /var/www/mepscore/data/meps.db

# Fix permissions
sudo chown www-data:www-data /var/www/mepscore/data/meps.db

# Check for locks
sudo lsof /var/www/mepscore/data/meps.db
```

### Performance Issues

#### High CPU Usage
```bash
# Check top processes
htop

# Check for runaway Python processes
ps aux | grep python

# Review application logs
tail -f /var/log/mepscore/application.log
```

#### Slow Response Times
```bash
# Check nginx access logs
tail -f /var/log/nginx/mepscore_access.log

# Run performance test
curl -w "@curl-format.txt" -o /dev/null -s https://mepscore.eu/api/health
```

#### Database Performance
```bash
# Check database size
ls -lah /var/www/mepscore/data/meps.db

# Run VACUUM if needed
sqlite3 /var/www/mepscore/data/meps.db "VACUUM;"
```

### Security Incidents

#### Suspicious Activity
```bash
# Check fail2ban status
sudo fail2ban-client status

# Review banned IPs
sudo fail2ban-client status nginx-http-auth

# Check security events
python3 /opt/mepscore-monitoring/system_monitor.py
```

#### DDoS Attack
```bash
# Check connection counts
netstat -an | grep :80 | wc -l
netstat -an | grep :443 | wc -l

# Review top IP addresses
awk '{print $1}' /var/log/nginx/mepscore_access.log | sort | uniq -c | sort -nr | head -20
```

## 📧 Support

### Log Locations
- **Application**: `/var/log/mepscore/application.log`
- **Monitoring**: `/var/log/mepscore/monitoring.log`
- **Health Checks**: `/var/log/mepscore/health_check.log`
- **Nginx Access**: `/var/log/nginx/mepscore_access.log`
- **Nginx Error**: `/var/log/nginx/mepscore_error.log`
- **System**: `/var/log/syslog`

### Monitoring Databases
- **System Metrics**: `/var/log/mepscore/monitoring.db`
- **Log Analysis**: `/var/log/mepscore/log_analysis.db`

### Configuration Files
- **Nginx**: `/etc/nginx/sites-available/mepscore`
- **Systemd**: `/etc/systemd/system/mepscore.service`
- **Fail2ban**: `/etc/fail2ban/jail.d/mepscore.conf`
- **Logrotate**: `/etc/logrotate.d/mepscore`

---

For additional support or questions about this deployment system, please refer to the monitoring dashboard or check the application logs for detailed information about system status and performance.