# Ballot Verification Web Application - Project Plan

## Project Overview

This web application will serve as a digital "proofreading assistant" for election officials to verify ballots before printing. The system will use GPT-5 with Code Interpreter to analyze ballot images and candidate/race data to identify potential issues such as missing ovals and misspelled candidate names.

**Key Principle**: This tool serves as "one more set of eyes" in an already robust human verification process, not as a replacement for human oversight.

## System Architecture

### Frontend (React/HTML)
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Ballot Verification UI                            │
├─────────────┬─────────────┬─────────────────┬─────────────────────────────┤
│ Text Area   │ Image       │ Analysis        │ Thinking Stream             │
│             │ Upload      │ Results         │                             │
│ Race/       │             │                 │ ┌─ Pass 1: Visual Analysis │
│ Candidate   │ PNG         │ Human-Readable  │ │  • Cropping ballot...     │
│ Data        │ Preview     │ Summary         │ │  • Checking candidate A   │
│             │             │                 │ │  • Found missing oval!   │
│ - Upload    │ [Upload     │ Missing Ovals:  │ └─ Pass 2: Content Valid. │
│   Text File │  PNG]       │ • John Doe      │    • Comparing names...   │
│ - Direct    │             │   (Confidence   │    • Spell check...       │
│   Edit      │             │    95%)         │                           │
│             │             │                 │ [Show/Hide Thinking]      │
│             │             │ Misspellings:   │                           │
│             │             │ • None found    │                           │
└─────────────┴─────────────┴─────────────────┴─────────────────────────────┘
                                   │
                            [Submit for Analysis]
```

### Backend (Flask + Background Processing)
```
┌─────────────────────────────────────────────────────────────┐
│                   Flask Application                         │
├─────────────────────────────────────────────────────────────┤
│  Routes:                                                    │
│  • POST /upload-image     - Handle PNG upload              │
│  • POST /upload-races     - Handle race/candidate text     │
│  • POST /analyze-ballot   - Trigger async LLM analysis     │
│  • GET  /analysis/{job_id}/status - Check processing       │
│  • GET  /analysis/{job_id}/results - Get final results     │
│  • GET  /analysis/{job_id}/thinking - Stream thinking      │
├─────────────────────────────────────────────────────────────┤
│  Background Worker (Threading/Celery):                     │
│  • OpenAI API Manager     - Handle long-running requests   │
│  • Job Status Tracker     - Update progress in real-time   │
│  • Thinking Stream Parser - Extract intermediate steps     │
│  • Results Formatter      - Convert JSON to human text     │
├─────────────────────────────────────────────────────────────┤
│  Services:                                                  │
│  • Image Processing       - Validate/prepare PNG files     │
│  • Text Processing        - Parse race/candidate data      │
│  • Job Queue Manager      - Track analysis jobs            │
│  • WebSocket Handler      - Real-time status updates       │
└─────────────────────────────────────────────────────────────┘
```

### LLM Integration Strategy
```
┌─────────────────────────────────────────────────────────────┐
│                    Dual-Pass Analysis                       │
├─────────────────────────────────────────────────────────────┤
│  Pass 1: Visual Analysis                                    │
│  • Focus: Missing ovals, formatting issues                 │
│  • Input: PNG image only                                   │
│  • Model: GPT-5 with Code Interpreter                      │
│  • Output: Visual anomaly report                           │
├─────────────────────────────────────────────────────────────┤
│  Pass 2: Content Validation                                │
│  • Focus: Candidate names, race completeness               │
│  • Input: PNG image + race/candidate data                  │
│  • Model: GPT-5 with Code Interpreter                      │
│  • Output: Content validation report                       │
└─────────────────────────────────────────────────────────────┘
```

## Technical Stack

### Frontend
- **Framework**: React with TypeScript
- **Styling**: CSS Modules or Tailwind CSS
- **State Management**: React hooks (useState, useReducer)
- **File Handling**: Native HTML5 file input with drag-and-drop
- **HTTP Client**: Fetch API or Axios

### Backend
- **Framework**: Flask (Python)
- **File Handling**: Werkzeug secure filename handling
- **Image Processing**: Pillow for basic image validation
- **API Integration**: OpenAI Python SDK
- **Data Validation**: Pydantic for request/response models
- **Error Handling**: Custom exception classes
- **Logging**: Python logging module

### External Services
- **LLM**: OpenAI GPT-5 with Code Interpreter enabled
- **Storage**: Local filesystem for prototype (future: cloud storage)

## Data Models

### Race/Candidate Data Format

**Input Format (Text)**:
Users provide contest and candidate data as structured text:
```
State Superintendent
  Brittany Kinser
  Jill Underly
  Reporting Units: All Reporting Units

Justice of the Supreme Court
  Brad Schimel
  Susan Crawford
  Reporting Units: All Reporting Units

Maple Bluff Village Trustee (3)
  Lilly Bickers
  Scott A. Robinson
  Jim Schuler
  Laura Peck
  Eric McLeod
  Reporting Units: V Maple Bluff Wds 1-2
```

**Internal Processing Format (JSON)**:
The backend converts text to structured data for LLM processing:
```json
{
  "races": [
    {
      "title": "State Superintendent",
      "candidates": ["Brittany Kinser", "Jill Underly"],
      "reporting_units": "All Reporting Units",
      "vote_for": 1
    },
    {
      "title": "Maple Bluff Village Trustee",
      "candidates": ["Lilly Bickers", "Scott A. Robinson", "Jim Schuler", "Laura Peck", "Eric McLeod"],
      "reporting_units": "V Maple Bluff Wds 1-2",
      "vote_for": 3
    }
  ]
}
```

### Analysis Response Format
```json
{
  "analysis_id": "uuid",
  "timestamp": "2024-12-05T10:30:00Z",
  "status": "completed",
  "human_readable_summary": "Found 2 issues on this ballot:\n\n**Missing Ovals (1 issue):**\n• John Doe in State Superintendent race is missing his oval (95% confidence)\n\n**Name Misspellings (1 issue):**\n• 'Jon Doe' should be 'John Doe' in State Superintendent race (92% confidence)\n\n**All Expected Races Present:** ✓\n**All Expected Candidates Present:** ✓",
  "thinking_stream": [
    {
      "timestamp": "2024-12-05T10:30:15Z",
      "step": "cropping_ballot",
      "description": "Extracting left column for analysis...",
      "image_url": "data:image/png;base64,..."
    },
    {
      "timestamp": "2024-12-05T10:30:22Z",
      "step": "checking_ovals",
      "description": "Scanning for ovals next to candidate names..."
    }
  ],
  "detailed_results": {
    "missing_ovals": [
      {
        "race": "State Superintendent",
        "candidate": "John Doe",
        "confidence": 0.95,
        "location": "left_column_top"
      }
    ],
    "misspelled_names": [
      {
        "found": "Jon Doe",
        "expected": "John Doe",
        "race": "State Superintendent",
        "confidence": 0.92
      }
    ]
  }
}
```

## LLM Prompt Strategy

### Pass 1: Visual Analysis Prompt
```
You are proofing a draft ballot before it goes to the printer. I need you to check specifically for missing ovals (selection bubbles) next to candidate names and referendum options.

The ballot layout:
- Three columns, read top to bottom then left to right
- Each contest starts with the race name and voting instructions ("Vote for 1", "Vote for 3", etc.)
- Each candidate should have an oval in front of their name
- Referendum questions have "Yes" and "No" options, each with an oval
- Sometimes the ballot software drops ovals during generation

Use your Code Interpreter to:
- Systematically examine each column
- Crop sections to focus on individual contests
- Count candidates vs ovals in each race
- Zoom in on areas where ovals might be missing

Report ONLY missing ovals with:
- Race name
- Candidate/option name
- Confidence level
- Location description

Ignore minor formatting issues, alignment problems, or text quality - focus solely on missing selection ovals.
```

### Pass 2: Content Validation Prompt
```
You are proofing a draft ballot before it goes to the printer. Compare this ballot image against the expected contest and candidate data.

Expected Contests and Candidates:
{text_race_data}

Validation tasks:
1. Verify all expected races appear on the ballot
2. Check that all expected candidates are listed in each race
3. Validate candidate name spelling (look for common typos)
4. Confirm vote instructions match expected numbers (e.g., "Vote for 3" for Maple Bluff trustees)

Use your Code Interpreter to:
- Extract all text from the ballot systematically
- Parse contest names and candidate lists
- Compare extracted names against expected data using fuzzy string matching
- Calculate confidence scores for potential misspellings

Report:
- Missing races or candidates
- Misspelled names with suggested corrections
- Vote instruction mismatches
- Confidence levels for each finding

Focus on accuracy - missing content or name misspellings are critical to capture.
```

## API Endpoints

### Core Endpoints
1. **POST /api/upload-image**
   - Upload PNG ballot image
   - Validate file type and size
   - Return upload confirmation and file ID

2. **POST /api/upload-contests**
   - Upload/submit contest and candidate text data
   - Parse and validate text format
   - Return validation status and parsed structure

3. **POST /api/analyze-ballot**
   - Trigger dual-pass LLM analysis
   - Return analysis job ID immediately
   - Start background processing

4. **GET /api/analysis/{job_id}/status**
   - Check analysis job status (queued/running/completed/failed)
   - Return current progress and estimated completion

5. **GET /api/analysis/{job_id}/thinking**
   - Server-sent events endpoint for real-time thinking stream
   - Returns intermediate analysis steps as they happen
   - Includes cropped images and reasoning steps

6. **GET /api/analysis/{job_id}/results**
   - Retrieve final analysis results
   - Returns human-readable summary and detailed findings

### Utility Endpoints
5. **GET /api/health**
   - System health check

6. **POST /api/validate-data**
   - Validate race/candidate data format without analysis

## User Interface Components

### Left Panel: Contest/Candidate Data
- **Text File Upload Button**: Import .txt file with contest data
- **Text Area**: Direct editing with format highlighting
- **Format Helper**: Show/hide expected format example
- **Parse Preview**: Show how text will be interpreted

### Center-Left Panel: Ballot Image
- **Drag-and-Drop Zone**: PNG file upload
- **Image Preview**: Zoomable ballot display
- **File Info**: Name, size, dimensions
- **Clear Button**: Remove uploaded image

### Center-Right Panel: Analysis Results
- **Status Indicator**: Loading, analyzing, complete states
- **Human-Readable Summary**: Plain English results
- **Issue Details**: Expandable findings with confidence scores
- **Progress Bar**: Show analysis completion percentage

### Right Panel: Thinking Stream (Collapsible)
- **Real-Time Log**: LLM's analysis steps as they happen
- **Image Previews**: Show cropped ballot sections being analyzed
- **Reasoning Steps**: Display model's thought process
- **Toggle Visibility**: Show/hide thinking stream panel

### Bottom Panel: Actions
- **Analyze Button**: Start ballot verification
- **Reset Button**: Clear all inputs and results
- **Save Session**: Preserve current state (future enhancement)

## Development Phases

### Phase 1: Core Infrastructure (Week 1-2)
- [ ] Set up Flask backend with basic routing
- [ ] Create React frontend with component structure
- [ ] Implement file upload functionality
- [ ] Basic OpenAI API integration
- [ ] Error handling and logging

### Phase 2: LLM Integration (Week 3-4)
- [ ] Implement async background job processing
- [ ] Develop dual-pass analysis workflow with focused prompts
- [ ] Add thinking stream capture and parsing
- [ ] Create text-to-JSON conversion for contest data
- [ ] Build human-readable result formatting
- [ ] Add real-time progress tracking via WebSockets/SSE
- [ ] Test with sample ballots from experiments

### Phase 3: UI Polish and Validation (Week 5-6)
- [ ] Enhance frontend UX/UI
- [ ] Add comprehensive input validation
- [ ] Implement result visualization
- [ ] Create comprehensive error messages
- [ ] Add loading states and progress indicators

### Phase 4: Testing and Refinement (Week 7-8)
- [ ] Test with ballot dataset from experiments
- [ ] Refine prompts based on results
- [ ] Optimize API response times
- [ ] Add configuration options
- [ ] Documentation and deployment preparation

## Configuration and Environment

### Environment Variables
```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4o  # Latest model with vision + code interpreter
OPENAI_MAX_TOKENS=16000  # Higher limit for image analysis
OPENAI_TEMPERATURE=0.1  # Low temperature for consistent results

# Flask Configuration  
FLASK_ENV=development
FLASK_DEBUG=true
SECRET_KEY=your-secret-key

# File Upload Configuration
MAX_CONTENT_LENGTH=50331648  # 48MB for high-res ballot images
UPLOAD_FOLDER=./uploads
ALLOWED_EXTENSIONS=png
MAX_IMAGE_DIMENSION=4096  # Resize if larger

# Analysis Configuration
ANALYSIS_TIMEOUT=600  # 10 minutes for complex analysis
CONFIDENCE_THRESHOLD=0.7
THINKING_STREAM_ENABLED=true
```

**OpenAI API Key Setup:**
1. Add your OpenAI API key to `/Users/epaulson/development/ballot-llm-ui/backend/.env`
2. The Flask app loads environment variables using `python-dotenv`
3. The key will be available to the Flask code via `os.getenv('OPENAI_API_KEY')`
4. Make sure `.env` is in your `.gitignore` to keep the API key secure

### Development Setup
1. **Backend Setup**:
   ```bash
   source .venv/bin/activate
   cd backend
   pip install -r requirements.txt
   export FLASK_APP=app.py
   flask run
   ```

2. **Frontend Setup**:
   ```bash
   cd frontend
   npm install
   npm start
   ```

## Error Handling Strategy

### Frontend Error Handling
- Network connectivity issues
- File upload errors (size, format)
- Invalid JSON in race data
- API timeout handling

### Backend Error Handling
- OpenAI API rate limits and errors
- Image processing failures
- Invalid input data
- Analysis timeout scenarios

### User Feedback
- Clear error messages in plain language
- Suggested remediation steps
- Graceful degradation for partial failures

## Security Considerations

### Input Validation
- File type verification (PNG only)
- File size limits
- JSON schema validation
- Sanitize file names

### API Security
- Rate limiting on endpoints
- Input sanitization
- Secure file storage
- API key protection

### Data Privacy
- No permanent storage of ballot images
- Temporary file cleanup
- Audit logging for compliance

## Future Enhancements

### Short-term (Next Version)
- Support for multi-page ballots
- Batch processing multiple ballots
- Results comparison between sessions
- Export functionality (PDF reports)

### Medium-term
- Integration with election management systems
- Support for different ballot layouts
- Advanced OCR preprocessing
- User authentication and sessions

### Long-term (Agent-based Architecture)
- Specialized agents for different validation types
- Model selection based on analysis type
- Machine learning for custom validation rules
- Integration with ballot design software

## Success Metrics

### Accuracy Metrics
- False positive rate < 10%
- False negative rate < 5%
- Processing time < 60 seconds per ballot
- User satisfaction score > 4.0/5.0

### Technical Metrics
- API uptime > 99%
- Average response time < 30 seconds
- Error rate < 1%
- Successful analysis completion > 95%

## Testing Strategy

### Unit Testing
- Backend API endpoint testing
- Frontend component testing
- Data validation testing
- Error handling verification

### Integration Testing
- End-to-end workflow testing
- OpenAI API integration testing
- File upload and processing testing
- Multi-browser compatibility testing

### User Acceptance Testing
- Test with actual election officials
- Validate against known ballot issues
- Usability testing with target users
- Performance testing under load

---

## Development Progress

### ✅ Completed (Session 1)

**Phase 1: Core Infrastructure**
- [x] Flask backend setup with proper project structure
- [x] File upload functionality (PNG images)
- [x] Contest text parsing (handles indented format from CONTESTS_AND_CANDIDATES_SAMPLE.md)
- [x] Basic three-panel frontend UI
- [x] API endpoints for health, validation, uploads
- [x] Image validation and resizing
- [x] CORS configuration for frontend-backend communication
- [x] Error handling and file security

**Current Working System:**
- Backend: Flask server on port 5000
- Frontend: Simple HTTP server on port 8000 
- Image uploads: PNG files validated and stored in `backend/uploads/`
- Text parsing: Correctly handles contest format with vote counts (e.g., "Maple Bluff Village Trustee (3)")
- Validation: Real-time contest data validation

### 🎯 Next Session Goals

**Phase 2: OpenAI Integration (Focus: Missing Ovals Detection)**
- [ ] Add OpenAI Python SDK to requirements
- [ ] Implement Pass 1: Visual analysis for missing ovals only
- [ ] Update `/api/analyze-ballot` endpoint to call OpenAI
- [ ] Add async job processing for long-running analysis
- [ ] Parse and format OpenAI responses
- [ ] Update frontend to show analysis progress and results

**Priority Order:**
1. **Missing Ovals Detection**: Single-purpose analysis to validate approach
2. **Basic Results Display**: Show findings in human-readable format
3. **Error Handling**: Robust handling of OpenAI API failures
4. **Progress Updates**: Real-time status in UI

### 🔧 Setup Instructions for Next Session

**Required for OpenAI Integration:**
1. Add OpenAI API key to `backend/.env`:
   ```bash
   OPENAI_API_KEY=sk-your-actual-key-here
   ```
2. Install OpenAI SDK:
   ```bash
   source .venv/bin/activate
   pip install openai
   ```
3. Start both servers:
   ```bash
   # Terminal 1: Backend
   source .venv/bin/activate
   cd backend && python app.py
   
   # Terminal 2: Frontend
   cd frontend && python3 -m http.server 8000
   ```

**Test Data Available:**
- `test-contest-data.txt`: Sample contest format for testing
- Upload any PNG ballot image to test the complete flow

### 🐛 Known Issues
- Text file upload button is placeholder (manual paste works fine)
- Frontend uses `python3` outside venv, `python` inside venv

---

*This project plan will be updated as development progresses and requirements evolve based on user feedback and technical discoveries.*
