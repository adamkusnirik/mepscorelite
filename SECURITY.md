# MEP Score Security Documentation

This document outlines the comprehensive security measures implemented in the MEP Score application deployment system.

## 🛡️ Security Architecture Overview

The MEP Score security implementation follows defense-in-depth principles with multiple layers of protection:

```
┌─────────────────────────────────────────────────────────────────┐
│                        Security Layers                         │
│                                                                 │
│  ┌─────────────────┐    ┌──────────────────────────────────┐   │
│  │   Network       │    │         Application              │   │
│  │                 │    │                                  │   │
│  │ • UFW Firewall  │───▶│ • Input Validation              │   │
│  │ • Rate Limiting │    │ • Security Headers              │   │
│  │ • Fail2ban      │    │ • Access Controls               │   │
│  │ • DDoS Protection    │ • Error Handling                │   │
│  └─────────────────┘    └──────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────┐    ┌──────────────────────────────────┐   │
│  │    System       │    │          Monitoring             │   │
│  │                 │    │                                  │   │
│  │ • SSH Hardening │───▶│ • Security Auditing            │   │
│  │ • File Permissions   │ • Log Analysis                 │   │
│  │ • Service Security   │ • Intrusion Detection          │   │
│  │ • Auto Updates  │    │ • Alert System                 │   │
│  └─────────────────┘    └──────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## 🔐 Authentication & Access Control

### SSH Security
- **Root login disabled**: `PermitRootLogin no`
- **Password authentication disabled**: `PasswordAuthentication no`
- **Key-based authentication only**: `PubkeyAuthentication yes`
- **Connection limits**: `MaxSessions 3`, `MaxStartups 3:30:10`
- **Login grace time**: 30 seconds timeout
- **Failed attempt limits**: Maximum 3 attempts

### Web Application Access
- **HTTPS enforced**: HTTP redirects to HTTPS
- **Modern TLS only**: TLS 1.2 and 1.3
- **Strong cipher suites**: ECDHE and ChaCha20 ciphers
- **HSTS enabled**: Strict-Transport-Security with preload

### Database Security
- **File permissions**: 640 (owner: www-data, group: www-data)
- **No network access**: SQLite file-based, no network exposure
- **Connection timeouts**: 10-second timeout for database operations
- **Query parameterization**: All queries use prepared statements

## 🌐 Network Security

### Firewall Configuration (UFW)
```bash
# Default policies
ufw default deny incoming
ufw default allow outgoing

# Allowed services
Port 22/tcp (SSH) - Limited rate limiting
Port 80/tcp (HTTP) - Redirect to HTTPS only
Port 443/tcp (HTTPS) - Main web traffic
Port 9000/tcp (Monitoring) - Internal networks only
```

### Rate Limiting (Nginx)
- **API endpoints**: 10 requests/second per IP
- **General pages**: 30 requests/second per IP  
- **Static files**: 50 requests/second per IP
- **Connection limits**: 20 concurrent connections per IP

### DDoS Protection
- **SYN flood protection**: `net.ipv4.tcp_syncookies = 1`
- **Connection tracking**: `net.ipv4.tcp_max_syn_backlog = 2048`
- **Rate limiting**: Multi-tier rate limiting in Nginx
- **Fail2ban integration**: Automatic IP banning for abuse

## 🚫 Intrusion Detection & Prevention

### Fail2ban Configuration

**SSH Protection:**
- **Max attempts**: 3 failed logins
- **Ban duration**: 1 hour
- **Log monitoring**: `/var/log/auth.log`

**Web Application Protection:**
- **HTTP auth failures**: 3 attempts → 1 hour ban
- **DoS patterns**: 10 requests/minute → 1 hour ban
- **Vulnerability scanning**: 2 attempts → 24 hour ban

**Custom Filters:**
```bash
# Authentication failures
/api/auth/* returning 40x status codes

# DoS patterns  
/api/* returning 429 (rate limited) status codes

# Vulnerability scanning
Requests for .env, .git, admin panels, PHP files
```

### Security Monitoring
- **System metrics**: CPU, memory, disk, network monitored every 5 minutes
- **Log analysis**: Access logs analyzed hourly for threats
- **File integrity**: AIDE monitoring for critical files (optional)
- **Security audits**: Automated security scans

## 📡 Security Headers & Policies

### HTTP Security Headers
```nginx
# HTTPS enforcement
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload

# Content Security Policy
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; 
                        style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com;

# Clickjacking protection  
X-Frame-Options: DENY

# MIME sniffing protection
X-Content-Type-Options: nosniff

# XSS filtering
X-XSS-Protection: 1; mode=block

# Referrer policy
Referrer-Policy: strict-origin-when-cross-origin

# Permissions policy
Permissions-Policy: geolocation=(), microphone=(), camera=(), payment=()
```

### File Access Protection
```nginx
# Block sensitive files
location ~ /\. { deny all; }
location ~ \.(ini|conf|log|bak|tmp|backup|old)$ { deny all; }
location ~ /(.git|.svn|.env|composer|package) { deny all; }

# Security.txt for responsible disclosure
location = /.well-known/security.txt {
    return 200 "Contact: security@mepscore.eu\nExpires: 2025-12-31T23:59:59.000Z\n";
}
```

## 🔍 Logging & Monitoring

### Security Log Analysis
- **Access patterns**: Geographic analysis, bot detection
- **Failed requests**: 4xx/5xx error monitoring  
- **Suspicious activity**: High request rates, scan attempts
- **User agent analysis**: Bot vs human traffic classification

### Alert Triggers
| Event Type | Threshold | Action |
|------------|-----------|--------|
| Failed SSH logins | 10/day | Email alert |
| High error rate | >5% | Email alert |
| Suspicious requests | >50/minute from single IP | Auto-ban + alert |
| System resource usage | CPU/Memory >90% | Email alert |
| Security scan attempts | Any | Auto-ban + log |

### Log Retention
- **Application logs**: 30 days rotation
- **Access logs**: 30 days rotation  
- **Security logs**: 90 days retention
- **Monitoring data**: 30 days in database

## 🔧 System Hardening

### Kernel Security Parameters
```bash
# IP spoofing protection
net.ipv4.conf.all.rp_filter = 1

# Ignore ICMP redirects
net.ipv4.conf.all.accept_redirects = 0
net.ipv6.conf.all.accept_redirects = 0

# Source route protection
net.ipv4.conf.all.accept_source_route = 0
net.ipv6.conf.all.accept_source_route = 0

# TCP SYN flood protection
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_max_syn_backlog = 2048

# Memory protection
kernel.dmesg_restrict = 1
kernel.kptr_restrict = 1
kernel.yama.ptrace_scope = 1
```

### File System Security
- **Secure /tmp**: tmpfs with noexec, nosuid, nodev
- **Root directory**: 700 permissions
- **Application files**: www-data ownership, 755 directories, 644 files
- **Log files**: 640 permissions, proper ownership
- **Database files**: 640 permissions, restricted access

### Service Security
- **Service isolation**: systemd with PrivateTmp=true
- **User separation**: www-data user for web services
- **Resource limits**: Memory and CPU limits for services
- **Process monitoring**: Automated restart on failure

## 🚨 Incident Response

### Automated Response
1. **Rate limiting exceeded**: Automatic temporary IP ban
2. **Security scan detected**: Permanent IP ban
3. **Service failure**: Automatic service restart attempt
4. **High resource usage**: Alert administrators
5. **Failed authentication**: Progressive ban duration

### Manual Response Procedures

**Security Breach Suspected:**
```bash
# 1. Immediate containment
sudo ufw deny from suspicious_ip
sudo fail2ban-client set nginx-http-auth banip suspicious_ip

# 2. Investigation
tail -f /var/log/nginx/mepscore_access.log
grep suspicious_ip /var/log/nginx/mepscore_access.log
python3 /opt/mepscore-monitoring/security_audit.py

# 3. Recovery
sudo systemctl restart mepscore nginx
sudo fail2ban-client reload
```

**DDoS Attack:**
```bash
# Emergency rate limiting
sudo nano /etc/nginx/sites-available/mepscore
# Add: limit_req_zone $binary_remote_addr zone=emergency:10m rate=1r/s;

# Monitor connections
watch 'netstat -an | grep :443 | wc -l'

# Block attack sources
sudo fail2ban-client set nginx-http-auth banip attacker_ip
```

### Recovery Procedures
1. **Service restoration**: Automated rollback to last known good state
2. **Data integrity check**: Database verification and repair
3. **Security audit**: Complete system security scan
4. **Monitoring review**: Analysis of attack vectors and improvements

## 🔄 Security Maintenance

### Daily (Automated)
- System backups with integrity verification
- Security log analysis and threat detection
- Resource monitoring and alerting
- Service health checks

### Weekly (Recommended)
```bash
# Security updates check
sudo apt update && sudo apt list --upgradable | grep security

# SSL certificate status
sudo certbot certificates

# Fail2ban status review
sudo fail2ban-client status

# Security audit
python3 /opt/mepscore-monitoring/security_audit.py
```

### Monthly (Required)
```bash
# Complete security audit
python3 /deployment/security/security_audit.py

# Review banned IPs
sudo fail2ban-client status nginx-http-auth

# Log analysis review
sudo find /var/log -name "*.log" -size +100M

# Update security policies
# Review and update firewall rules
# Review and update fail2ban configuration
```

### Quarterly (Recommended)
- **Penetration testing**: External security assessment
- **Vulnerability scanning**: Automated security scanning
- **Security policy review**: Update security procedures
- **Staff security training**: Security awareness updates

## 📋 Compliance & Standards

### Security Standards Compliance
- **OWASP Top 10**: Protection against common web vulnerabilities
- **SSL/TLS**: Modern encryption standards (TLS 1.2/1.3)
- **HTTP Security**: Standard security headers implemented
- **Access Control**: Principle of least privilege

### Data Protection
- **Encryption at rest**: File system encryption (optional)
- **Encryption in transit**: HTTPS/TLS for all connections
- **Database security**: Local SQLite with restricted access
- **Backup encryption**: Encrypted backup storage (configurable)

### Audit Trail
- **Access logging**: All web requests logged
- **Authentication logging**: SSH and system access logged
- **Configuration changes**: System changes tracked
- **Security events**: All security incidents logged and alerted

## 🔧 Security Configuration Files

### Key Configuration Files
```
/etc/nginx/sites-available/mepscore       # Web server security config
/etc/ssh/sshd_config.d/mepscore_security.conf  # SSH hardening
/etc/fail2ban/jail.d/mepscore-enhanced.conf     # Intrusion prevention
/etc/ufw/applications.d/mepscore         # Firewall application rules
/etc/sysctl.d/99-mepscore-security.conf  # Kernel security parameters
/etc/logrotate.d/mepscore                # Log rotation security
```

### Security Scripts
```
deployment/security/security_hardening.sh  # System hardening script
deployment/security/security_audit.py      # Security audit tool
deployment/monitoring/system_monitor.py    # Security monitoring
deployment/monitoring/log_analyzer.py      # Log analysis and alerts
```

## 🚀 Quick Security Checklist

### Pre-Deployment Security
- [ ] SSH keys configured, passwords disabled
- [ ] Firewall rules configured and tested
- [ ] SSL certificates obtained and configured
- [ ] Security headers implemented
- [ ] Rate limiting configured
- [ ] Monitoring and alerting set up

### Post-Deployment Verification
- [ ] Run security audit: `python3 deployment/security/security_audit.py`
- [ ] Test firewall rules: `nmap -sT your-domain.com`
- [ ] Verify SSL configuration: `ssllabs.com/ssltest/`
- [ ] Check security headers: `securityheaders.com`
- [ ] Test fail2ban: Monitor logs during test attacks
- [ ] Verify monitoring: Check dashboard and alerts

### Ongoing Security Maintenance
- [ ] Weekly security updates: `apt update && apt upgrade`
- [ ] Monthly security audits
- [ ] Quarterly security reviews
- [ ] Annual penetration testing
- [ ] Regular backup testing
- [ ] Incident response plan testing

## 📞 Security Contacts

### Emergency Response
- **System Administrator**: admin@mepscore.eu
- **Security Team**: security@mepscore.eu
- **24/7 Monitoring**: Via configured alerting system

### Responsible Disclosure
Security vulnerabilities should be reported to: **security@mepscore.eu**

**Please include:**
- Description of the vulnerability
- Steps to reproduce
- Potential impact assessment
- Suggested remediation (if available)

**Response Timeline:**
- Initial acknowledgment: 24 hours
- Preliminary assessment: 72 hours  
- Resolution timeline: Based on severity
- Public disclosure: After fix deployment

---

This security documentation is reviewed and updated regularly to reflect current threats and best practices. Last updated: 2025-08-14