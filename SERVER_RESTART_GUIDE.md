# Server Restart Guide

Quick guide for restarting the MEPScore server when it's down.

## **Quick Server Restart Guide**

### **1. Connect to Server**
```bash
ssh -i "C:\Users\adamk\Downloads\LightsailDefaultKey-eu-west-1(3).pem" ubuntu@108.128.29.141
```

### **2. Go to App Directory**
```bash
cd /var/www/mepscore
```

### **3. Check Current Status**
```bash
ps aux | grep serve.py
```
*(Shows if the server is running)*

### **4. Kill Any Running Processes**
```bash
pkill -f serve.py
```

### **5. Start Server**
```bash
nohup python3 serve.py > server.log 2>&1 &
```

### **6. Verify It's Running**
```bash
ps aux | grep serve.py
```
*(Should show the running process)*

### **7. Test the Website**
Visit: `https://mepscore.eu` in your browser

---

## **Alternative One-Command Restart**
```bash
ssh -i "C:\Users\adamk\Downloads\LightsailDefaultKey-eu-west-1(3).pem" ubuntu@108.128.29.141 "cd /var/www/mepscore && pkill -f serve.py && nohup python3 serve.py > server.log 2>&1 &"
```

## **If You Get Permission Errors**
```bash
sudo chown -R ubuntu:ubuntu /var/www/mepscore
```

## **Server Details**
- **Server IP**: 108.128.29.141
- **App Location**: `/var/www/mepscore`
- **Log File**: `server.log`
- **Port**: 80 (HTTPS via reverse proxy)
- **Website**: https://mepscore.eu

## **Troubleshooting**

### **Check Server Logs**
```bash
tail -f /var/www/mepscore/server.log
```

### **Check System Resources**
```bash
df -h          # Disk space
free -h        # Memory usage
top            # CPU usage
```

### **If Still Not Working**
1. Check if port 80 is available: `sudo netstat -tlnp | grep :80`
2. Restart the entire server: `sudo reboot`
3. Wait 2-3 minutes and try connecting again

**Note**: The server runs on port 80, so it should be accessible immediately at `https://mepscore.eu` after starting.