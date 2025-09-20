# Render Deployment Guide

## 🚀 Deploy to Render

### Step 1: Prepare Repository
1. Push your backend code to GitHub
2. Make sure all files are committed:
   - `main.py`
   - `requirements.txt`
   - `Dockerfile`
   - `render.yaml`

### Step 2: Create Render Account
1. Go to [render.com](https://render.com)
2. Sign up with GitHub
3. Connect your GitHub account

### Step 3: Deploy Web Service
1. Click "New +" → "Web Service"
2. Connect your GitHub repository
3. Configure the service:
   - **Name**: `clubhouse-bot-api`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free (or paid for better performance)

### Step 4: Environment Variables
Add these environment variables in Render dashboard:
- `PYTHON_VERSION`: `3.11.0`
- `DATA_DIR`: `/tmp/data` (optional - uses /tmp/data by default)

### Step 5: Deploy
1. Click "Create Web Service"
2. Wait for deployment to complete
3. Your API will be available at: `https://your-app-name.onrender.com`

## 🔧 Important Notes

### Free Tier Limitations
- **Sleep Mode**: Free services sleep after 15 minutes of inactivity
- **Cold Start**: First request after sleep takes ~30 seconds
- **Memory**: Limited to 512MB RAM
- **CPU**: Shared CPU resources

### Selenium in Cloud
- Runs in headless mode (no browser window)
- Chrome and ChromeDriver are pre-installed
- May be slower than local development

### Data Persistence
- Files are stored in `/app/data` directory
- Data persists between deployments
- Consider using a database for production

## 🔄 Update Frontend

Update your frontend API client to use the Render URL:

```javascript
// In src/api/clients/clubhouseBotClient.js
const API_BASE_URL = 'https://your-app-name.onrender.com';
```

## 🐛 Troubleshooting

### Common Issues
1. **Build Fails**: Check requirements.txt and Python version
2. **Pydantic Compilation Error**: Use `requirements-minimal.txt` instead
3. **Selenium Errors**: Ensure Chrome options are correct for headless mode
4. **Memory Issues**: Free tier has limited RAM
5. **Slow Performance**: Consider upgrading to paid plan

### Fix Build Errors
If you get pydantic compilation errors:

**Option 1: Use Flask (Recommended)**
1. Rename `main_flask.py` to `main.py`
2. Rename `requirements-flask.txt` to `requirements.txt`
3. Update start command to: `python main.py`

**Option 2: Use Minimal Pydantic**
1. Replace `requirements.txt` with `requirements-minimal.txt`
2. Or manually set build command: `pip install --upgrade pip && pip install fastapi==0.104.1 uvicorn==0.24.0 selenium==4.15.2 requests==2.31.0 pydantic==2.0.3 python-multipart==0.0.6`

**Option 3: Manual Build Command**
Set build command to: `pip install --upgrade pip && pip install fastapi==0.104.1 uvicorn==0.24.0 selenium==4.15.2 requests==2.31.0 pydantic==2.0.3 python-multipart==0.0.6`

### Logs
- Check Render dashboard → Logs tab
- Look for error messages during build/deployment
- Monitor memory usage

## 📈 Scaling

### Upgrade to Paid Plan
- **Starter**: $7/month - Always on, 512MB RAM
- **Standard**: $25/month - 1GB RAM, better performance
- **Pro**: $85/month - 2GB RAM, dedicated resources

### Production Considerations
- Use PostgreSQL database instead of files
- Implement proper error handling
- Add rate limiting
- Set up monitoring and alerts
