from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import time
import requests
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

app = Flask(__name__)
CORS(app)

# API URLs
GIF_URL = 'https://www.clubhouse.com/web_api/gif_reaction'
CHANNEL_FEED_URL = 'https://www.clubhouse.com/web_api/get_feed_v3'

# File paths - use data directory for cloud deployment
DATA_DIR = os.getenv('DATA_DIR', '/app/data')
TOKEN_FILE = os.path.join(DATA_DIR, 'web_token.txt')
GIPHY_FILE = os.path.join(DATA_DIR, 'giphy.txt')

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Global bot state
bot_running = False
bot_thread = None

# Utility functions
def get_session_id():
    try:
        with open(TOKEN_FILE, 'r') as file:
            return file.readline().strip()
    except:
        return None

def get_channel_id(session_id):
    try:
        headers = {'Cookie': f'sessionid={session_id};'}
        response = requests.post(CHANNEL_FEED_URL, headers=headers, json={})
        items = response.json().get('items', [])
        for item in items:
            channel_info = item.get('channel')
            if channel_info and 'channel' in channel_info:
                return channel_info['channel']
        return None
    except:
        return None

def get_giphy_ids():
    try:
        with open(GIPHY_FILE, 'r') as file:
            return [line.strip() for line in file if line.strip()]
    except:
        return []

def send_gif_reaction(channel_id, giphy_id, headers):
    try:
        payload = {'channel': channel_id, 'giphy_id': giphy_id}
        requests.post(GIF_URL, headers=headers, json=payload)
        return f"Now Showing GIF Successfully\nGiphy ID : {giphy_id} & Room ID : {channel_id}"
    except Exception as e:
        return f"Error: {e}"

def run_bot():
    global bot_running
    session_id = get_session_id()
    if not session_id:
        return
    
    headers = {'Cookie': f'sessionid={session_id};'}
    giphy_ids = get_giphy_ids()
    if not giphy_ids:
        return
    
    i = 0
    while bot_running:
        channel_id = get_channel_id(session_id)
        if channel_id:
            msg = send_gif_reaction(channel_id, giphy_ids[i], headers)
            print(f"Bot: {msg}")  # Log to console
            i = (i + 1) % len(giphy_ids)
        else:
            print("Bot: No channel found, Retrying...")
            time.sleep(10)
            continue
        time.sleep(15)

# API Routes
@app.route('/')
def root():
    return {"message": "Clubhouse Bot API is running"}

@app.route('/auth/login', methods=['POST'])
def login():
    """Login endpoint (placeholder - you may want to implement actual authentication)"""
    try:
        data = request.get_json()
        # For now, just create an empty token file
        # In a real implementation, you'd validate credentials
        with open(TOKEN_FILE, "w") as f:
            f.write("")  # Empty token for now
        return {"message": "Login successful", "success": True}
    except Exception as e:
        return {"error": f"Login failed: {str(e)}"}, 400

@app.route('/auth/session', methods=['GET'])
def get_session():
    """Get current session status"""
    token = get_session_id()
    return {"has_token": bool(token), "token": token}

@app.route('/auth/signup', methods=['POST'])
def signup_clubhouse():
    """Start Clubhouse signup process"""
    def run_signup_browser():
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # Run in headless mode for cloud
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            driver = webdriver.Chrome(options=chrome_options)
            driver.get("https://www.clubhouse.com/signin")
            
            WebDriverWait(driver, 180).until(
                lambda d: any(c['name'] == 'sessionid' for c in d.get_cookies())
            )
            cookies = driver.get_cookies()
            session_cookie = None
            for cookie in cookies:
                if cookie['name'] == 'sessionid':
                    session_cookie = cookie['value']
                    break
            
            if session_cookie:
                with open(TOKEN_FILE, 'w') as f:
                    f.write(session_cookie)
                print("Clubhouse token saved successfully")
            else:
                print("Token not found. Try again.")
            driver.quit()
        except Exception as e:
            print(f"Signup error: {str(e)}")
    
    threading.Thread(target=run_signup_browser, daemon=True).start()
    return {"message": "Signup process started. Check browser window."}

@app.route('/auth/token', methods=['DELETE'])
def clear_token():
    """Clear stored session token"""
    try:
        open(TOKEN_FILE, 'w').close()
        return {"message": "Token cleared successfully"}
    except Exception as e:
        return {"error": f"Failed to clear token: {str(e)}"}, 500

@app.route('/giphy', methods=['GET'])
def get_giphy_list():
    """Get list of stored GIF IDs"""
    giphy_ids = get_giphy_ids()
    return {"giphy_ids": giphy_ids}

@app.route('/giphy', methods=['POST'])
def add_giphy():
    """Add a new GIF ID"""
    try:
        data = request.get_json()
        giphy_id = data.get('giphy_id')
        if giphy_id:
            with open(GIPHY_FILE, 'a') as f:
                f.write(giphy_id + "\n")
            return {"message": f"GIF ID {giphy_id} added successfully"}
        return {"error": "No giphy_id provided"}, 400
    except Exception as e:
        return {"error": f"Failed to add GIF: {str(e)}"}, 500

@app.route('/giphy', methods=['DELETE'])
def clear_giphy():
    """Clear all GIF IDs"""
    try:
        open(GIPHY_FILE, 'w').close()
        return {"message": "All GIF IDs cleared successfully"}
    except Exception as e:
        return {"error": f"Failed to clear GIFs: {str(e)}"}, 500

@app.route('/bot/status', methods=['GET'])
def get_bot_status():
    """Get current bot status"""
    return {"running": bot_running, "message": "Bot is running" if bot_running else "Bot is stopped"}

@app.route('/bot/start', methods=['POST'])
def start_bot():
    """Start the GIF bot"""
    global bot_running, bot_thread
    
    if bot_running:
        return {"message": "Bot is already running"}
    
    session_id = get_session_id()
    if not session_id:
        return {"error": "No session token found. Please login or signup first."}, 400
    
    giphy_ids = get_giphy_ids()
    if not giphy_ids:
        return {"error": "No GIF IDs found. Please add some GIFs first."}, 400
    
    bot_running = True
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    return {"message": "Bot started successfully"}

@app.route('/bot/stop', methods=['POST'])
def stop_bot():
    """Stop the GIF bot"""
    global bot_running
    
    if not bot_running:
        return {"message": "Bot is not running"}
    
    bot_running = False
    return {"message": "Bot stopped successfully"}

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
