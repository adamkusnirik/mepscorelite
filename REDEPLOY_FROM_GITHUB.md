# Redeploy from GitHub (Keep Data Folder)

This will clean your current deployment and redeploy fresh from GitHub while preserving your data folder.

## Quick Instructions

1. **SSH to your AWS Lightsail server:**
   ```bash
   ssh -i "path/to/your/key.pem" ubuntu@YOUR_LIGHTSAIL_IP
   ```

2. **Download the redeploy script:**
   ```bash
   cd /var/www/mepscore
   wget https://raw.githubusercontent.com/adamkusnirik/mepscore/main/deployment/redeploy_from_github.sh
   chmod +x deployment/redeploy_from_github.sh
   ```

3. **Run the redeploy script:**
   ```bash
   sudo bash deployment/redeploy_from_github.sh
   ```

   The script will:
   - ✅ Stop all services
   - ✅ Backup your data folder
   - ✅ Clean everything except data
   - ✅ Clone fresh code from GitHub
   - ✅ Restore your data folder
   - ✅ Set up Python environment
   - ✅ Restart all services

## Development Workflow After Redeploy

Once redeployed, your workflow will be:

1. **Make changes locally** (on your computer)
2. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Your changes"
   git push origin main
   ```

3. **Update server:**
   ```bash
   # SSH to server
   ssh -i "key.pem" ubuntu@YOUR_IP
   
   # Pull updates
   cd /var/www/mepscore
   sudo git pull origin main
   
   # Restart service
   sudo systemctl restart mepscore
   ```

## Useful Commands After Redeploy

**View logs:**
```bash
sudo journalctl -u mepscore -f
```

**Check service status:**
```bash
sudo systemctl status mepscore
sudo systemctl status nginx
```

**Restart services:**
```bash
sudo systemctl restart mepscore
sudo systemctl restart nginx
```

**Check what branch you're on:**
```bash
cd /var/www/mepscore
git branch -vv
git status
```

This gives you a clean GitHub-based workflow where you can easily make changes and deploy them!