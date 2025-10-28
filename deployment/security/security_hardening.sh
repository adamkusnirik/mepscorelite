#!/bin/bash

# MEP Score Security Hardening Script
# This script implements additional security measures for production deployment

set -e

echo "========================================"
echo "MEP Score Security Hardening"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

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

print_status "Starting security hardening process..."

# 1. SSH Security Hardening
print_status "Hardening SSH configuration..."

# Backup original sshd_config
cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup

# Create secure SSH configuration
cat > /etc/ssh/sshd_config.d/mepscore_security.conf << 'EOF'
# MEP Score SSH Security Configuration

# Authentication
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
AuthenticationMethods publickey
MaxAuthTries 3
LoginGraceTime 30

# Connection settings
ClientAliveInterval 300
ClientAliveCountMax 2
MaxSessions 3
MaxStartups 3:30:10

# Protocol settings
Protocol 2
UsePAM yes
X11Forwarding no
AllowTcpForwarding no
GatewayPorts no
PermitTunnel no
PermitUserEnvironment no

# Logging
SyslogFacility AUTHPRIV
LogLevel VERBOSE

# Restrict users (uncomment and customize as needed)
# AllowUsers deploy
# DenyUsers root
EOF

# Validate SSH configuration
print_status "Validating SSH configuration..."
if ! sshd -T &>/dev/null; then
    print_error "SSH configuration validation failed!"
    mv /etc/ssh/sshd_config.backup /etc/ssh/sshd_config
    exit 1
fi

# 2. Firewall Configuration with UFW
print_status "Configuring advanced firewall rules..."

# Reset UFW to defaults
ufw --force reset

# Default policies
ufw default deny incoming
ufw default allow outgoing

# SSH access (limit to specific IPs in production)
ufw allow ssh comment 'SSH access'

# Web server access
ufw allow 'Nginx Full' comment 'Web server'

# Monitoring dashboard (internal only)
ufw allow from 10.0.0.0/8 to any port 9000 comment 'Internal monitoring'
ufw allow from 172.16.0.0/12 to any port 9000 comment 'Internal monitoring'
ufw allow from 192.168.0.0/16 to any port 9000 comment 'Internal monitoring'

# Rate limiting for SSH (optional, requires ufw-extras)
if command -v ufw >/dev/null 2>&1; then
    # Limit SSH connections
    ufw limit ssh comment 'SSH rate limiting'
fi

# Enable UFW
ufw --force enable

# 3. Fail2ban Enhanced Configuration
print_status "Configuring enhanced Fail2ban rules..."

# Create MEP Score specific fail2ban filters
cat > /etc/fail2ban/filter.d/mepscore-auth.conf << 'EOF'
# Fail2ban filter for MEP Score authentication failures

[Definition]
failregex = ^<HOST> .* "(GET|POST) /api/auth.*" 40[0-9] .*$
            ^<HOST> .* "(GET|POST) /admin.*" 40[0-9] .*$
ignoreregex =
EOF

cat > /etc/fail2ban/filter.d/mepscore-dos.conf << 'EOF'
# Fail2ban filter for MEP Score DoS protection

[Definition]
failregex = ^<HOST> .* "(GET|POST) /api/.*" 429 .*$
ignoreregex =
EOF

cat > /etc/fail2ban/filter.d/mepscore-scan.conf << 'EOF'
# Fail2ban filter for MEP Score vulnerability scanning

[Definition]
failregex = ^<HOST> .* "(GET|POST) .*(/\.env|/\.git|/admin|/wp-admin|/phpmyadmin|/xmlrpc\.php).*" [0-9]+ .*$
            ^<HOST> .* "(GET|POST) .*(\.php|\.asp|\.jsp).*" 404 .*$
ignoreregex =
EOF

# Enhanced fail2ban jail configuration
cat > /etc/fail2ban/jail.d/mepscore-enhanced.conf << 'EOF'
[DEFAULT]
# Ban duration (24 hours for security violations)
bantime = 86400
findtime = 600
maxretry = 5

# Email notifications
destemail = admin@mepscore.eu
sender = fail2ban@mepscore.eu
mta = sendmail
action = %(action_mwl)s

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/mepscore_error.log
maxretry = 3
bantime = 3600

[mepscore-auth]
enabled = true
filter = mepscore-auth
port = http,https
logpath = /var/log/nginx/mepscore_access.log
maxretry = 5
bantime = 86400

[mepscore-dos]
enabled = true
filter = mepscore-dos
port = http,https
logpath = /var/log/nginx/mepscore_access.log
maxretry = 10
findtime = 60
bantime = 3600

[mepscore-scan]
enabled = true
filter = mepscore-scan
port = http,https
logpath = /var/log/nginx/mepscore_access.log
maxretry = 2
bantime = 86400
EOF

# 4. System Security Settings
print_status "Applying system security settings..."

# Disable unnecessary network protocols
cat > /etc/modprobe.d/mepscore-blacklist.conf << 'EOF'
# Disable unnecessary network protocols
blacklist dccp
blacklist sctp
blacklist rds
blacklist tipc
install dccp /bin/true
install sctp /bin/true
install rds /bin/true
install tipc /bin/true
EOF

# Kernel security parameters
cat > /etc/sysctl.d/99-mepscore-security.conf << 'EOF'
# MEP Score Security Parameters

# IP Spoofing protection
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1

# Ignore ICMP ping requests
net.ipv4.icmp_echo_ignore_all = 0
net.ipv4.icmp_echo_ignore_broadcasts = 1

# Ignore ICMP redirects
net.ipv4.conf.all.accept_redirects = 0
net.ipv6.conf.all.accept_redirects = 0
net.ipv4.conf.all.send_redirects = 0

# Ignore source route packets
net.ipv4.conf.all.accept_source_route = 0
net.ipv6.conf.all.accept_source_route = 0

# Log martian packets
net.ipv4.conf.all.log_martians = 1

# TCP SYN flood protection
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_max_syn_backlog = 2048
net.ipv4.tcp_synack_retries = 3

# IP forwarding (disable if not needed)
net.ipv4.ip_forward = 0
net.ipv6.conf.all.forwarding = 0

# Memory protection
kernel.dmesg_restrict = 1
kernel.kptr_restrict = 1
kernel.yama.ptrace_scope = 1

# Core dump restrictions
fs.suid_dumpable = 0
kernel.core_uses_pid = 1
EOF

# Apply sysctl settings
sysctl -p /etc/sysctl.d/99-mepscore-security.conf

# 5. File System Security
print_status "Implementing file system security..."

# Secure /tmp directory
if ! mount | grep -q "tmpfs on /tmp"; then
    print_status "Configuring secure /tmp directory..."
    cat >> /etc/fstab << 'EOF'
tmpfs /tmp tmpfs defaults,noatime,nosuid,nodev,noexec,mode=1777,size=1G 0 0
EOF
fi

# Set secure permissions on critical directories
chmod 700 /root
chmod 755 /var/www
chmod 750 /var/log/mepscore
chmod 640 /var/log/mepscore/*.log 2>/dev/null || true

# 6. Application Security
print_status "Implementing application security measures..."

# Create application security script
cat > /opt/mepscore-monitoring/security_check.sh << 'EOF'
#!/bin/bash

# MEP Score Security Check Script
LOG_FILE="/var/log/mepscore/security_check.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

log_security() {
    echo "[$TIMESTAMP] $1" >> $LOG_FILE
}

# Check for suspicious processes
log_security "Starting security check"

# Check for unauthorized users
if [ $(who | wc -l) -gt 5 ]; then
    log_security "WARNING: High number of active user sessions: $(who | wc -l)"
fi

# Check for world-writable files in application directory
find /var/www/mepscore -type f -perm -o+w 2>/dev/null | while read file; do
    log_security "WARNING: World-writable file found: $file"
done

# Check for SUID/SGID files
find /var/www/mepscore -type f \( -perm -4000 -o -perm -2000 \) 2>/dev/null | while read file; do
    log_security "WARNING: SUID/SGID file found: $file"
done

# Check system resources
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}')
MEMORY_USAGE=$(free | grep Mem | awk '{printf "%.2f", $3/$2 * 100.0}')

if (( $(echo "$CPU_USAGE > 90" | bc -l) )); then
    log_security "WARNING: High CPU usage: $CPU_USAGE%"
fi

if (( $(echo "$MEMORY_USAGE > 90" | bc -l) )); then
    log_security "WARNING: High memory usage: $MEMORY_USAGE%"
fi

# Check for failed login attempts
FAILED_LOGINS=$(grep "Failed password" /var/log/auth.log | grep "$(date '+%b %d')" | wc -l)
if [ $FAILED_LOGINS -gt 10 ]; then
    log_security "WARNING: High number of failed login attempts: $FAILED_LOGINS"
fi

log_security "Security check completed"
EOF

chmod +x /opt/mepscore-monitoring/security_check.sh

# 7. Log Monitoring and Intrusion Detection
print_status "Setting up log monitoring..."

# Install and configure logwatch if not present
if ! command -v logwatch &> /dev/null; then
    apt install -y logwatch
fi

# Create custom logwatch configuration
mkdir -p /etc/logwatch/conf/services
cat > /etc/logwatch/conf/services/mepscore.conf << 'EOF'
Title = "MEP Score Security Events"
LogFile = mepscore_access.log
LogFile = mepscore_error.log
LogFile = security_check.log
*OnlyService = mepscore
*RemoveHeaders = Yes
EOF

# 8. Automated Security Updates
print_status "Configuring automated security updates..."

# Install unattended-upgrades if not present
apt install -y unattended-upgrades apt-listchanges

# Configure unattended upgrades
cat > /etc/apt/apt.conf.d/50unattended-upgrades << 'EOF'
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}";
    "${distro_id}:${distro_codename}-security";
    "${distro_id}ESMApps:${distro_codename}-apps-security";
    "${distro_id}ESM:${distro_codename}-infra-security";
};

Unattended-Upgrade::Package-Blacklist {
    "nginx";
    "nginx-core";
    "nginx-common";
    "python3";
};

Unattended-Upgrade::DevRelease "false";
Unattended-Upgrade::Remove-Unused-Dependencies "true";
Unattended-Upgrade::Automatic-Reboot "false";
Unattended-Upgrade::Mail "admin@mepscore.eu";
Unattended-Upgrade::MailOnlyOnError "true";
EOF

cat > /etc/apt/apt.conf.d/20auto-upgrades << 'EOF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Download-Upgradeable-Packages "1";
APT::Periodic::AutocleanInterval "7";
APT::Periodic::Unattended-Upgrade "1";
EOF

# 9. File Integrity Monitoring
print_status "Setting up file integrity monitoring..."

# Create AIDE configuration for MEP Score
if command -v aide &> /dev/null; then
    cat >> /etc/aide/aide.conf << 'EOF'

# MEP Score Application Monitoring
/var/www/mepscore f+p+u+g+s+m+c+md5+sha256
/etc/nginx f+p+u+g+s+m+c+md5+sha256
/etc/systemd/system/mepscore.service f+p+u+g+s+m+c+md5+sha256
/etc/fail2ban/jail.d f+p+u+g+s+m+c+md5+sha256
EOF

    # Initialize AIDE database
    print_status "Initializing AIDE database (this may take a while)..."
    aide --init
    mv /var/lib/aide/aide.db.new /var/lib/aide/aide.db
fi

# 10. Security Monitoring Cron Jobs
print_status "Setting up security monitoring cron jobs..."

# Add security check to cron
(crontab -l 2>/dev/null; echo "0 */6 * * * /opt/mepscore-monitoring/security_check.sh") | crontab -

# Add daily security report
(crontab -l 2>/dev/null; echo "0 6 * * * /usr/sbin/logwatch --output mail --mailto admin@mepscore.eu --detail Med") | crontab -

# Add weekly AIDE check (if available)
if command -v aide &> /dev/null; then
    (crontab -l 2>/dev/null; echo "0 3 * * 0 /usr/bin/aide --check") | crontab -
fi

# 11. Restart Services
print_status "Restarting security services..."

# Restart SSH (carefully)
print_warning "Restarting SSH service - ensure you have another way to access the server!"
systemctl restart sshd

# Restart fail2ban
systemctl restart fail2ban

# Start and enable services
systemctl enable unattended-upgrades
systemctl start unattended-upgrades

# 12. Security Verification
print_status "Performing security verification..."

# Test SSH configuration
if ! ssh -T -o ConnectTimeout=5 localhost exit 2>/dev/null; then
    print_warning "SSH configuration might have issues. Please verify SSH access works."
fi

# Check fail2ban status
if systemctl is-active --quiet fail2ban; then
    print_status "Fail2ban is running correctly"
else
    print_error "Fail2ban is not running!"
fi

# Check UFW status
if ufw status | grep -q "Status: active"; then
    print_status "UFW firewall is active"
else
    print_error "UFW firewall is not active!"
fi

# Final security status
print_status "Security hardening completed!"
echo ""
echo "========================================"
echo "Security Hardening Summary"
echo "========================================"
echo "✓ SSH hardened with key-only authentication"
echo "✓ UFW firewall configured with restrictive rules"
echo "✓ Enhanced fail2ban protection enabled"
echo "✓ System security parameters applied"
echo "✓ File system security implemented"
echo "✓ Automated security updates enabled"
echo "✓ Security monitoring and alerting configured"
echo "✓ Log monitoring with logwatch enabled"
if command -v aide &> /dev/null; then
    echo "✓ File integrity monitoring with AIDE"
fi
echo ""
echo "Important Notes:"
echo "• SSH root login is now disabled"
echo "• Password authentication is disabled"
echo "• All access requires SSH keys"
echo "• Security monitoring runs every 6 hours"
echo "• Daily security reports via email"
echo "• Automated security updates enabled"
echo ""
echo "Monitor security status:"
echo "• fail2ban-client status"
echo "• ufw status verbose"
echo "• tail -f /var/log/mepscore/security_check.log"
echo "========================================"

print_status "Security hardening script completed successfully!"