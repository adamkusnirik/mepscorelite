# MEP Score Professional DevOps Deployment Guide

This comprehensive guide provides step-by-step instructions for deploying the MEP Score application using professional DevOps practices with automated CI/CD, monitoring, and security features.

## 🎯 Overview

The MEP Score application now includes a complete DevOps infrastructure featuring:

- **Automated CI/CD** with GitHub Actions
- **Professional monitoring** and alerting system  
- **Security hardening** with fail2ban and rate limiting
- **Performance optimization** with advanced caching
- **Health checks** and automated recovery
- **Comprehensive logging** and analytics

## 🏗️ Infrastructure Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        GitHub Repository                        │
│  ┌─────────────────┐    ┌──────────────────────────────────┐   │
│  │   Source Code   │    │        GitHub Actions           │   │
│  │                 │───▶│  • Test & Validate             │   │
│  │ • Frontend      │    │  • Build & Optimize            │   │
│  │ • Backend API   │    │  • Deploy to AWS               │   │
│  │ • Data Scripts  │    │  • Health Checks & Rollback    │   │
│  └─────────────────┘    └──────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    │ SSH Deploy
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AWS Lightsail Server                        │
│                                                                 │
│  ┌─────────────────┐    ┌──────────────────────────────────┐   │
│  │     Nginx       │    │         MEP Score App           │   │
│  │                 │    │                                  │   │
│  │ • SSL/TLS       │───▶│  • Python API Server           │   │
│  │ • Rate Limiting │    │  • SQLite Database              │   │
│  │ • Caching       │    │  • Data Processing              │   │
│  │ • Compression   │    │  • Health Endpoints             │   │
│  └─────────────────┘    └──────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────┐    ┌──────────────────────────────────┐   │
│  │   Monitoring    │    │          Security               │   │
│  │                 │    │                                  │   │
│  │ • System Metrics│    │  • Fail2ban Protection         │   │
│  │ • Log Analysis  │    │  • Security Headers             │   │
│  │ • Web Dashboard │    │  • File Access Control         │   │
│  │ • Email Alerts  │    │  • Rate Limiting                │   │
│  └─────────────────┘    └──────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Deployment

### Method 1: Automated GitHub Actions Deployment (Recommended)

1. **Configure GitHub Secrets**
   ```
   Repository Settings → Secrets and Variables → Actions → New Repository Secret
   
   LIGHTSAIL_SSH_KEY: Your private SSH key content
   LIGHTSAIL_HOST: Your server IP address (e.g., 1.2.3.4)
   ```

2. **Trigger Deployment**
   ```bash
   # Push to main branch triggers automatic deployment
   git push origin main
   
   # Or trigger manual deployment
   GitHub Actions → Deploy MEP Score → Run workflow
   ```

3. **Monitor Deployment**
   - Watch GitHub Actions workflow progress
   - Check deployment logs for any issues
   - Verify site is live at `https://mepscore.eu`

### Method 2: Manual Deployment

1. **Prepare Server**
   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y
   
   # Upload deployment files
   scp -r deployment/ user@your-server:/tmp/
   ```

2. **Run Deployment Script**
   ```bash
   ssh user@your-server
   cd /tmp/deployment
   sudo chmod +x deploy.sh
   sudo ./deploy.sh
   ```

3. **Configure SSL**
   ```bash
   # Follow prompts during deployment script
   # Or run manually later:
   sudo certbot --nginx -d mepscore.eu -d www.mepscore.eu
   ```

## 📋 Detailed Setup Instructions

### Step 1: Server Preparation

**AWS Lightsail Setup:**
1. Create Ubuntu 20.04 LTS instance ($10-20/month recommended)
2. Configure static IP
3. Set up DNS (A records: @ and www → static IP)
4. Configure firewall (ports 22, 80, 443)

**Server Configuration:**
```bash
# Create deployment user (optional but recommended)
sudo adduser deploy
sudo usermod -aG sudo deploy
sudo mkdir -p /home/deploy/.ssh
sudo cp ~/.ssh/authorized_keys /home/deploy/.ssh/
sudo chown -R deploy:deploy /home/deploy/.ssh
sudo chmod 700 /home/deploy/.ssh
sudo chmod 600 /home/deploy/.ssh/authorized_keys
```

### Step 2: GitHub Repository Setup

**Required Repository Structure:**
```
mepscore/
├── .github/workflows/deploy.yml    # GitHub Actions workflow
├── deployment/                     # Deployment scripts and configs
│   ├── deploy.sh                  # Main deployment script
│   ├── nginx.conf                 # Web server configuration
│   ├── mepscore.service           # Systemd service
│   ├── production_serve.py        # Production Python server
│   └── monitoring/                # Monitoring scripts
├── public/                        # Frontend files
├── backend/                       # Python backend
├── data/                         # Application data
└── requirements.txt              # Python dependencies
```

**GitHub Secrets Configuration:**

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `LIGHTSAIL_SSH_KEY` | Private SSH key for server access | `-----BEGIN OPENSSH PRIVATE KEY-----...` |
| `LIGHTSAIL_HOST` | Server IP address | `1.2.3.4` |

**Generate SSH Key for GitHub Actions:**
```bash
# On your local machine
ssh-keygen -t ed25519 -f ~/.ssh/mepscore_deploy -C "github-actions@mepscore.eu"

# Add public key to server authorized_keys
ssh-copy-id -i ~/.ssh/mepscore_deploy.pub user@your-server

# Copy private key content to GitHub Secrets
cat ~/.ssh/mepscore_deploy
```

### Step 3: Environment Configuration

**Server Environment Variables:**
```bash
# Create environment file
sudo nano /etc/environment

# Add these variables:
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=alerts@mepscore.eu
SMTP_PASSWORD=your-app-specific-password
ALERT_EMAIL=admin@mepscore.eu
EMAIL=admin@mepscore.eu

# Reload environment
source /etc/environment
```

**Email Alerts Setup (Optional):**
1. Create Gmail app-specific password
2. Configure SMTP settings in environment variables
3. Test email notifications:
   ```bash
   python3 /opt/mepscore-monitoring/system_monitor.py
   ```

### Step 4: Data Management

**Upload ParlTrack Data:**
```bash
# Upload required data files to server
scp data/parltrack/*.json.zst user@server:/var/www/mepscore/data/parltrack/

# Or update via deployment script
./deployment/upload_files.sh
```

**Data Processing:**
```bash
# Process ParlTrack data
cd /var/www/mepscore
sudo -u www-data ./venv/bin/python backend/ingest_parltrack.py
sudo -u www-data ./venv/bin/python backend/build_term_dataset.py
```

## 🔧 Advanced Configuration

### Nginx Customization

**Custom Rates and Limits:**
```nginx
# Edit /etc/nginx/sites-available/mepscore

# Rate limiting zones
limit_req_zone $binary_remote_addr zone=api:10m rate=20r/s;     # Increase API rate
limit_req_zone $binary_remote_addr zone=general:10m rate=50r/s; # Increase general rate

# Connection limiting
limit_conn_zone $binary_remote_addr zone=perip:10m;
limit_conn perip 30; # Increase connection limit
```

**Custom Cache Settings:**
```nginx
# Longer cache for static assets
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
    expires 2y;  # Increase to 2 years
    add_header Cache-Control "public, immutable";
}

# Custom cache for JSON data
location ~* \.json$ {
    expires 6h;  # Increase to 6 hours
    add_header Cache-Control "public, must-revalidate";
}
```

### Monitoring Customization

**Alert Thresholds:**
```python
# Edit deployment/monitoring/system_monitor.py

ALERT_THRESHOLDS = {
    'cpu_percent': 75,      # Lower threshold for earlier warning
    'memory_percent': 80,   # Adjust based on your needs
    'disk_percent': 85,     # Adjust based on disk size
    'response_time_ms': 1500,  # Stricter response time
    'error_rate_percent': 3    # Lower error tolerance
}
```

**Monitoring Frequency:**
```python
# Health check interval (seconds)
HEALTH_CHECK_INTERVAL = 30  # More frequent checks

# Email alert cooldown
alert_cooldown = timedelta(minutes=15)  # Shorter cooldown
```

### Security Hardening

**SSH Configuration:**
```bash
sudo nano /etc/ssh/sshd_config

# Recommended settings:
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
MaxAuthTries 3
ClientAliveInterval 300
ClientAliveCountMax 2

sudo systemctl restart sshd
```

**Fail2ban Custom Rules:**
```bash
sudo nano /etc/fail2ban/jail.d/mepscore-custom.conf

[mepscore-api]
enabled = true
port = https,http
filter = mepscore-api
logpath = /var/log/nginx/mepscore_access.log
maxretry = 20
findtime = 60
bantime = 3600
```

**UFW Firewall:**
```bash
# Basic firewall setup
sudo ufw --force enable
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'

# Allow monitoring dashboard (internal only)
sudo ufw allow from 10.0.0.0/8 to any port 9000
sudo ufw allow from 172.16.0.0/12 to any port 9000
sudo ufw allow from 192.168.0.0/16 to any port 9000
```

## 📊 Monitoring & Alerting

### Available Dashboards

1. **System Monitoring Dashboard**
   - URL: `http://server-ip:9000`
   - Features: Real-time metrics, performance charts, alert history
   - Access: Internal network only

2. **Application Health Endpoints**
   - `https://mepscore.eu/health` - Basic health check
   - `https://mepscore.eu/api/health` - Detailed API health with metrics

### Monitoring Metrics

**System Metrics (Collected every 5 minutes):**
- CPU usage percentage
- Memory usage percentage
- Disk usage percentage
- Network I/O statistics
- Load average
- Process count

**Application Metrics:**
- API response times
- Request rates
- Error rates
- Database connectivity
- Service availability

**Log Analysis (Processed hourly):**
- Traffic patterns by geography
- Bot vs human traffic
- Top pages and referers
- Security events
- Bandwidth usage

### Alert Types

| Alert Type | Trigger Condition | Severity | Action |
|------------|------------------|----------|---------|
| High CPU | CPU > 80% | Warning | Monitor |
| High Memory | Memory > 85% | Warning | Monitor |
| High Disk | Disk > 90% | Critical | Email + Cleanup |
| API Down | API not responding | Critical | Email + Restart |
| Site Down | Main site down | Critical | Email + Investigate |
| Slow Response | Response > 2s | Warning | Monitor |
| Security Event | Suspicious activity | Warning | Email + Log |

### Custom Alerts

**Email Configuration:**
```bash
# Test email alerts
sudo -u www-data python3 << 'EOF'
import smtplib
from email.mime.text import MIMEText

msg = MIMEText("Test alert from MEP Score monitoring")
msg['Subject'] = "Test Alert"
msg['From'] = "alerts@mepscore.eu"
msg['To'] = "admin@mepscore.eu"

server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login('alerts@mepscore.eu', 'your-password')
server.send_message(msg)
server.quit()
print("Test email sent successfully!")
EOF
```

**Slack Integration (Optional):**
```python
# Add to monitoring/system_monitor.py
import requests

def send_slack_alert(alert):
    webhook_url = "https://hooks.slack.com/your-webhook-url"
    payload = {
        "text": f"MEP Score Alert: {alert['severity']} - {alert['message']}"
    }
    requests.post(webhook_url, json=payload)
```

## 🛠️ Maintenance & Operations

### Regular Maintenance Tasks

**Daily (Automated):**
- System backups at 2:00 AM
- Log rotation at 2:30 AM
- Health monitoring every 5 minutes
- Security scanning hourly

**Weekly (Manual/Scripted):**
```bash
#!/bin/bash
# weekly_maintenance.sh

# System updates
sudo apt update && sudo apt list --upgradable
sudo apt upgrade -y

# SSL certificate check
sudo certbot certificates

# Disk cleanup
sudo apt autoremove -y
sudo apt autoclean

# Log analysis
sudo find /var/log -name "*.log" -size +100M -exec ls -lh {} \;

# Backup verification
ls -lah /var/backups/mepscore/ | tail -10

# Performance check
curl -w "@curl-format.txt" -o /dev/null -s https://mepscore.eu/api/health
```

**Monthly (Manual):**
```bash
# Database optimization
sudo -u www-data sqlite3 /var/www/mepscore/data/meps.db "VACUUM;"
sudo -u www-data sqlite3 /var/www/mepscore/data/meps.db "ANALYZE;"

# Review system logs
sudo journalctl --since "1 month ago" --until "now" -p err

# Security audit
sudo fail2ban-client status
sudo ufw status verbose

# Resource usage review
sudo iotop -ao
sudo netstat -tuln
```

### Performance Tuning

**Database Optimization:**
```sql
-- Connect to database
sqlite3 /var/www/mepscore/data/meps.db

-- Check database size and stats
.dbinfo

-- Optimize queries
PRAGMA optimize;

-- Enable WAL mode for better concurrency
PRAGMA journal_mode=WAL;

-- Adjust cache size (in pages, default page size is 4096 bytes)
PRAGMA cache_size=10000;  -- 40MB cache
```

**Nginx Optimization:**
```nginx
# Edit /etc/nginx/nginx.conf

worker_processes auto;
worker_connections 2048;
worker_rlimit_nofile 4096;

# Optimize keepalive
keepalive_requests 1000;
keepalive_timeout 30;

# Buffer optimizations
client_body_buffer_size 128k;
client_max_body_size 10m;
client_header_buffer_size 1k;
large_client_header_buffers 4 4k;
output_buffers 1 32k;
postpone_output 1460;
```

### Scaling Considerations

**Vertical Scaling (Lightsail):**
- Upgrade instance size via AWS console
- Monitor resource usage to determine when to scale
- Plan for brief downtime during scaling

**Horizontal Scaling Preparation:**
```nginx
# Load balancer ready configuration
upstream mepscore_backend {
    least_conn;
    server 127.0.0.1:8000 weight=1;
    # server 127.0.0.1:8001 weight=1;  # Additional instances
    keepalive 16;
}

server {
    # ... existing configuration ...
    
    location /api/ {
        proxy_pass http://mepscore_backend;
        # ... existing proxy settings ...
    }
}
```

## 🚨 Troubleshooting Guide

### Common Deployment Issues

**GitHub Actions Deployment Fails:**
```bash
# Check SSH connection
ssh -i ~/.ssh/key user@server

# Verify server has enough space
df -h

# Check service status
sudo systemctl status mepscore nginx

# Review deployment logs
sudo journalctl -u mepscore -n 100
```

**SSL Certificate Issues:**
```bash
# Check certificate status
sudo certbot certificates

# Test nginx configuration
sudo nginx -t

# Force certificate renewal
sudo certbot renew --force-renewal -d mepscore.eu

# Check certificate chain
openssl s_client -connect mepscore.eu:443 -servername mepscore.eu
```

**Database Connection Issues:**
```bash
# Check database file permissions
ls -la /var/www/mepscore/data/meps.db

# Test database connectivity
sudo -u www-data sqlite3 /var/www/mepscore/data/meps.db ".tables"

# Check for database locks
sudo lsof /var/www/mepscore/data/meps.db

# Fix permissions if needed
sudo chown www-data:www-data /var/www/mepscore/data/meps.db
```

### Performance Issues

**High CPU Usage:**
```bash
# Identify top CPU processes
htop
ps aux --sort=-%cpu | head -20

# Check for runaway Python processes
pgrep -f python | xargs ps -fp

# Restart application service
sudo systemctl restart mepscore
```

**Memory Leaks:**
```bash
# Monitor memory usage
watch -n 5 'free -h'

# Check for memory-intensive processes
ps aux --sort=-%mem | head -20

# Check application logs for errors
tail -f /var/log/mepscore/application.log

# Restart if necessary
sudo systemctl restart mepscore
```

**Slow Response Times:**
```bash
# Test response times
curl -w "@curl-format.txt" -o /dev/null -s https://mepscore.eu/

# Check database performance
time sudo -u www-data sqlite3 /var/www/mepscore/data/meps.db "SELECT COUNT(*) FROM meps;"

# Review slow queries in logs
grep -i "slow" /var/log/mepscore/application.log

# Check system load
uptime
iostat -x 1
```

### Security Incidents

**Suspicious Activity Detection:**
```bash
# Check fail2ban status
sudo fail2ban-client status nginx-http-auth

# Review banned IPs
sudo fail2ban-client status nginx-http-auth

# Analyze access patterns
awk '{print $1}' /var/log/nginx/mepscore_access.log | sort | uniq -c | sort -nr | head -20

# Check for unusual user agents
awk -F'"' '{print $6}' /var/log/nginx/mepscore_access.log | sort | uniq -c | sort -nr | head -20
```

**DDoS Mitigation:**
```bash
# Emergency rate limiting
sudo nano /etc/nginx/sites-available/mepscore

# Add strict rate limiting temporarily:
limit_req_zone $binary_remote_addr zone=emergency:10m rate=1r/s;

location / {
    limit_req zone=emergency burst=5 nodelay;
    # ... existing configuration ...
}

# Reload nginx
sudo nginx -s reload

# Monitor connections
watch 'netstat -an | grep :80 | wc -l'
```

## 📈 Performance Monitoring

### Key Performance Indicators (KPIs)

**Response Time Targets:**
- API endpoints: < 500ms average
- Static files: < 100ms average
- Database queries: < 50ms average
- Full page load: < 2s

**Availability Targets:**
- Overall uptime: > 99.5%
- API availability: > 99.9%
- SSL certificate validity: Always valid
- Security updates: Applied within 7 days

**Resource Utilization:**
- CPU usage: < 70% average
- Memory usage: < 80% average  
- Disk usage: < 85% maximum
- Network bandwidth: < 80% of capacity

### Performance Testing

**Load Testing Setup:**
```bash
# Install Apache Bench
sudo apt install apache2-utils

# Test API endpoint
ab -n 1000 -c 10 https://mepscore.eu/api/health

# Test main page
ab -n 1000 -c 10 https://mepscore.eu/

# Test with different concurrency levels
for c in 1 5 10 20 50; do
    echo "Testing with $c concurrent connections:"
    ab -n 100 -c $c https://mepscore.eu/ | grep "Requests per second"
done
```

**Continuous Performance Monitoring:**
```python
#!/usr/bin/env python3
# performance_test.py

import requests
import time
import statistics

def measure_response_time(url, samples=10):
    times = []
    for _ in range(samples):
        start = time.time()
        response = requests.get(url, timeout=10)
        end = time.time()
        
        if response.status_code == 200:
            times.append((end - start) * 1000)  # Convert to milliseconds
    
    if times:
        return {
            'url': url,
            'avg_ms': statistics.mean(times),
            'median_ms': statistics.median(times),
            'min_ms': min(times),
            'max_ms': max(times),
            'samples': len(times)
        }
    return None

# Test key endpoints
endpoints = [
    'https://mepscore.eu/',
    'https://mepscore.eu/api/health',
    'https://mepscore.eu/profile.html',
    'https://mepscore.eu/data/term10_dataset.json'
]

for endpoint in endpoints:
    result = measure_response_time(endpoint)
    if result:
        print(f"URL: {result['url']}")
        print(f"Average: {result['avg_ms']:.1f}ms")
        print(f"Median: {result['median_ms']:.1f}ms")
        print(f"Range: {result['min_ms']:.1f}ms - {result['max_ms']:.1f}ms")
        print("-" * 50)
```

## 🎯 Best Practices Summary

### Deployment Best Practices

1. **Always use version control** - All configuration changes should be committed
2. **Test in staging first** - Use a staging environment for major changes
3. **Automate everything** - Use GitHub Actions for consistent deployments
4. **Monitor deployments** - Watch metrics during and after deployments
5. **Have rollback ready** - Always maintain ability to quickly rollback

### Security Best Practices

1. **Keep systems updated** - Regular security updates
2. **Monitor continuously** - 24/7 monitoring and alerting
3. **Limit access** - Principle of least privilege
4. **Encrypt everything** - HTTPS only, secure communication
5. **Regular backups** - Automated, tested backup strategy

### Performance Best Practices

1. **Cache aggressively** - Multiple layers of caching
2. **Optimize assets** - Minification, compression, optimization
3. **Monitor performance** - Continuous performance tracking
4. **Scale proactively** - Scale before you need to
5. **Optimize databases** - Regular maintenance and optimization

### Operational Best Practices

1. **Document everything** - Keep documentation current
2. **Automate maintenance** - Reduce manual tasks
3. **Plan for disasters** - Have disaster recovery procedures
4. **Regular reviews** - Periodic architecture and security reviews
5. **Team training** - Ensure team knows the system

---

This deployment system provides a solid foundation for running MEP Score in production with professional-grade reliability, security, and performance. For additional support or customization needs, refer to the monitoring dashboard and log files for detailed system information.