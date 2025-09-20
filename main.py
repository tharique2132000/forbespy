from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import threading
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
import os
import json

app = FastAPI(title="Clubhouse Bot API", version="1.0.0")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API URLs
GIF_URL = 'https://www.clubhouse.com/web_api/gif_reaction'
CHANNEL_FEED_URL = 'https://www.clubhouse.com/web_api/get_feed_v3'

# File paths - use data directory for cloud deployment
import os
DATA_DIR = os.getenv('DATA_DIR', '/app/data')
TOKEN_FILE = os.path.join(DATA_DIR, 'web_token.txt')
GIPHY_FILE = os.path.join(DATA_DIR, 'giphy.txt')

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Global bot state
bot_running = False
bot_thread = None

# Pydantic models
class LoginRequest(BaseModel):
    username: str
    password: str

class GiphyRequest(BaseModel):
    giphy_id: str

class BotStatus(BaseModel):
    running: bool
    message: str

class SessionInfo(BaseModel):
    has_token: bool
    token: Optional[str] = None

class GiphyList(BaseModel):
    giphy_ids: List[str]

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

# API Endpoints
@app.get("/")
async def root():
    return {"message": "Clubhouse Bot API is running"}

@app.post("/auth/login")
async def login(request: LoginRequest):
    """Login endpoint (placeholder - you may want to implement actual authentication)"""
    try:
        # For now, just create an empty token file
        # In a real implementation, you'd validate credentials
        with open(TOKEN_FILE, "w") as f:
            f.write("")  # Empty token for now
        return {"message": "Login successful", "success": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Login failed: {str(e)}")

@app.get("/auth/session", response_model=SessionInfo)
async def get_session():
    """Get current session status"""
    token = get_session_id()
    return SessionInfo(has_token=bool(token), token=token)

@app.post("/auth/signup")
async def signup_clubhouse(background_tasks: BackgroundTasks):
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
        except Exception as e:
            print(f"Signup error: {str(e)}")
    
    background_tasks.add_task(run_signup_browser)
    return {"message": "Signup process started. Check browser window."}

@app.delete("/auth/token")
async def clear_token():
    """Clear stored session token"""
    try:
        open(TOKEN_FILE, 'w').close()
        return {"message": "Token cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear token: {str(e)}")

@app.get("/giphy", response_model=GiphyList)
async def get_giphy_list():
    """Get list of stored GIF IDs"""
    giphy_ids = get_giphy_ids()
    return GiphyList(giphy_ids=giphy_ids)

@app.post("/giphy")
async def add_giphy(request: GiphyRequest):
    """Add a new GIF ID"""
    try:
        with open(GIPHY_FILE, 'a') as f:
            f.write(request.giphy_id + "\n")
        return {"message": f"GIF ID {request.giphy_id} added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add GIF: {str(e)}")

@app.delete("/giphy")
async def clear_giphy():
    """Clear all GIF IDs"""
    try:
        open(GIPHY_FILE, 'w').close()
        return {"message": "All GIF IDs cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear GIFs: {str(e)}")

@app.get("/bot/status", response_model=BotStatus)
async def get_bot_status():
    """Get current bot status"""
    return BotStatus(running=bot_running, message="Bot is running" if bot_running else "Bot is stopped")

@app.post("/bot/start")
async def start_bot():
    """Start the GIF bot"""
    global bot_running, bot_thread
    
    if bot_running:
        return {"message": "Bot is already running"}
    
    session_id = get_session_id()
    if not session_id:
        raise HTTPException(status_code=400, detail="No session token found. Please login or signup first.")
    
    giphy_ids = get_giphy_ids()
    if not giphy_ids:
        raise HTTPException(status_code=400, detail="No GIF IDs found. Please add some GIFs first.")
    
    bot_running = True
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    return {"message": "Bot started successfully"}

@app.post("/bot/stop")
async def stop_bot():
    """Stop the GIF bot"""
    global bot_running
    
    if not bot_running:
        return {"message": "Bot is not running"}
    
    bot_running = False
    return {"message": "Bot stopped successfully"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
