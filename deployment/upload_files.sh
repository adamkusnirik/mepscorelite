#!/bin/bash

# File upload script for MEP Score deployment
# Run this from your local machine to upload files to Lightsail

set -e

# Configuration - REPLACE THESE VALUES
SERVER_IP="YOUR_LIGHTSAIL_IP"
KEY_PATH="path/to/your/LightsailDefaultKey-eu-west-1.pem"
SERVER_USER="ubuntu"  # or "bitnami" depending on your Lightsail instance

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
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

# Check if required variables are set
if [ "$SERVER_IP" = "YOUR_LIGHTSAIL_IP" ]; then
    print_error "Please update SERVER_IP in this script with your Lightsail instance IP"
    exit 1
fi

if [ ! -f "$KEY_PATH" ]; then
    print_error "SSH key not found at $KEY_PATH. Please update KEY_PATH in this script."
    exit 1
fi

print_status "Starting file upload to Lightsail instance..."

# Create application directory on server
print_status "Creating application directory on server..."
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" "sudo mkdir -p /var/www/mepscore && sudo chown $SERVER_USER:$SERVER_USER /var/www/mepscore"

# Upload application files (excluding data directory for now)
print_status "Uploading application files..."
rsync -avz --progress -e "ssh -i $KEY_PATH" \
    --exclude='data/' \
    --exclude='__pycache__/' \
    --exclude='*.pyc' \
    --exclude='.git/' \
    --exclude='node_modules/' \
    --exclude='.vscode/' \
    --exclude='.claude/' \
    ./ "$SERVER_USER@$SERVER_IP:/var/www/mepscore/"

# Create data directory structure
print_status "Creating data directory structure..."
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" "cd /var/www/mepscore && mkdir -p data/parltrack && mkdir -p public/data"

# Upload essential data files (compressed)
print_status "Uploading compressed data files..."
if [ -f "data/meps.db" ]; then
    scp -i "$KEY_PATH" "data/meps.db" "$SERVER_USER@$SERVER_IP:/var/www/mepscore/data/"
    print_status "Database uploaded successfully"
fi

if [ -f "public/data/term10_dataset.json" ]; then
    scp -i "$KEY_PATH" "public/data/"*.json "$SERVER_USER@$SERVER_IP:/var/www/mepscore/public/data/"
    print_status "Dataset files uploaded successfully"
fi

# Upload parltrack data files
print_status "Uploading parltrack data files..."
if [ -d "data/parltrack" ]; then
    rsync -avz --progress -e "ssh -i $KEY_PATH" \
        data/parltrack/ "$SERVER_USER@$SERVER_IP:/var/www/mepscore/data/parltrack/"
    print_status "Parltrack data uploaded successfully"
fi

# Set proper permissions
print_status "Setting proper file permissions..."
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" "sudo chown -R www-data:www-data /var/www/mepscore && sudo chmod -R 755 /var/www/mepscore"

print_status "File upload completed successfully!"
print_status "Next steps:"
echo "1. SSH to your server: ssh -i $KEY_PATH $SERVER_USER@$SERVER_IP"
echo "2. Run the deployment script: sudo bash /var/www/mepscore/deployment/deploy.sh"