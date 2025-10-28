#!/bin/bash

# Improved MEP Score GitHub Redeploy Script
# Fixes: disk space issues, proper data preservation, cleanup of temp files
# Run this script on your AWS Lightsail server to clean and redeploy

set -e

# Configuration
APP_DIR="/var/www/mepscore"
TEMP_DATA_DIR="/tmp/mepscore_data_preserve_$(date +%s)"
GITHUB_URL="https://github.com/adamkusnirik/mepscore.git"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

cleanup_temp_files() {
    print_step "Cleaning up temporary files..."
    # Remove any old backup directories that might exist
    rm -rf /tmp/mepscore_data_backup* /tmp/mepscore_data_preserve* 2>/dev/null || true
    print_status "Temporary files cleaned up"
}

check_disk_space() {
    print_step "Checking available disk space..."
    available_space=$(df / | awk 'NR==2 {print $4}')
    required_space=4194304  # 4GB in KB
    
    if [ "$available_space" -lt "$required_space" ]; then
        print_error "Insufficient disk space. Available: $(($available_space/1024/1024))GB, Required: 4GB"
        print_status "Cleaning up old temporary files..."
        cleanup_temp_files
        
        # Check again after cleanup
        available_space=$(df / | awk 'NR==2 {print $4}')
        if [ "$available_space" -lt "$required_space" ]; then
            print_error "Still insufficient disk space after cleanup. Please free up space manually."
            exit 1
        fi
    fi
    print_status "Disk space check passed: $(($available_space/1024/1024))GB available"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root (use sudo)"
   exit 1
fi

echo "========================================"
echo "MEP Score GitHub Redeploy Script (Fixed)"
echo "========================================"

print_warning "This will DELETE all files except data folder and redeploy from GitHub"
echo "Are you sure you want to continue? (y/N)"
read -r response

if [[ ! "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    print_error "Deployment cancelled by user"
    exit 0
fi

# Pre-deployment checks
check_disk_space
cleanup_temp_files

# Step 1: Stop services
print_step "1. Stopping services..."
systemctl stop mepscore || true
systemctl stop nginx || true
print_status "Services stopped"

# Step 2: Preserve data folder with better path handling
print_step "2. Preserving data folder..."
if [ -d "$APP_DIR/data" ]; then
    # Use timestamped directory to avoid conflicts
    cp -r "$APP_DIR/data" "$TEMP_DATA_DIR"
    print_status "Data folder copied to $TEMP_DATA_DIR"
    
    # Verify the copy was successful
    if [ ! -d "$TEMP_DATA_DIR" ]; then
        print_error "Failed to preserve data folder"
        exit 1
    fi
    
    data_size=$(du -sh "$TEMP_DATA_DIR" | cut -f1)
    print_status "Preserved data size: $data_size"
else
    print_warning "No data folder found"
fi

# Step 3: Clean application directory
print_step "3. Cleaning application directory..."
if [ -d "$APP_DIR" ]; then
    rm -rf $APP_DIR/*
    rm -rf $APP_DIR/.[!.]* 2>/dev/null || true
    print_status "Application directory cleaned"
fi

# Step 4: Clone from GitHub
print_step "4. Cloning fresh code from GitHub..."
cd $APP_DIR
git clone $GITHUB_URL .
print_status "Code cloned from GitHub"

# Step 5: Restore data folder
print_step "5. Restoring data folder..."
if [ -d "$TEMP_DATA_DIR" ]; then
    # Remove any empty data directory created by git clone
    rm -rf "$APP_DIR/data"
    
    # Move preserved data back
    mv "$TEMP_DATA_DIR" "$APP_DIR/data"
    print_status "Data folder restored successfully"
    
    # Verify restoration
    if [ -f "$APP_DIR/data/meps.db" ]; then
        db_size=$(du -sh "$APP_DIR/data/meps.db" | cut -f1)
        print_status "Database restored: $db_size"
    fi
    
    # Check for essential parltrack files
    parltrack_files=$(find "$APP_DIR/data/parltrack" -name "*.json" -size +1M 2>/dev/null | wc -l)
    if [ "$parltrack_files" -gt 0 ]; then
        print_status "Found $parltrack_files parltrack data files"
    else
        print_warning "No large parltrack data files found - API may not work properly"
    fi
else
    print_warning "No preserved data found"
    mkdir -p $APP_DIR/data/parltrack
    print_status "Created empty data directories"
fi

# Step 6: Set permissions
print_step "6. Setting permissions..."
chown -R www-data:www-data $APP_DIR
chmod -R 755 $APP_DIR
chmod +x $APP_DIR/deployment/*.sh
print_status "Permissions set"

# Step 7: Install dependencies
print_step "7. Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    python3 -m pip install --upgrade pip
    python3 -m pip install -r requirements.txt
    print_status "Python dependencies installed"
fi

# Step 8: Final cleanup of any remaining temp files
print_step "8. Final cleanup..."
cleanup_temp_files

# Step 9: Start services
print_step "9. Starting services..."
systemctl start mepscore || true
systemctl start nginx || true
print_status "Services started"

# Step 10: Verify deployment
print_step "10. Verifying deployment..."
sleep 5

if systemctl is-active --quiet mepscore; then
    print_status "MEP Score service is running"
else
    print_warning "MEP Score service is not running"
fi

if systemctl is-active --quiet nginx; then
    print_status "Nginx service is running"
else
    print_warning "Nginx service is not running"
fi

# Test API endpoint
print_step "11. Testing API functionality..."
api_test=$(curl -s "http://localhost:8000/api/health" | grep -o '"success":true' || echo "failed")
if [ "$api_test" = '"success":true' ]; then
    print_status "API health check passed"
else
    print_warning "API health check failed - check logs"
fi

# Final disk space check
final_space=$(df / | awk 'NR==2 {print $4}')
print_status "Final disk space: $(($final_space/1024/1024))GB available"

echo "========================================"
echo "Redeployment completed successfully!"
echo "========================================"
print_status "Your MEP Score application has been redeployed from GitHub"
print_status "Data preservation and cleanup completed"
print_status "Check the logs if you encounter any issues:"
echo "  - MEP Score: sudo journalctl -u mepscore -f"
echo "  - Nginx: sudo journalctl -u nginx -f"
echo "  - API Test: curl http://localhost:8000/api/health"