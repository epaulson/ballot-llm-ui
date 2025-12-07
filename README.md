# Ballot LLM UI

## Quick Start for Development

### Setup
```bash
# Activate venv and install dependencies
source .venv/bin/activate
cd backend && pip install -r requirements.txt
```

### Add OpenAI API Key
Edit `backend/.env` and replace:
```
OPENAI_API_KEY=sk-your-actual-api-key-here
```

### Run Both Servers
```bash
# Terminal 1: Backend
source .venv/bin/activate
cd backend && python app.py

# Terminal 2: Frontend  
cd frontend && python3 -m http.server 8000
```

### Access Application
- Frontend: http://localhost:8000
- Backend API: http://localhost:5000/api/health

### Test Data
Use `test-contest-data.txt` for contest data input.

## Status
✅ **Working**: File uploads, text parsing, basic UI
🚧 **Next**: OpenAI integration for missing ovals detection