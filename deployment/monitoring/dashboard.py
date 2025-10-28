#!/usr/bin/env python3
"""
MEP Score Monitoring Dashboard
Simple web dashboard for monitoring system status and metrics
"""

from flask import Flask, jsonify, render_template_string
import sqlite3
import psutil
import requests
from datetime import datetime, timedelta
import json
import os

app = Flask(__name__)

MONITORING_DB = "/var/log/mepscore/monitoring.db"
ANALYSIS_DB = "/var/log/mepscore/log_analysis.db"

# HTML template for dashboard
DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MEP Score Monitoring Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { text-align: center; margin-bottom: 30px; }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .metric-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .metric-value { font-size: 2em; font-weight: bold; color: #333; }
        .metric-label { color: #666; font-size: 0.9em; margin-top: 5px; }
        .status-good { color: #28a745; }
        .status-warning { color: #ffc107; }
        .status-error { color: #dc3545; }
        .charts-container { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px; }
        .chart-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .chart-card canvas { max-height: 300px; }
        .alerts-section { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .alert-item { padding: 10px; margin: 5px 0; border-radius: 4px; }
        .alert-critical { background: #f8d7da; border: 1px solid #f5c6cb; }
        .alert-warning { background: #fff3cd; border: 1px solid #ffeaa7; }
        .alert-info { background: #d1ecf1; border: 1px solid #b8daff; }
        .refresh-btn { background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; }
        .refresh-btn:hover { background: #0056b3; }
        @media (max-width: 768px) {
            .charts-container { grid-template-columns: 1fr; }
            .metrics-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>MEP Score Monitoring Dashboard</h1>
            <button class="refresh-btn" onclick="refreshData()">Refresh Data</button>
            <p>Last updated: <span id="lastUpdate"></span></p>
        </div>
        
        <div class="metrics-grid" id="metricsGrid">
            <!-- Metrics will be populated by JavaScript -->
        </div>
        
        <div class="charts-container">
            <div class="chart-card">
                <h3>System Resources (Last 24h)</h3>
                <canvas id="systemChart"></canvas>
            </div>
            <div class="chart-card">
                <h3>Response Time & Requests (Last 24h)</h3>
                <canvas id="performanceChart"></canvas>
            </div>
        </div>
        
        <div class="alerts-section">
            <h3>Recent Alerts</h3>
            <div id="alertsList">
                <!-- Alerts will be populated by JavaScript -->
            </div>
        </div>
    </div>

    <script>
        let systemChart, performanceChart;
        
        function refreshData() {
            updateMetrics();
            updateCharts();
            updateAlerts();
            document.getElementById('lastUpdate').textContent = new Date().toLocaleString();
        }
        
        async function updateMetrics() {
            try {
                const response = await fetch('/api/metrics');
                const data = await response.json();
                
                const metricsGrid = document.getElementById('metricsGrid');
                metricsGrid.innerHTML = '';
                
                // Current system status
                const metrics = [
                    {
                        label: 'CPU Usage',
                        value: data.current_cpu + '%',
                        status: data.current_cpu > 80 ? 'error' : data.current_cpu > 60 ? 'warning' : 'good'
                    },
                    {
                        label: 'Memory Usage',
                        value: data.current_memory + '%',
                        status: data.current_memory > 85 ? 'error' : data.current_memory > 70 ? 'warning' : 'good'
                    },
                    {
                        label: 'Disk Usage',
                        value: data.current_disk + '%',
                        status: data.current_disk > 90 ? 'error' : data.current_disk > 75 ? 'warning' : 'good'
                    },
                    {
                        label: 'API Status',
                        value: data.api_status ? 'Online' : 'Offline',
                        status: data.api_status ? 'good' : 'error'
                    },
                    {
                        label: 'Response Time',
                        value: Math.round(data.avg_response_time) + 'ms',
                        status: data.avg_response_time > 2000 ? 'error' : data.avg_response_time > 1000 ? 'warning' : 'good'
                    },
                    {
                        label: 'Requests/Hour',
                        value: data.requests_per_hour.toLocaleString(),
                        status: 'good'
                    }
                ];
                
                metrics.forEach(metric => {
                    const card = document.createElement('div');
                    card.className = 'metric-card';
                    card.innerHTML = `
                        <div class="metric-value status-${metric.status}">${metric.value}</div>
                        <div class="metric-label">${metric.label}</div>
                    `;
                    metricsGrid.appendChild(card);
                });
            } catch (error) {
                console.error('Error updating metrics:', error);
            }
        }
        
        async function updateCharts() {
            try {
                const response = await fetch('/api/charts');
                const data = await response.json();
                
                // System resources chart
                if (systemChart) systemChart.destroy();
                const systemCtx = document.getElementById('systemChart').getContext('2d');
                systemChart = new Chart(systemCtx, {
                    type: 'line',
                    data: {
                        labels: data.timestamps,
                        datasets: [{
                            label: 'CPU %',
                            data: data.cpu_data,
                            borderColor: 'rgb(255, 99, 132)',
                            tension: 0.1
                        }, {
                            label: 'Memory %',
                            data: data.memory_data,
                            borderColor: 'rgb(54, 162, 235)',
                            tension: 0.1
                        }, {
                            label: 'Disk %',
                            data: data.disk_data,
                            borderColor: 'rgb(255, 205, 86)',
                            tension: 0.1
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            y: { beginAtZero: true, max: 100 }
                        }
                    }
                });
                
                // Performance chart
                if (performanceChart) performanceChart.destroy();
                const perfCtx = document.getElementById('performanceChart').getContext('2d');
                performanceChart = new Chart(perfCtx, {
                    type: 'line',
                    data: {
                        labels: data.timestamps,
                        datasets: [{
                            label: 'Response Time (ms)',
                            data: data.response_time_data,
                            borderColor: 'rgb(75, 192, 192)',
                            tension: 0.1,
                            yAxisID: 'y'
                        }, {
                            label: 'Requests/Hour',
                            data: data.requests_data,
                            borderColor: 'rgb(153, 102, 255)',
                            tension: 0.1,
                            yAxisID: 'y1'
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            y: { type: 'linear', display: true, position: 'left' },
                            y1: { type: 'linear', display: true, position: 'right' }
                        }
                    }
                });
            } catch (error) {
                console.error('Error updating charts:', error);
            }
        }
        
        async function updateAlerts() {
            try {
                const response = await fetch('/api/alerts');
                const data = await response.json();
                
                const alertsList = document.getElementById('alertsList');
                alertsList.innerHTML = '';
                
                if (data.length === 0) {
                    alertsList.innerHTML = '<p>No recent alerts</p>';
                    return;
                }
                
                data.forEach(alert => {
                    const alertDiv = document.createElement('div');
                    alertDiv.className = `alert-item alert-${alert.severity}`;
                    alertDiv.innerHTML = `
                        <strong>${alert.alert_type}</strong> - ${alert.message}
                        <br><small>${new Date(alert.timestamp).toLocaleString()}</small>
                    `;
                    alertsList.appendChild(alertDiv);
                });
            } catch (error) {
                console.error('Error updating alerts:', error);
            }
        }
        
        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', function() {
            refreshData();
            // Auto-refresh every 60 seconds
            setInterval(refreshData, 60000);
        });
    </script>
</body>
</html>
'''

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template_string(DASHBOARD_TEMPLATE)

@app.route('/api/metrics')
def api_metrics():
    """API endpoint for current metrics"""
    try:
        # Get current system metrics
        current_cpu = psutil.cpu_percent(interval=1)
        current_memory = psutil.virtual_memory().percent
        current_disk = psutil.disk_usage('/').percent
        
        # Check API status
        api_status = False
        avg_response_time = 0
        try:
            response = requests.get('http://localhost:8000/api/health', timeout=5)
            if response.status_code == 200:
                api_status = True
                # You can extract response time from the response if needed
        except:
            pass
        
        # Get recent metrics from database
        conn = sqlite3.connect(MONITORING_DB)
        cursor = conn.cursor()
        
        # Get average response time and request rate from last hour
        one_hour_ago = datetime.now() - timedelta(hours=1)
        cursor.execute('''
            SELECT AVG(response_time_ms), COUNT(*) * 60 as requests_per_hour
            FROM metrics 
            WHERE timestamp > ? AND response_time_ms > 0
        ''', (one_hour_ago,))
        
        row = cursor.fetchone()
        if row:
            avg_response_time = row[0] or 0
            requests_per_hour = row[1] or 0
        else:
            requests_per_hour = 0
        
        conn.close()
        
        return jsonify({
            'current_cpu': round(current_cpu, 1),
            'current_memory': round(current_memory, 1),
            'current_disk': round(current_disk, 1),
            'api_status': api_status,
            'avg_response_time': avg_response_time,
            'requests_per_hour': requests_per_hour
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/charts')
def api_charts():
    """API endpoint for chart data"""
    try:
        conn = sqlite3.connect(MONITORING_DB)
        cursor = conn.cursor()
        
        # Get last 24 hours of data, grouped by hour
        twenty_four_hours_ago = datetime.now() - timedelta(hours=24)
        cursor.execute('''
            SELECT 
                strftime('%H:00', timestamp) as hour,
                AVG(cpu_percent) as avg_cpu,
                AVG(memory_percent) as avg_memory,
                AVG(disk_percent) as avg_disk,
                AVG(response_time_ms) as avg_response_time,
                COUNT(*) as request_count
            FROM metrics 
            WHERE timestamp > ?
            GROUP BY strftime('%Y-%m-%d %H', timestamp)
            ORDER BY timestamp
        ''', (twenty_four_hours_ago,))
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            # Return empty data if no metrics available
            return jsonify({
                'timestamps': [],
                'cpu_data': [],
                'memory_data': [],
                'disk_data': [],
                'response_time_data': [],
                'requests_data': []
            })
        
        timestamps = [row[0] for row in rows]
        cpu_data = [round(row[1] or 0, 1) for row in rows]
        memory_data = [round(row[2] or 0, 1) for row in rows]
        disk_data = [round(row[3] or 0, 1) for row in rows]
        response_time_data = [round(row[4] or 0, 1) for row in rows]
        requests_data = [row[5] or 0 for row in rows]
        
        return jsonify({
            'timestamps': timestamps,
            'cpu_data': cpu_data,
            'memory_data': memory_data,
            'disk_data': disk_data,
            'response_time_data': response_time_data,
            'requests_data': requests_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/alerts')
def api_alerts():
    """API endpoint for recent alerts"""
    try:
        conn = sqlite3.connect(MONITORING_DB)
        cursor = conn.cursor()
        
        # Get alerts from last 24 hours
        twenty_four_hours_ago = datetime.now() - timedelta(hours=24)
        cursor.execute('''
            SELECT alert_type, severity, message, timestamp
            FROM alerts 
            WHERE timestamp > ?
            ORDER BY timestamp DESC
            LIMIT 20
        ''', (twenty_four_hours_ago,))
        
        rows = cursor.fetchall()
        conn.close()
        
        alerts = []
        for row in rows:
            alerts.append({
                'alert_type': row[0],
                'severity': row[1],
                'message': row[2],
                'timestamp': row[3]
            })
        
        return jsonify(alerts)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    # Create log directory if it doesn't exist
    os.makedirs('/var/log/mepscore', exist_ok=True)
    
    # Run in development mode - in production, use proper WSGI server
    app.run(host='127.0.0.1', port=9000, debug=False)