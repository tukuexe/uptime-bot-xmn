from flask import Flask, request, jsonify
import requests
import time
import threading
import schedule
from pymongo import MongoClient
from datetime import datetime
import os
import json
import subprocess
import logging

app = Flask(__name__)

# MongoDB Configuration
MONGO_URI = "mongodb+srv://schoolchat_user:tukubhuyan123@cluster0.i386mxq.mongodb.net/schoolchat?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI)
db = client.uptime_monitor

# Telegram Bot Configuration
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', 'YOUR_TELEGRAM_BOT_TOKEN')
TELEGRAM_WEBHOOK_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

class MultiLangUptimeMonitor:
    def __init__(self):
        self.websites = self.load_websites_from_db()
        self.monitoring_active = True
        self.setup_telegram_webhook()
    
    def load_websites_from_db(self):
        """Load websites from MongoDB"""
        try:
            sites = list(db.websites.find({}))
            print(f"📥 Loaded {len(sites)} websites from MongoDB")
            return sites
        except Exception as e:
            print(f"❌ MongoDB Error: {e}")
            return []
    
    def save_website_to_db(self, url, name, language="python"):
        """Save website to MongoDB"""
        try:
            website = {
                "url": url,
                "name": name,
                "language": language,
                "status": "unknown",
                "last_checked": datetime.now(),
                "created_at": datetime.now()
            }
            db.websites.update_one(
                {"url": url},
                {"$set": website},
                upsert=True
            )
            self.websites = self.load_websites_from_db()
            return True
        except Exception as e:
            print(f"❌ Save Error: {e}")
            return False
    
    def remove_website_from_db(self, url):
        """Remove website from MongoDB"""
        try:
            db.websites.delete_one({"url": url})
            self.websites = self.load_websites_from_db()
            return True
        except Exception as e:
            print(f"❌ Remove Error: {e}")
            return False
    
    def setup_telegram_webhook(self):
        """Setup Telegram webhook"""
        if TELEGRAM_TOKEN != 'YOUR_TELEGRAM_BOT_TOKEN':
            webhook_url = f"https://{request.host}/telegram"
            requests.post(
                f"{TELEGRAM_WEBHOOK_URL}/setWebhook",
                data={"url": webhook_url}
            )
            print(f"✅ Telegram webhook set: {webhook_url}")
    
    def check_with_python(self, website):
        """Python-based monitoring"""
        try:
            start = time.time()
            response = requests.get(website['url'], timeout=30)
            response_time = round((time.time() - start) * 1000, 2)
            
            status = 'up' if response.status_code == 200 else 'down'
            self.log_check(website, status, response_time, response.status_code)
            return status == 'up'
        except Exception as e:
            self.log_check(website, 'down', 0, 0, str(e))
            return False
    
    def check_with_nodejs(self, website):
        """Node.js-based monitoring"""
        try:
            result = subprocess.run([
                'node', '-e', f'''
                const https = require("https");
                const http = require("http");
                const start = Date.now();
                const url = "{website["url"]}";
                const protocol = url.startsWith("https") ? https : http;
                
                const req = protocol.get(url, (res) => {{
                    const time = Date.now() - start;
                    console.log(`${{res.statusCode}}|${{time}}`);
                    process.exit(res.statusCode === 200 ? 0 : 1);
                }});
                
                req.setTimeout(30000, () => {{
                    console.log("timeout|0");
                    process.exit(1);
                }});
                
                req.on("error", (e) => {{
                    console.log(`error|0|${{e.message}}`);
                    process.exit(1);
                }});
                '''
            ], capture_output=True, text=True, timeout=35)
            
            if result.returncode == 0:
                status_code, response_time = result.stdout.strip().split('|')
                self.log_check(website, 'up', int(response_time), int(status_code))
                return True
            return False
        except Exception as e:
            self.log_check(website, 'down', 0, 0, str(e))
            return False
    
    def check_with_ruby(self, website):
        """Ruby-based monitoring"""
        try:
            result = subprocess.run([
                'ruby', '-e', f'''
                require "net/http"
                require "uri"
                require "timeout"
                
                begin
                  start = Time.now
                  uri = URI("{website["url"]}")
                  response = Net::HTTP.get_response(uri)
                  time = ((Time.now - start) * 1000).to_i
                  
                  if response.is_a?(Net::HTTPSuccess)
                    puts "${{response.code}}|${{time}}"
                    exit 0
                  else
                    puts "${{response.code}}|${{time}}"
                    exit 1
                  end
                rescue => e
                  puts "error|0|${{e.message}}"
                  exit 1
                end
                '''
            ], capture_output=True, text=True, timeout=35)
            
            if result.returncode == 0:
                status_code, response_time = result.stdout.strip().split('|')
                self.log_check(website, 'up', int(response_time), int(status_code))
                return True
            return False
        except Exception as e:
            self.log_check(website, 'down', 0, 0, str(e))
            return False
    
    def check_with_php(self, website):
        """PHP-based monitoring"""
        try:
            result = subprocess.run([
                'php', '-r', f'''
                <?php
                $start = microtime(true);
                $context = stream_context_create([
                    "http" => [
                        "timeout" => 30,
                        "user_agent" => "UptimeBot/1.0"
                    ]
                ]);
                
                $content = @file_get_contents("{website["url"]}", false, $context);
                $time = round((microtime(true) - $start) * 1000);
                
                if ($content !== false && isset($http_response_header)) {{
                    preg_match("/HTTP\/[0-9.]+\s+([0-9]+)/", $http_response_header[0], $matches);
                    $status = $matches[1] ?? 0;
                    echo "$status|$time";
                    exit($status == 200 ? 0 : 1);
                }} else {{
                    echo "error|0|Connection failed";
                    exit(1);
                }}
                ?>
                '''
            ], capture_output=True, text=True, timeout=35)
            
            if result.returncode == 0:
                status_code, response_time = result.stdout.strip().split('|')
                self.log_check(website, 'up', int(response_time), int(status_code))
                return True
            return False
        except Exception as e:
            self.log_check(website, 'down', 0, 0, str(e))
            return False
    
    def check_with_go(self, website):
        """Go-based monitoring - using inline Go code"""
        try:
            go_code = f'''
            package main
            import (
                "fmt"
                "net/http"
                "time"
                "os"
            )
            func main() {{
                client := &http.Client{{Timeout: 30 * time.Second}}
                start := time.Now()
                
                resp, err := client.Get("{website["url"]}")
                if err != nil {{
                    fmt.Printf("error|0|%v", err)
                    os.Exit(1)
                }}
                defer resp.Body.Close()
                
                duration := time.Since(start).Milliseconds()
                fmt.Printf("%d|%d", resp.StatusCode, duration)
                
                if resp.StatusCode == 200 {{
                    os.Exit(0)
                }} else {{
                    os.Exit(1)
                }}
            }}
            '''
            
            # Write Go code to temporary file
            with open('/tmp/checker.go', 'w') as f:
                f.write(go_code)
            
            # Compile and run
            compile_result = subprocess.run(['go', 'build', '-o', '/tmp/checker', '/tmp/checker.go'], 
                                          capture_output=True, timeout=30)
            
            if compile_result.returncode == 0:
                run_result = subprocess.run(['/tmp/checker'], capture_output=True, text=True, timeout=35)
                if run_result.returncode == 0:
                    status_code, response_time = run_result.stdout.strip().split('|')
                    self.log_check(website, 'up', int(response_time), int(status_code))
                    return True
            
            return False
        except Exception as e:
            self.log_check(website, 'down', 0, 0, str(e))
            return False
    
    def log_check(self, website, status, response_time, status_code, error=""):
        """Log check result to MongoDB"""
        try:
            log_entry = {
                "website": website['url'],
                "name": website['name'],
                "status": status,
                "response_time": response_time,
                "status_code": status_code,
                "error": error,
                "checked_at": datetime.now(),
                "language": website.get('language', 'python')
            }
            db.uptime_logs.insert_one(log_entry)
            
            # Update website status
            db.websites.update_one(
                {"url": website['url']},
                {"$set": {
                    "status": status,
                    "last_checked": datetime.now(),
                    "last_response_time": response_time
                }}
            )
            
            # Send Telegram alert if website is down
            if status == 'down' and TELEGRAM_TOKEN != 'YOUR_TELEGRAM_BOT_TOKEN':
                self.send_telegram_alert(website, error)
        except Exception as e:
            print(f"❌ Logging Error: {e}")
    
    def send_telegram_alert(self, website, error):
        """Send alert via Telegram"""
        try:
            message = f"🚨 *WEBSITE DOWN* 🚨\\n\\n*{website['name']}*\\n{website['url']}\\n\\n*Error:* {error}\\n*Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # Get chat IDs from database
            chats = db.telegram_chats.find({})
            for chat in chats:
                requests.post(
                    f"{TELEGRAM_WEBHOOK_URL}/sendMessage",
                    json={
                        "chat_id": chat['chat_id'],
                        "text": message,
                        "parse_mode": "Markdown"
                    }
                )
        except Exception as e:
            print(f"❌ Telegram Alert Error: {e}")
    
    def check_all_websites(self):
        """Check all websites using different languages"""
        if not self.websites or not self.monitoring_active:
            return
        
        print(f"🔍 [{datetime.now()}] Checking {len(self.websites)} websites...")
        
        # Group websites by language for batch processing
        language_groups = {}
        for website in self.websites:
            lang = website.get('language', 'python')
            if lang not in language_groups:
                language_groups[lang] = []
            language_groups[lang].append(website)
        
        # Check websites using their assigned languages
        threads = []
        for lang, sites in language_groups.items():
            for site in sites:
                thread = threading.Thread(target=self.check_website_with_language, args=(site, lang))
                thread.start()
                threads.append(thread)
                time.sleep(0.5)  # Stagger requests
        
        for thread in threads:
            thread.join()
        
        # Log summary
        up_count = db.websites.count_documents({"status": "up"})
        print(f"📊 [{datetime.now()}] Status: {up_count}/{len(self.websites)} up")
    
    def check_website_with_language(self, website, language):
        """Check website using specific language"""
        try:
            if language == 'nodejs':
                self.check_with_nodejs(website)
            elif language == 'ruby':
                self.check_with_ruby(website)
            elif language == 'php':
                self.check_with_php(website)
            elif language == 'go':
                self.check_with_go(website)
            else:  # python
                self.check_with_python(website)
        except Exception as e:
            self.log_check(website, 'down', 0, 0, f"Language {language} error: {str(e)}")

# Global monitor instance
monitor = MultiLangUptimeMonitor()

def monitoring_loop():
    """Background monitoring loop"""
    while True:
        if monitor.monitoring_active:
            monitor.check_all_websites()
        time.sleep(300)  # 5 minutes

# Start monitoring thread
monitor_thread = threading.Thread(target=monitoring_loop, daemon=True)
monitor_thread.start()

# Flask Routes
@app.route('/')
def home():
    return jsonify({
        "status": "🚀 Multi-Language Uptime Monitor Running",
        "websites_count": len(monitor.websites),
        "languages": ["python", "nodejs", "ruby", "php", "go"],
        "timestamp": datetime.now().isoformat()
    })

@app.route('/telegram', methods=['POST'])
def telegram_webhook():
    """Handle Telegram bot commands"""
    try:
        data = request.get_json()
        message = data.get('message', {})
        text = message.get('text', '')
        chat_id = message.get('chat', {}).get('id')
        
        if not chat_id:
            return 'OK'
        
        # Save chat ID for notifications
        db.telegram_chats.update_one(
            {"chat_id": chat_id},
            {"$set": {"chat_id": chat_id, "last_active": datetime.now()}},
            upsert=True
        )
        
        # Process commands
        if text.startswith('/add'):
            parts = text.split(' ')
            if len(parts) >= 3:
                url = parts[1]
                name = ' '.join(parts[2:])
                language = 'python'
                
                if len(parts) >= 4:
                    language = parts[-1].lower()
                    name = ' '.join(parts[2:-1])
                
                if monitor.save_website_to_db(url, name, language):
                    response = f"✅ *Added Website*\\n*Name:* {name}\\n*URL:* {url}\\n*Language:* {language}"
                else:
                    response = "❌ Failed to add website"
            else:
                response = "Usage: /add <url> <name> [language]\\nLanguages: python, nodejs, ruby, php, go"
        
        elif text.startswith('/remove'):
            parts = text.split(' ')
            if len(parts) >= 2:
                url = parts[1]
                if monitor.remove_website_from_db(url):
                    response = f"✅ Removed website: {url}"
                else:
                    response = "❌ Website not found"
            else:
                response = "Usage: /remove <url>"
        
        elif text.startswith('/list'):
            websites = list(db.websites.find({}, {'_id': 0}))
            if websites:
                response = "📋 *Websites Monitoring*\\n\\n"
                for site in websites:
                    status_emoji = "✅" if site.get('status') == 'up' else "❌"
                    response += f"{status_emoji} *{site['name']}*\\n{site['url']}\\nLanguage: {site.get('language', 'python')}\\n\\n"
            else:
                response = "No websites configured"
        
        elif text.startswith('/stats'):
            total = db.websites.count_documents({})
            up = db.websites.count_documents({"status": "up"})
            response = f"📊 *Statistics*\\nTotal Websites: {total}\\nUp: {up}\\nDown: {total - up}"
        
        else:
            response = '''🤖 *Uptime Monitor Bot*\\n\\nCommands:\\n/add <url> <name> [language]\\n/remove <url>\\n/list\\n/stats\\n\\nLanguages: python, nodejs, ruby, php, go'''
        
        # Send response to Telegram
        requests.post(
            f"{TELEGRAM_WEBHOOK_URL}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": response,
                "parse_mode": "Markdown"
            }
        )
        
    except Exception as e:
        print(f"❌ Telegram Error: {e}")
    
    return 'OK'

@app.route('/add', methods=['POST'])
def add_website_api():
    """API to add website"""
    data = request.get_json()
    url = data.get('url')
    name = data.get('name', url)
    language = data.get('language', 'python')
    
    if monitor.save_website_to_db(url, name, language):
        return jsonify({"status": "success", "message": "Website added"})
    return jsonify({"status": "error", "message": "Failed to add website"})

@app.route('/status')
def status_api():
    """API to get status"""
    websites = list(db.websites.find({}, {'_id': 0}))
    return jsonify({
        "websites": websites,
        "total": len(websites),
        "up": len([w for w in websites if w.get('status') == 'up']),
        "timestamp": datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("🚀 Multi-Language Uptime Monitor Started!")
    print("📊 Websites:", len(monitor.websites))
    print("🔧 Languages: Python, Node.js, Ruby, PHP, Go")
    print("🤖 Telegram Bot: Ready")
    print("💾 MongoDB: Connected")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
