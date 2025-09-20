# Clubhouse Bot Backend

This is the FastAPI backend that handles Selenium automation for the Clubhouse GIF Bot.

## Setup

1. **Install Python Dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Install ChromeDriver**
   - Download ChromeDriver from https://chromedriver.chromium.org/
   - Make sure it's in your PATH or in the same directory as the Python script
   - Alternatively, install via package manager:
     - Windows: `choco install chromedriver`
     - macOS: `brew install chromedriver`
     - Linux: `sudo apt-get install chromium-chromedriver`

3. **Run the Backend**
   ```bash
   python main.py
   ```
   
   The API will be available at `http://localhost:8000`

## API Endpoints

### Authentication
- `POST /auth/login` - Login with username/password
- `GET /auth/session` - Get current session status
- `POST /auth/signup` - Start automated Clubhouse signup
- `DELETE /auth/token` - Clear stored session token

### GIF Management
- `GET /giphy` - Get list of stored GIF IDs
- `POST /giphy` - Add a new GIF ID
- `DELETE /giphy` - Clear all GIF IDs

### Bot Control
- `GET /bot/status` - Get current bot status
- `POST /bot/start` - Start the automated bot
- `POST /bot/stop` - Stop the automated bot

## How It Works

1. **Session Management**: The backend stores Clubhouse session tokens in `web_token.txt`
2. **GIF Storage**: GIF IDs are stored in `giphy.txt`
3. **Automation**: Uses Selenium to:
   - Open Chrome browser for Clubhouse signup
   - Extract session cookies automatically
   - Send GIF reactions to Clubhouse channels
4. **API Communication**: Provides REST endpoints for the React frontend

## Files Created

- `web_token.txt` - Stores Clubhouse session token
- `giphy.txt` - Stores GIF IDs for reactions

## Security Notes

- Session tokens are stored locally and should be kept secure
- The automated signup opens a browser window that stays open
- Make sure to clear tokens when done using the bot
