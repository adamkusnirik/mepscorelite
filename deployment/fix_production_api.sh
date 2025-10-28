#!/bin/bash

# Quick fix for MEP Score API on production server
echo "========================================"
echo "MEP Score API Quick Fix"
echo "========================================"

cd /var/www/mepscore

# Install missing psutil dependency for production server
echo "1. Installing missing Python dependencies..."
pip3 install psutil --break-system-packages || pip3 install psutil

# Restart the service
echo "2. Restarting MEP Score service..."
sudo systemctl stop mepscore || true
sudo systemctl start mepscore

# Wait for service to start
echo "3. Waiting for service to start..."
sleep 5

# Check if service is running
echo "4. Checking service status..."
if systemctl is-active --quiet mepscore; then
    echo "✓ MEP Score service is running"
else
    echo "✗ Service failed to start. Checking logs..."
    sudo journalctl -u mepscore --no-pager -n 20
    
    echo ""
    echo "Trying to start serve.py directly for testing..."
    cd /var/www/mepscore
    python3 serve.py &
    SERVER_PID=$!
    sleep 3
    
    if kill -0 $SERVER_PID 2>/dev/null; then
        echo "✓ Direct server start successful"
        echo "Testing API..."
        curl -s http://localhost:8000/api/health || echo "API test failed"
        kill $SERVER_PID
    else
        echo "✗ Direct server start failed"
    fi
fi

# Test API endpoint
echo "5. Testing API..."
if curl -s http://localhost:8000/api/health > /dev/null; then
    echo "✓ API is responding"
    curl -s http://localhost:8000/api/health | head -5
else
    echo "✗ API is not responding"
    echo "Checking what's on port 8000..."
    netstat -tlnp | grep :8000 || echo "Nothing on port 8000"
fi

echo ""
echo "========================================"
echo "Next steps:"
echo "1. If API is working: Check nginx configuration"
echo "2. If API not working: Check logs with 'sudo journalctl -u mepscore -f'"
echo "3. Manual test: 'cd /var/www/mepscore && python3 serve.py'"
echo "========================================"