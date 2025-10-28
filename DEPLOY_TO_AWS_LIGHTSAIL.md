# Quick AWS Lightsail Deployment Guide

## Prerequisites

1. **AWS Account** - Sign up at [aws.amazon.com](https://aws.amazon.com)
2. **Domain** - Register or transfer your domain (optional, but recommended)
3. **GitHub Repository** - Your code is already at: https://github.com/adamkusnirik/mepscore.git

## Step 1: Create AWS Lightsail Instance

1. **Login to AWS Console**
   - Go to AWS Console → Search "Lightsail" → Click "Create instance"

2. **Configure Instance**
   - **Region**: Europe (Ireland) - eu-west-1
   - **Platform**: Linux/Unix 
   - **Blueprint**: Ubuntu 20.04 LTS
   - **Instance plan**: $10/month (2GB RAM, 1vCPU) - recommended for start
   - **Instance name**: `mepscore-server`

3. **Create Static IP**
   - Go to Networking → Create static IP
   - Attach to your instance
   - **Save this IP address** - you'll need it

## Step 2: Upload Application Files

1. **Download SSH Key**
   - In Lightsail console → Your instance → Connect tab
   - Download default key pair (save as `LightsailDefaultKey-eu-west-1.pem`)

2. **Update Upload Script**
   - Edit `deployment/upload_files.sh`
   - Replace `YOUR_LIGHTSAIL_IP` with your static IP
   - Replace key path with your downloaded key location

3. **Run Upload Script**
   ```bash
   # Make executable and run
   chmod +x deployment/upload_files.sh
   ./deployment/upload_files.sh
   ```

## Step 3: Deploy Application

1. **SSH to Server**
   ```bash
   ssh -i "path/to/your/key.pem" ubuntu@YOUR_LIGHTSAIL_IP
   ```

2. **Clone Repository (Alternative to upload script)**
   ```bash
   sudo mkdir -p /var/www/mepscore
   cd /var/www/mepscore
   sudo git clone https://github.com/adamkusnirik/mepscore.git .
   ```

3. **Upload Your Data Files**
   Since data files are excluded from GitHub, you need to upload them:
   ```bash
   # From your local machine, upload data files
   scp -i "path/to/key.pem" -r data/ ubuntu@YOUR_IP:/tmp/
   ssh -i "path/to/key.pem" ubuntu@YOUR_IP "sudo cp -r /tmp/data/* /var/www/mepscore/data/"
   ```

4. **Run Deployment Script**
   ```bash
   cd /var/www/mepscore
   sudo chmod +x deployment/deploy.sh
   sudo bash deployment/deploy.sh
   ```

## Step 4: Configure Domain (Optional)

If you have a domain, configure it to point to your Lightsail IP:

1. **DNS Records**
   - A record: `@` → Your Lightsail IP
   - A record: `www` → Your Lightsail IP

2. **SSL Certificate** (after DNS propagation)
   ```bash
   sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
   ```

## Step 5: Verify Deployment

1. **Check Services**
   ```bash
   sudo systemctl status mepscore
   sudo systemctl status nginx
   ```

2. **Test Application**
   - Open browser: `http://YOUR_IP:8000` or `https://yourdomain.com`
   - You should see your MEP ranking application

## Maintenance Commands

**View Logs:**
```bash
sudo journalctl -u mepscore -f
sudo tail -f /var/log/mepscore.log
```

**Restart Services:**
```bash
sudo systemctl restart mepscore
sudo systemctl restart nginx
```

**Update Application:**
```bash
cd /var/www/mepscore
sudo git pull
sudo systemctl restart mepscore
```

## Troubleshooting

**Application won't start:**
- Check data files exist: `ls -la /var/www/mepscore/data/`
- Check permissions: `sudo chown -R www-data:www-data /var/www/mepscore`

**Domain not loading:**
- Verify DNS: Use [whatsmydns.net](https://whatsmydns.net)
- Check firewall: `sudo ufw status`

**SSL issues:**
- Ensure domain resolves before running certbot
- Check nginx config: `sudo nginx -t`

---

Your MEP Score application will be deployed and accessible on AWS Lightsail!

**Costs**: ~$10-20/month depending on instance size
**Performance**: Can handle moderate traffic loads
**Scaling**: Easy to upgrade instance size as needed