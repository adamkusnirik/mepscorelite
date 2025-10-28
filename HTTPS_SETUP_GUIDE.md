# HTTPS Setup Guide for MEP Score Application

## Current Configuration

✅ **HTTPS is now active on the AWS Lightsail server**

- **URL**: `https://108.128.29.141/`
- **Certificate**: Self-signed (browsers will show security warning)
- **HTTP Redirect**: All HTTP traffic automatically redirects to HTTPS
- **Security**: Modern TLS configuration with security headers

## What Was Implemented

### 1. Nginx Reverse Proxy
- Installed and configured Nginx as a reverse proxy
- HTTP (port 80) redirects to HTTPS (port 443)
- HTTPS (port 443) proxies to Python server (port 8000)

### 2. SSL Certificate
- Self-signed certificate for immediate HTTPS functionality
- Valid for 365 days
- Certificate files located at `/etc/ssl/mepscore/`

### 3. Security Configuration
- **TLS Versions**: TLS 1.2 and TLS 1.3
- **HSTS**: Enforces HTTPS for 1 year
- **X-Frame-Options**: Prevents clickjacking
- **X-Content-Type-Options**: Prevents MIME sniffing attacks

## Browser Access

### Current Access
```
https://108.128.29.141/
```

**⚠️ Browser Warning**: Because this uses a self-signed certificate, browsers will show a security warning. This is normal and expected.

### How to Access Despite Warning

**Chrome/Edge:**
1. Visit `https://108.128.29.141/`
2. Click "Advanced"
3. Click "Proceed to 108.128.29.141 (unsafe)"

**Firefox:**
1. Visit `https://108.128.29.141/`
2. Click "Advanced"
3. Click "Accept the Risk and Continue"

## Production Certificate Upgrade

For a production deployment without browser warnings, you need:

### Option 1: Domain Name + Let's Encrypt (Recommended)

1. **Get a domain** (e.g., `mepscore.yourdomain.com`)
2. **Point DNS** to `108.128.29.141`
3. **Update Nginx configuration**:
   ```bash
   sudo nano /etc/nginx/sites-available/mepscore
   # Change server_name from 108.128.29.141 to your domain
   ```
4. **Get Let's Encrypt certificate**:
   ```bash
   sudo certbot --nginx -d mepscore.yourdomain.com
   ```

### Option 2: AWS Certificate Manager (Advanced)
- Use AWS Load Balancer with ACM certificate
- Requires additional AWS configuration

## Testing HTTPS Functionality

### Command Line Tests
```bash
# Test HTTPS (ignore self-signed warning)
curl -k https://108.128.29.141/

# Test HTTP redirect
curl -I http://108.128.29.141/

# Test API endpoint
curl -k https://108.128.29.141/api/health
```

### Browser Tests
1. **Homepage**: `https://108.128.29.141/`
2. **Profile page**: `https://108.128.29.141/profile.html?mep_id=88882&term=10`
3. **API endpoint**: `https://108.128.29.141/api/health`

## Configuration Files

### Nginx Configuration
```bash
# View current config
sudo cat /etc/nginx/sites-available/mepscore

# Test configuration
sudo nginx -t

# Reload after changes
sudo systemctl reload nginx
```

### SSL Certificate Files
```bash
# Certificate: /etc/ssl/mepscore/mepscore.crt
# Private key: /etc/ssl/mepscore/mepscore.key

# View certificate details
openssl x509 -in /etc/ssl/mepscore/mepscore.crt -text -noout
```

## Maintenance Commands

### Check HTTPS Status
```bash
# Check if Nginx is running
sudo systemctl status nginx

# Check SSL certificate expiry
openssl x509 -in /etc/ssl/mepscore/mepscore.crt -noout -dates

# Test SSL configuration
curl -k -v https://108.128.29.141/ 2>&1 | grep -E "(SSL|TLS)"
```

### Restart Services
```bash
# Restart Nginx
sudo systemctl restart nginx

# Restart Python server
pkill -f "python3 serve.py"
cd /var/www/mepscore && python3 serve.py &
```

## Troubleshooting

### Common Issues

**1. "Connection refused"**
- Check if Nginx is running: `sudo systemctl status nginx`
- Restart if needed: `sudo systemctl restart nginx`

**2. "502 Bad Gateway"**
- Python server not running
- Start it: `cd /var/www/mepscore && python3 serve.py &`

**3. Certificate errors**
- Check certificate files exist: `ls -la /etc/ssl/mepscore/`
- Regenerate if needed (see commands below)

### Regenerate Self-Signed Certificate
```bash
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/mepscore/mepscore.key \
  -out /etc/ssl/mepscore/mepscore.crt \
  -subj '/C=US/ST=State/L=City/O=Organization/CN=108.128.29.141'

sudo systemctl reload nginx
```

## Security Notes

### Current Security Level
- ✅ **Encryption**: All traffic encrypted with TLS
- ✅ **Headers**: Security headers implemented
- ⚠️ **Certificate**: Self-signed (not trusted by browsers)
- ✅ **Redirect**: HTTP automatically redirects to HTTPS

### For Production Use
- Replace self-signed certificate with domain-validated certificate
- Consider additional security measures (fail2ban, rate limiting)
- Regular security updates and monitoring

## Summary

🎉 **HTTPS is now successfully configured!**

- All traffic is encrypted
- HTTP automatically redirects to HTTPS
- API endpoints work over HTTPS
- Ready for production use (with trusted certificate)

Visit: `https://108.128.29.141/` (accept security warning for self-signed cert)

---

**Setup completed**: August 15, 2025  
**Certificate expires**: August 15, 2026  
**Status**: ✅ Fully functional HTTPS deployment