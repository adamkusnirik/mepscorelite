# AWS Lightsail Deployment Guide for MEP Score (mepscore.eu)

This comprehensive guide will help you deploy your MEP Score application to AWS Lightsail with zero previous experience.

## Prerequisites

- AWS account
- Domain name: mepscore.eu (registered)
- Basic command line knowledge
- Your application files ready

## Part 1: AWS Lightsail Setup

### Step 1: Create Lightsail Instance

1. **Login to AWS Console**
   - Go to [aws.amazon.com](https://aws.amazon.com)
   - Sign in to your AWS account
   - Search for "Lightsail" and click on it

2. **Create Instance**
   - Click "Create instance"
   - Choose region: **Europe (Ireland)** (eu-west-1) for better performance in Europe
   - Select platform: **Linux/Unix**
   - Select blueprint: **Ubuntu 20.04 LTS**

3. **Choose Instance Plan**
   - **Recommended for starting**: $10/month (2GB RAM, 1vCPU, 60GB SSD)
   - **For higher traffic**: $20/month (4GB RAM, 2vCPU, 80GB SSD)
   - You can upgrade later if needed

4. **Configure Instance**
   - Instance name: `mepscore-server`
   - Add tags (optional): 
     - Key: `Project`, Value: `MEP Score`
     - Key: `Environment`, Value: `Production`

5. **Create Instance**
   - Click "Create instance"
   - Wait 2-3 minutes for the instance to be ready

### Step 2: Configure Networking

1. **Get Static IP**
   - In Lightsail console, go to "Networking" tab
   - Click "Create static IP"
   - Select your instance: `mepscore-server`
   - Name: `mepscore-static-ip`
   - Click "Create"
   - **Note down this IP address** - you'll need it for DNS

2. **Configure Firewall**
   - Go to your instance
   - Click "Networking" tab
   - Under "Firewall", ensure these ports are open:
     - SSH (22) - Restrict to your IP for security
     - HTTP (80) - Source: Anywhere
     - HTTPS (443) - Source: Anywhere

## Part 2: Domain Configuration

### Step 3: Configure DNS for mepscore.eu

You need to point your domain to your Lightsail instance. Here are instructions for common registrars:

#### Option A: Using AWS Lightsail DNS (Recommended)

1. **Create DNS Zone in Lightsail**
   - In Lightsail console, go to "Networking" → "DNS zones"
   - Click "Create DNS zone"
   - Enter domain: `mepscore.eu`
   - Click "Create DNS zone"

2. **Configure DNS Records**
   - **A record**: `@` → Your Static IP Address
   - **A record**: `www` → Your Static IP Address
   - **CNAME record**: `www.mepscore.eu` → `mepscore.eu`

3. **Update Nameservers at Registrar**
   - Note the nameservers shown in Lightsail (e.g., ns-123.awsdns-12.com)
   - Login to your domain registrar
   - Update nameservers to use AWS nameservers
   - **This can take 24-48 hours to propagate**

#### Option B: Using Your Registrar's DNS

If you prefer to keep your current DNS provider:

1. **Add A Records**
   - `@` (root domain) → Your Static IP Address
   - `www` → Your Static IP Address

2. **Verify DNS Propagation**
   - Use [whatsmydns.net](https://whatsmydns.net) to check if your domain points to your server
   - Enter `mepscore.eu` and check A record
   - It should show your Lightsail static IP

## Part 3: Server Setup

### Step 4: Connect to Your Server

1. **Download SSH Key**
   - In Lightsail console, go to your instance
   - Click "Connect" tab
   - Download the default key pair
   - Save as `LightsailDefaultKey-eu-west-1.pem`

2. **Connect via SSH**

   **On Windows (using PowerShell or Command Prompt):**
   ```powershell
   # Set proper permissions on the key file
   icacls "path\to\LightsailDefaultKey-eu-west-1.pem" /reset
   icacls "path\to\LightsailDefaultKey-eu-west-1.pem" /inheritance:r /grant:r "%username%:R"
   
   # Connect to server
   ssh -i "path\to\LightsailDefaultKey-eu-west-1.pem" ubuntu@YOUR_STATIC_IP
   ```

   **On macOS/Linux:**
   ```bash
   chmod 400 ~/Downloads/LightsailDefaultKey-eu-west-1.pem
   ssh -i ~/Downloads/LightsailDefaultKey-eu-west-1.pem ubuntu@YOUR_STATIC_IP
   ```

3. **First Login**
   - Type `yes` when asked about host authenticity
   - You should see the Ubuntu welcome message

### Step 5: Upload Your Application Files

1. **Prepare Upload Script**
   - Edit `deployment/upload_files.sh` on your local machine
   - Replace `YOUR_LIGHTSAIL_IP` with your actual static IP
   - Update `KEY_PATH` to point to your downloaded key file

2. **Run Upload Script**
   ```bash
   # On Windows (using Git Bash or WSL)
   bash deployment/upload_files.sh
   
   # On macOS/Linux
   chmod +x deployment/upload_files.sh
   ./deployment/upload_files.sh
   ```

3. **Manual Upload Alternative**
   If the script fails, upload files manually:
   ```bash
   # Create directory
   ssh -i "KEY_PATH" ubuntu@YOUR_IP "sudo mkdir -p /var/www/mepscore"
   
   # Upload files
   scp -i "KEY_PATH" -r ./* ubuntu@YOUR_IP:/tmp/mepscore/
   ssh -i "KEY_PATH" ubuntu@YOUR_IP "sudo mv /tmp/mepscore/* /var/www/mepscore/"
   ```

### Step 6: Run Deployment Script

1. **Connect to Server**
   ```bash
   ssh -i "KEY_PATH" ubuntu@YOUR_STATIC_IP
   ```

2. **Navigate to Application Directory**
   ```bash
   cd /var/www/mepscore
   ls -la  # Verify files are uploaded
   ```

3. **Make Scripts Executable**
   ```bash
   sudo chmod +x deployment/deploy.sh
   sudo chmod +x deployment/upload_files.sh
   ```

4. **Run Deployment Script**
   ```bash
   sudo bash deployment/deploy.sh
   ```

   The script will:
   - Update the system
   - Install Python, Nginx, and other dependencies
   - Create virtual environment
   - Configure Nginx
   - Set up systemd service
   - Configure firewall

5. **Configure SSL Certificate**
   - When prompted for SSL certificate setup, type `y`
   - **Important**: Make sure your domain points to the server before this step
   - The script will automatically obtain and configure Let's Encrypt SSL certificate

## Part 4: Final Configuration

### Step 7: Verify Deployment

1. **Check Services Status**
   ```bash
   sudo systemctl status mepscore
   sudo systemctl status nginx
   ```

2. **Check Application Logs**
   ```bash
   sudo journalctl -u mepscore -f
   ```

3. **Test the Application**
   - Open web browser
   - Go to `https://mepscore.eu`
   - You should see your MEP ranking application

### Step 8: Update Application Configuration

1. **Update Production Server Configuration**
   Edit the systemd service to use production server:
   ```bash
   sudo nano /etc/systemd/system/mepscore.service
   ```
   
   Change the ExecStart line:
   ```
   ExecStart=/var/www/mepscore/venv/bin/python deployment/production_serve.py
   ```

2. **Reload and Restart Services**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl restart mepscore
   sudo systemctl restart nginx
   ```

## Part 5: Maintenance and Monitoring

### Updating Your Application

1. **Connect to Server**
   ```bash
   ssh -i "KEY_PATH" ubuntu@YOUR_STATIC_IP
   ```

2. **Update Files**
   - Upload new files using the upload script
   - Or use git if you have a repository set up

3. **Restart Services**
   ```bash
   sudo systemctl restart mepscore
   sudo systemctl restart nginx
   ```

### Monitoring and Logs

1. **Application Logs**
   ```bash
   sudo journalctl -u mepscore -f            # Follow real-time logs
   sudo tail -f /var/log/mepscore.log        # Application logs
   sudo tail -f /var/log/nginx/mepscore_access.log  # Access logs
   sudo tail -f /var/log/nginx/mepscore_error.log   # Error logs
   ```

2. **System Resources**
   ```bash
   htop          # CPU and memory usage
   df -h         # Disk usage
   free -h       # Memory usage
   ```

3. **SSL Certificate Renewal**
   - Certificates auto-renew via cron job
   - Test renewal: `sudo certbot renew --dry-run`

### Backup Strategy

1. **Database Backup**
   ```bash
   cp /var/www/mepscore/data/meps.db /var/www/mepscore/backups/meps_$(date +%Y%m%d).db
   ```

2. **Full Instance Snapshot**
   - Go to Lightsail console
   - Select your instance
   - Click "Snapshots" tab
   - Create manual snapshot
   - Set up automatic snapshots (recommended)

### Scaling Up

When you need more resources:

1. **Upgrade Instance**
   - In Lightsail console, go to your instance
   - Click "Manage" → "Change your plan"
   - Select larger instance size
   - **Note**: This requires a reboot

2. **Migrate to EC2**
   - For advanced scaling needs
   - Use Lightsail's "Upgrade to EC2" feature

## Troubleshooting

### Common Issues

1. **Domain Not Resolving**
   - Check DNS propagation: [whatsmydns.net](https://whatsmydns.net)
   - Verify A records point to your static IP
   - Wait up to 48 hours for full propagation

2. **SSL Certificate Issues**
   - Ensure domain resolves before running certbot
   - Check firewall allows ports 80 and 443
   - Manually run: `sudo certbot --nginx -d mepscore.eu -d www.mepscore.eu`

3. **Application Not Loading**
   - Check service status: `sudo systemctl status mepscore`
   - Check logs: `sudo journalctl -u mepscore -f`
   - Verify file permissions: `sudo chown -R www-data:www-data /var/www/mepscore`

4. **High Resource Usage**
   - Monitor with `htop`
   - Check for memory leaks in logs
   - Consider upgrading instance size

5. **Database Issues**
   - Check file exists: `ls -la /var/www/mepscore/data/meps.db`
   - Verify permissions: `sudo chown www-data:www-data /var/www/mepscore/data/meps.db`
   - Test database: `sqlite3 /var/www/mepscore/data/meps.db ".tables"`

### Getting Help

- **AWS Lightsail Documentation**: [docs.aws.amazon.com/lightsail](https://docs.aws.amazon.com/lightsail/)
- **Let's Encrypt Community**: [community.letsencrypt.org](https://community.letsencrypt.org/)
- **Ubuntu Community**: [askubuntu.com](https://askubuntu.com/)

## Security Best Practices

1. **SSH Security**
   - Disable password authentication
   - Use key-based authentication only
   - Restrict SSH access to your IP

2. **Firewall Configuration**
   - Only open necessary ports (22, 80, 443)
   - Consider using Fail2Ban for brute-force protection

3. **Regular Updates**
   - Enable automatic security updates
   - Regularly update application dependencies
   - Keep SSL certificates current

4. **Backup Strategy**
   - Daily automated snapshots
   - Store critical data backups off-site
   - Test backup restoration regularly

## Cost Management

- **Monitor Usage**: Check Lightsail console for data transfer and storage usage
- **Set Billing Alerts**: Configure AWS billing alerts to avoid surprises
- **Optimize Resources**: Start small and scale up as needed
- **Review Monthly**: Regularly review costs and usage patterns

Your MEP Score application should now be successfully deployed and accessible at https://mepscore.eu!