#!/bin/bash

# MEP Score Professional Deployment Script for AWS Lightsail
# This script sets up the complete production-ready application environment
# with monitoring, logging, security, and optimization

set -e

echo "========================================"
echo "MEP Score Professional Deployment Script"
echo "========================================"

# Configuration
APP_DIR="/var/www/mepscore"
DOMAIN="mepscore.eu"
EMAIL="${EMAIL:-admin@mepscore.eu}"
NGINX_CONFIG="/etc/nginx/sites-available/mepscore"
LOG_DIR="/var/log/mepscore"
BACKUP_DIR="/var/backups/mepscore"
MONITORING_DIR="/opt/mepscore-monitoring"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root (use sudo)"
   exit 1
fi

print_status "Starting MEP Score deployment..."

# Step 1: Update system
print_status "Updating system packages..."
apt update && apt upgrade -y

# Step 2: Install required packages
print_status "Installing required packages..."
apt install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx sqlite3 git curl \
    htop iotop nethogs unzip fail2ban logrotate rsync cron \
    python3-dev build-essential libssl-dev libffi-dev \
    supervisor redis-server \
    nodejs npm

# Step 3: Create application directory structure
print_status "Creating application directory structure..."
mkdir -p $APP_DIR
mkdir -p $LOG_DIR
mkdir -p $BACKUP_DIR
mkdir -p $MONITORING_DIR
mkdir -p /var/cache/mepscore
mkdir -p /var/run/mepscore

cd $APP_DIR

# Step 4: Create virtual environment
print_status "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Step 5: Install Python dependencies
print_status "Installing Python dependencies..."
pip install --upgrade pip setuptools wheel
pip install requests tqdm certifi charset-normalizer idna urllib3 colorama flask flask-cors ijson gunicorn \
    psutil redis flask-limiter prometheus-client

# Step 6: Create www-data directories
print_status "Setting up directory permissions..."
chown -R www-data:www-data $APP_DIR
chmod -R 755 $APP_DIR

# Step 7: Configure Nginx
print_status "Configuring Nginx..."
cp deployment/nginx.conf $NGINX_CONFIG
ln -sf $NGINX_CONFIG /etc/nginx/sites-enabled/mepscore
rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
nginx -t
if [ $? -ne 0 ]; then
    print_error "Nginx configuration test failed!"
    exit 1
fi

# Step 8: Configure systemd service
print_status "Setting up systemd service..."
cp deployment/mepscore.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable mepscore

# Step 9: Start services
print_status "Starting services..."
systemctl start nginx
systemctl start mepscore

# Step 10: Configure firewall
print_status "Configuring firewall..."
ufw --force enable
ufw allow ssh
ufw allow 'Nginx Full'
ufw delete allow 'Nginx HTTP' 2>/dev/null || true

# Step 11: Setup SSL certificate
print_status "Setting up SSL certificate..."
print_warning "Make sure your domain $DOMAIN points to this server's IP address!"
echo "Would you like to set up SSL certificate now? (y/n)"
read -r response

if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    print_status "Obtaining SSL certificate..."
    certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos --email $EMAIL --redirect
    
    # Test SSL renewal
    certbot renew --dry-run
    
    # Setup auto-renewal
    (crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | crontab -
else
    print_warning "SSL certificate setup skipped. You can run it later with:"
    print_warning "sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN"
fi

# Step 12: Final service restart
print_status "Restarting services..."
systemctl restart mepscore
systemctl restart nginx

# Step 13: Apply security hardening
print_status "Applying security hardening..."

# Make security scripts executable
chmod +x deployment/security/security_hardening.sh
chmod +x deployment/security/security_audit.py

# Run security hardening
if [ -f "deployment/security/security_hardening.sh" ]; then
    print_status "Running security hardening script..."
    bash deployment/security/security_hardening.sh
else
    print_warning "Security hardening script not found, applying basic security measures..."
    
    # Basic SSH hardening
    print_status "Applying basic SSH security..."
    sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
    sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
    sed -i 's/PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
    
    # Enable UFW firewall
    print_status "Configuring basic firewall..."
    ufw --force reset
    ufw default deny incoming
    ufw default allow outgoing
    ufw allow ssh
    ufw allow 'Nginx Full'
    ufw --force enable
fi

# Step 14: Configure monitoring and logging
print_status "Setting up monitoring and logging..."

# Create log rotation configuration
cat > /etc/logrotate.d/mepscore << 'EOF'
/var/log/mepscore/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 www-data www-data
    postrotate
        systemctl reload mepscore
    endscript
}

/var/log/nginx/mepscore*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    sharedscripts
    postrotate
        systemctl reload nginx
    endscript
}
EOF

# Configure fail2ban for security
cat > /etc/fail2ban/jail.d/mepscore.conf << 'EOF'
[nginx-http-auth]
enabled = true
filter = nginx-http-auth
logpath = /var/log/nginx/mepscore_error.log
maxretry = 3
bantime = 3600

[nginx-noscript]
enabled = true
logpath = /var/log/nginx/mepscore_access.log
maxretry = 6
bantime = 3600

[nginx-badbots]
enabled = true
logpath = /var/log/nginx/mepscore_access.log
maxretry = 2
bantime = 86400
EOF

# Start fail2ban
systemctl enable fail2ban
systemctl start fail2ban

# Create monitoring script
cat > $MONITORING_DIR/health_check.sh << 'EOF'
#!/bin/bash
# MEP Score Health Check Script

LOG_FILE="/var/log/mepscore/health_check.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Check if services are running
check_service() {
    if systemctl is-active --quiet $1; then
        echo "[$TIMESTAMP] ✅ $1 service is running" >> $LOG_FILE
        return 0
    else
        echo "[$TIMESTAMP] ❌ $1 service is DOWN" >> $LOG_FILE
        return 1
    fi
}

# Check HTTP response
check_http() {
    local url=$1
    local expected_code=$2
    local response=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 $url)
    
    if [ "$response" = "$expected_code" ]; then
        echo "[$TIMESTAMP] ✅ $url responding correctly ($response)" >> $LOG_FILE
        return 0
    else
        echo "[$TIMESTAMP] ❌ $url not responding correctly (got $response, expected $expected_code)" >> $LOG_FILE
        return 1
    fi
}

# Check disk space
check_disk_space() {
    local usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ $usage -lt 90 ]; then
        echo "[$TIMESTAMP] ✅ Disk usage: ${usage}%" >> $LOG_FILE
        return 0
    else
        echo "[$TIMESTAMP] ⚠️  High disk usage: ${usage}%" >> $LOG_FILE
        return 1
    fi
}

# Check memory usage
check_memory() {
    local usage=$(free | awk 'FNR==2{printf "%.0f", $3/($3+$4)*100}')
    if [ $usage -lt 90 ]; then
        echo "[$TIMESTAMP] ✅ Memory usage: ${usage}%" >> $LOG_FILE
        return 0
    else
        echo "[$TIMESTAMP] ⚠️  High memory usage: ${usage}%" >> $LOG_FILE
        return 1
    fi
}

# Run checks
echo "[$TIMESTAMP] Starting health checks..." >> $LOG_FILE

check_service "mepscore"
MEPSCORE_STATUS=$?

check_service "nginx"
NGINX_STATUS=$?

check_http "http://localhost:8000/api/health" "200"
API_STATUS=$?

check_http "https://mepscore.eu/" "200"
SITE_STATUS=$?

check_disk_space
DISK_STATUS=$?

check_memory
MEMORY_STATUS=$?

# Overall status
if [ $MEPSCORE_STATUS -eq 0 ] && [ $NGINX_STATUS -eq 0 ] && [ $API_STATUS -eq 0 ] && [ $SITE_STATUS -eq 0 ] && [ $DISK_STATUS -eq 0 ] && [ $MEMORY_STATUS -eq 0 ]; then
    echo "[$TIMESTAMP] ✅ All health checks passed" >> $LOG_FILE
    exit 0
else
    echo "[$TIMESTAMP] ❌ Some health checks failed" >> $LOG_FILE
    
    # Try to restart services if they're down
    if [ $MEPSCORE_STATUS -ne 0 ]; then
        echo "[$TIMESTAMP] Attempting to restart mepscore service..." >> $LOG_FILE
        systemctl restart mepscore
    fi
    
    if [ $NGINX_STATUS -ne 0 ]; then
        echo "[$TIMESTAMP] Attempting to restart nginx service..." >> $LOG_FILE
        systemctl restart nginx
    fi
    
    exit 1
fi
EOF

chmod +x $MONITORING_DIR/health_check.sh

# Set up cron job for health checks (every 5 minutes)
(crontab -l 2>/dev/null; echo "*/5 * * * * $MONITORING_DIR/health_check.sh") | crontab -

# Set up daily backup script
cat > $MONITORING_DIR/backup.sh << 'EOF'
#!/bin/bash
# MEP Score Backup Script

BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/mepscore_backup_$BACKUP_DATE.tar.gz"

echo "Creating backup: $BACKUP_FILE"

# Create backup
tar -czf "$BACKUP_FILE" \
    --exclude='venv' \
    --exclude='node_modules' \
    --exclude='*.log' \
    --exclude='cache' \
    -C /var/www mepscore

# Keep only last 7 backups
find $BACKUP_DIR -name "mepscore_backup_*.tar.gz" -type f -mtime +7 -delete

echo "Backup completed: $BACKUP_FILE"
ls -lh "$BACKUP_FILE"
EOF

chmod +x $MONITORING_DIR/backup.sh

# Set up daily backup cron job (2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * $MONITORING_DIR/backup.sh") | crontab -

# Step 14: Set proper ownership and permissions
print_status "Setting final permissions and ownership..."
chown -R www-data:www-data $APP_DIR
chown -R www-data:www-data $LOG_DIR
chown -R www-data:www-data /var/cache/mepscore
chown -R www-data:www-data /var/run/mepscore
chmod 755 $APP_DIR
chmod 755 $LOG_DIR
chmod 755 $BACKUP_DIR
chmod 755 $MONITORING_DIR

# Step 15: Display status
print_status "Professional deployment completed!"
echo ""
echo "========================================"
echo "Deployment Summary"
echo "========================================"
echo "Application Directory: $APP_DIR"
echo "Log Directory: $LOG_DIR"
echo "Backup Directory: $BACKUP_DIR"
echo "Monitoring Directory: $MONITORING_DIR"
echo "Domain: $DOMAIN"
echo ""
echo "Services Status:"
systemctl status mepscore --no-pager -l
echo ""
systemctl status nginx --no-pager -l
echo ""
systemctl status fail2ban --no-pager -l
echo ""
echo "========================================"
echo "Management Commands:"
echo "• Health check: $MONITORING_DIR/health_check.sh"
echo "• Manual backup: $MONITORING_DIR/backup.sh"
echo "• View logs: tail -f $LOG_DIR/application.log"
echo "• Check health: curl https://$DOMAIN/api/health"
echo "• Service status: systemctl status mepscore nginx"
echo "========================================"
echo ""
echo "Security Features Enabled:"
echo "• Fail2ban protection against brute force"
echo "• Automated health checks every 5 minutes"
echo "• Daily automated backups at 2 AM"
echo "• Log rotation for disk space management"
echo "• SSL/TLS encryption with Let's Encrypt"
echo "========================================"

print_status "Professional deployment script completed successfully!"
print_status "Your MEP Score application is now production-ready!"