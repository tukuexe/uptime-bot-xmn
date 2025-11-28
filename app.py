from flask import Flask, render_template_string, request, jsonify
import requests
import time
import threading
import schedule
from datetime import datetime
import os
import json

app = Flask(__name__)

# Retro-style HTML with responsive design
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🚀 Retro Uptime Guardian</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Courier New', monospace;
            background: linear-gradient(45deg, #0f0f0f, #1a1a2e);
            color: #00ff00;
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            border: 3px solid #00ff00;
            border-radius: 15px;
            padding: 20px;
            background: rgba(0, 0, 0, 0.8);
            box-shadow: 0 0 30px #00ff00;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            border-bottom: 2px dashed #00ff00;
        }
        .glitch {
            font-size: 3em;
            font-weight: bold;
            text-transform: uppercase;
            position: relative;
            text-shadow: 0.05em 0 0 #ff00ff, -0.05em -0.025em 0 #00ffff;
            animation: glitch 2s infinite;
        }
        @keyframes glitch {
            0% { text-shadow: 0.05em 0 0 #ff00ff, -0.05em -0.025em 0 #00ffff; }
            14% { text-shadow: 0.05em 0 0 #ff00ff, -0.05em -0.025em 0 #00ffff; }
            15% { text-shadow: -0.05em -0.025em 0 #ff00ff, 0.025em 0.025em 0 #00ffff; }
            49% { text-shadow: -0.05em -0.025em 0 #ff00ff, 0.025em 0.025em 0 #00ffff; }
            50% { text-shadow: 0.025em 0.05em 0 #ff00ff, 0.05em 0 0 #00ffff; }
            99% { text-shadow: 0.025em 0.05em 0 #ff00ff, 0.05em 0 0 #00ffff; }
            100% { text-shadow: -0.025em 0 0 #ff00ff, -0.025em -0.025em 0 #00ffff; }
        }
        .controls {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background: rgba(0, 255, 0, 0.1);
            border: 1px solid #00ff00;
            border-radius: 10px;
            padding: 20px;
            transition: all 0.3s;
        }
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 5px 15px rgba(0, 255, 0, 0.3);
        }
        input, button {
            width: 100%;
            padding: 12px;
            margin: 8px 0;
            background: black;
            border: 1px solid #00ff00;
            color: #00ff00;
            border-radius: 5px;
            font-family: 'Courier New', monospace;
        }
        button {
            background: #00ff00;
            color: black;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
        }
        button:hover {
            background: #ff00ff;
            color: white;
        }
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        .status-item {
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            font-weight: bold;
        }
        .up { background: rgba(0, 255, 0, 0.2); border: 1px solid #00ff00; }
        .down { background: rgba(255, 0, 0, 0.2); border: 1px solid #ff0000; animation: pulse 2s infinite; }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        .log {
            background: black;
            border: 1px solid #00ff00;
            border-radius: 5px;
            padding: 15px;
            height: 200px;
            overflow-y: auto;
            margin-top: 20px;
            font-size: 0.9em;
        }
        .log-entry { margin: 5px 0; padding: 5px; border-left: 3px solid #00ff00; }
        .timestamp { color: #ff00ff; }
        @media (max-width: 768px) {
            .glitch { font-size: 2em; }
            .controls { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="glitch">🚀 RETRO UPTIME GUARDIAN</div>
            <p>Keeping your Render apps alive 24/7 with retro style! ⚡</p>
        </div>

        <div class="controls">
            <div class="card">
                <h3>🎯 Add Website</h3>
                <input type="text" id="siteUrl" placeholder="https://your-app.onrender.com" value="https://your-app.onrender.com">
                <input type="text" id="siteName" placeholder="My Awesome App" value="My Awesome App">
                <button onclick="addWebsite()">➕ ADD WEBSITE</button>
            </div>

            <div class="card">
                <h3>⚙️ Quick Actions</h3>
                <button onclick="startMonitoring()">🚀 START MONITORING</button>
                <button onclick="stopMonitoring()">🛑 STOP MONITORING</button>
                <button onclick="checkAllNow()">🔍 CHECK ALL NOW</button>
            </div>

            <div class="card">
                <h3>📊 Stats</h3>
                <div id="stats">
                    <p>📈 Total Websites: <span id="totalSites">0</span></p>
                    <p>✅ Up: <span id="upCount">0</span></p>
                    <p>❌ Down: <span id="downCount">0</span></p>
                    <p>⏰ Last Check: <span id="lastCheck">Never</span></p>
                </div>
            </div>
        </div>

        <div class="card">
            <h3>🌐 Website Status</h3>
            <div id="statusGrid" class="status-grid">
                <!-- Status items will appear here -->
            </div>
        </div>

        <div class="card">
            <h3>📜 Activity Log</h3>
            <div id="log" class="log">
                <div class="log-entry"><span class="timestamp">[{{ current_time }}]</span> System initialized. Ready to monitor!</div>
            </div>
        </div>
    </div>

    <script>
        let monitoring = false;
        let checkInterval;

        function addWebsite() {
            const url = document.getElementById('siteUrl').value;
            const name = document.getElementById('siteName').value;
            
            fetch('/add_website', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({url: url, name: name})
            })
            .then(response => response.json())
            .then(data => {
                addLog(`✅ Added: ${name}`);
                updateStatus();
            });
        }

        function startMonitoring() {
            monitoring = true;
            fetch('/start_monitoring')
            .then(response => response.json())
            .then(data => {
                addLog('🚀 Monitoring started!');
                checkInterval = setInterval(updateStatus, 5000);
            });
        }

        function stopMonitoring() {
            monitoring = false;
            fetch('/stop_monitoring')
            .then(response => response.json())
            .then(data => {
                addLog('🛑 Monitoring stopped!');
                clearInterval(checkInterval);
            });
        }

        function checkAllNow() {
            fetch('/check_all')
            .then(response => response.json())
            .then(data => {
                addLog('🔍 Manual check initiated!');
                updateStatus();
            });
        }

        function updateStatus() {
            fetch('/status')
            .then(response => response.json())
            .then(data => {
                document.getElementById('totalSites').textContent = data.total_sites;
                document.getElementById('upCount').textContent = data.up_count;
                document.getElementById('downCount').textContent = data.down_count;
                document.getElementById('lastCheck').textContent = data.last_check;
                
                const statusGrid = document.getElementById('statusGrid');
                statusGrid.innerHTML = '';
                
                data.websites.forEach(site => {
                    const statusClass = site.status === 'up' ? 'up' : 'down';
                    const statusEmoji = site.status === 'up' ? '✅' : '❌';
                    statusGrid.innerHTML += `
                        <div class="status-item ${statusClass}">
                            ${statusEmoji} ${site.name}<br>
                            <small>${site.response_time}ms</small>
                        </div>
                    `;
                });
            });
        }

        function addLog(message) {
            const log = document.getElementById('log');
            const timestamp = new Date().toLocaleTimeString();
            log.innerHTML += `<div class="log-entry"><span class="timestamp">[${timestamp}]</span> ${message}</div>`;
            log.scrollTop = log.scrollHeight;
        }

        // Initial load
        updateStatus();
    </script>
</body>
</html>
'''

# Global variables
websites = []
monitoring_active = False
last_check_time = "Never"

class WebsiteMonitor:
    def __init__(self):
        self.websites = []
        self.load_websites()
    
    def load_websites(self):
        global websites
        try:
            # Try to load from environment variable (for Render persistence)
            sites_json = os.environ.get('MONITOR_WEBSITES', '[]')
            self.websites = json.loads(sites_json)
            websites = self.websites
        except:
            self.websites = []
            websites = []
    
    def save_websites(self):
        global websites
        try:
            # Save to environment (in production) and update global
            os.environ['MONITOR_WEBSITES'] = json.dumps(self.websites)
            websites = self.websites
        except:
            pass
    
    def add_website(self, url, name):
        website = {
            'url': url,
            'name': name,
            'status': 'unknown',
            'response_time': 0,
            'last_checked': 'Never'
        }
        self.websites.append(website)
        self.save_websites()
        return f"✅ Added {name}"
    
    def check_website(self, website):
        try:
            start_time = time.time()
            response = requests.get(website['url'], timeout=30, headers={
                'User-Agent': 'RetroUptimeGuardian/1.0'
            })
            response_time = round((time.time() - start_time) * 1000, 2)
            
            website['status'] = 'up' if response.status_code == 200 else 'down'
            website['response_time'] = response_time
            website['last_checked'] = datetime.now().strftime('%H:%M:%S')
            
            return True
        except Exception as e:
            website['status'] = 'down'
            website['response_time'] = 0
            website['last_checked'] = datetime.now().strftime('%H:%M:%S')
            return False
    
    def check_all_websites(self):
        global last_check_time
        if not self.websites:
            return
        
        last_check_time = datetime.now().strftime('%H:%M:%S')
        
        # Check all websites in parallel using threads
        threads = []
        for website in self.websites:
            thread = threading.Thread(target=self.check_website, args=(website,))
            thread.start()
            threads.append(thread)
        
        for thread in threads:
            thread.join()
        
        self.save_websites()

# Global monitor instance
monitor = WebsiteMonitor()

def monitoring_job():
    """Background job that runs every 5-10 minutes"""
    if monitoring_active and monitor.websites:
        print(f"[{datetime.now()}] 🔍 Checking {len(monitor.websites)} websites...")
        monitor.check_all_websites()
        
        # Log results
        up_count = sum(1 for site in monitor.websites if site['status'] == 'up')
        print(f"[{datetime.now()}] 📊 Status: {up_count}/{len(monitor.websites)} up")

def start_monitoring_thread():
    """Start the background monitoring thread"""
    def run_scheduler():
        while monitoring_active:
            monitoring_job()
            # Random interval between 5-10 minutes
            time.sleep(300)  # 5 minutes
    
    if monitoring_active:
        thread = threading.Thread(target=run_scheduler, daemon=True)
        thread.start()

# Flask Routes
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, current_time=datetime.now().strftime('%H:%M:%S'))

@app.route('/add_website', methods=['POST'])
def add_website():
    data = request.get_json()
    result = monitor.add_website(data['url'], data['name'])
    return jsonify({'message': result, 'total_sites': len(monitor.websites)})

@app.route('/start_monitoring', methods=['POST'])
def start_monitoring():
    global monitoring_active
    monitoring_active = True
    start_monitoring_thread()
    return jsonify({'message': '🚀 Monitoring started!'})

@app.route('/stop_monitoring', methods=['POST'])
def stop_monitoring():
    global monitoring_active
    monitoring_active = False
    return jsonify({'message': '🛑 Monitoring stopped!'})

@app.route('/check_all', methods=['POST'])
def check_all():
    monitor.check_all_websites()
    return jsonify({'message': '🔍 Manual check completed!'})

@app.route('/status')
def status():
    up_count = sum(1 for site in monitor.websites if site['status'] == 'up')
    down_count = len(monitor.websites) - up_count
    
    return jsonify({
        'total_sites': len(monitor.websites),
        'up_count': up_count,
        'down_count': down_count,
        'last_check': last_check_time,
        'websites': monitor.websites
    })

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

# Initialize with some default websites if empty
if __name__ == '__main__':
    if not monitor.websites:
        monitor.add_website('https://httpstat.us/200', 'Example Website')
        monitor.add_website('https://google.com', 'Google')
        print("✅ Added default websites")
    
    # Start monitoring automatically
    monitoring_active = True
    start_monitoring_thread()
    
    print("🚀 Retro Uptime Guardian Started!")
    print("🌐 Web Interface: http://localhost:5000")
    print("📊 Monitoring:", len(monitor.websites), "websites")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
