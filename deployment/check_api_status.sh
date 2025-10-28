#!/bin/bash

# API Status Checker for MEP Score Production Server
# Run this script on your server to diagnose API issues

echo "========================================"
echo "MEP Score API Status Checker"
echo "========================================"

# Check if systemd service is running
echo "1. Checking systemd service status..."
if systemctl is-active --quiet mepscore; then
    echo "✓ MEP Score service is RUNNING"
    systemctl status mepscore --no-pager
else
    echo "✗ MEP Score service is NOT RUNNING"
    echo "Last service logs:"
    journalctl -u mepscore --no-pager -n 10
fi

echo ""
echo "2. Checking port 8000..."
if netstat -tlnp | grep :8000 > /dev/null; then
    echo "✓ Port 8000 is being used:"
    netstat -tlnp | grep :8000
else
    echo "✗ Nothing is listening on port 8000"
fi

echo ""
echo "3. Testing API health endpoint..."
if curl -s http://localhost:8000/api/health > /dev/null; then
    echo "✓ API health endpoint is responding:"
    curl -s http://localhost:8000/api/health | jq . 2>/dev/null || curl -s http://localhost:8000/api/health
else
    echo "✗ API health endpoint is not responding"
    echo "Testing basic HTTP connection..."
    curl -I http://localhost:8000/ 2>&1 || echo "No response from server"
fi

echo ""
echo "4. Checking required files..."
cd /var/www/mepscore

files_to_check=(
    "serve.py"
    "deployment/production_serve.py"
    "data/meps.db"
    "data/parltrack/ep_mep_activities.json"
    "data/parltrack/ep_amendments.json"
    "public/index.html"
    "public/profile.html"
)

for file in "${files_to_check[@]}"; do
    if [ -f "$file" ]; then
        echo "✓ $file exists"
    else
        echo "✗ $file is missing"
    fi
done

echo ""
echo "5. Checking log files..."
if [ -d "/var/log/mepscore" ]; then
    echo "✓ Log directory exists"
    if [ -f "/var/log/mepscore/application.log" ]; then
        echo "Recent application logs:"
        tail -5 /var/log/mepscore/application.log
    else
        echo "✗ No application.log found"
    fi
else
    echo "✗ Log directory /var/log/mepscore does not exist"
fi

echo ""
echo "6. Testing specific MEP API endpoint..."
test_url="http://localhost:8000/api/mep/257011/category/speeches?term=10&limit=5"
echo "Testing: $test_url"
if curl -s "$test_url" > /dev/null; then
    echo "✓ MEP API endpoint is responding"
    echo "Sample response:"
    curl -s "$test_url" | jq '.success, .total_count, .data_source' 2>/dev/null || curl -s "$test_url" | head -3
else
    echo "✗ MEP API endpoint is not responding"
fi

echo ""
echo "========================================"
echo "Diagnosis Summary:"
echo "========================================"

# Simple diagnosis
if systemctl is-active --quiet mepscore && netstat -tlnp | grep :8000 > /dev/null && curl -s http://localhost:8000/api/health > /dev/null; then
    echo "✓ API server appears to be working correctly"
    echo "If profile pages still show 'Detailed Data Not Available', the issue may be:"
    echo "  - Nginx configuration not proxying API requests"
    echo "  - Frontend trying to connect to wrong port/URL"
    echo "  - CORS or firewall blocking API requests"
else
    echo "✗ API server has issues that need to be resolved"
    echo "Recommended actions:"
    echo "  1. sudo systemctl restart mepscore"
    echo "  2. sudo systemctl enable mepscore"
    echo "  3. Check logs: sudo journalctl -u mepscore -f"
fi

echo ""
echo "To restart the service:"
echo "  sudo systemctl restart mepscore"
echo "  sudo systemctl status mepscore"
echo ""
echo "To view real-time logs:"
echo "  sudo journalctl -u mepscore -f"