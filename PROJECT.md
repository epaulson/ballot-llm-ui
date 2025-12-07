# Ballot Verification Web Application - Project Plan

## Project Overview

This web application serves as a digital "proofreading assistant" for election officials to verify ballots before printing. The system uses OpenAI GPT-4o with vision to analyze ballot images and candidate/race data to identify potential issues such as missing ovals and misspelled candidate names.

**Key Principle**: This tool serves as "one more set of eyes" in an already robust human verification process, not as a replacement for human oversight.

## Current Implementation Status (December 2025)

**✅ COMPLETED:**
- Multi-agent analysis system with sequential processing
- Missing ovals detection agent (Agent 1)
- Spelling error detection agent (Agent 2) 
- Frontend supporting both analysis types
- Backend job management with progress tracking
- Contest data parsing and validation
- Image upload and processing
- Comprehensive results display

**🔧 CURRENT ARCHITECTURE:**

### Multi-Agent Analysis System
```
┌─────────────────────────────────────────────────────────────┐
│              Multi-Agent Orchestrator                      │
├─────────────────────────────────────────────────────────────┤
│  analyze_ballot_with_openai()                              │
│  ├─ Agent 1: analyze_ballot_for_missing_ovals()            │
│  │  • Input: PNG image only                               │
│  │  • Focus: Missing ovals, visual anomalies              │
│  │  • Progress: 10% → 50%                                 │
│  │                                                         │
│  ├─ Agent 2: analyze_ballot_for_spelling()                 │
│  │  • Input: PNG image + contest text data                │
│  │  • Focus: Candidate name spelling errors               │
│  │  • Progress: 50% → 90%                                 │
│  │                                                         │
│  └─ combine_agent_results()                                │
│     • Merge findings from both agents                     │
│     • Generate unified summary                             │
│     • Progress: 90% → 100%                                │
└─────────────────────────────────────────────────────────────┘
```

### Frontend (HTML/CSS/JavaScript)
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Multi-Agent Ballot Verification UI                    │
├─────────────┬─────────────┬─────────────────────────────────────────────────┤
│ Contest     │ Ballot      │ Analysis Results                                │
│ Data Input  │ Image       │                                                 │
│             │ Upload      │ 🔍 Multi-Agent Analysis Summary                │
│ • Text area │             │ ├─ Agent 1: Missing ovals check               │
│ • Validate  │ • PNG only  │ └─ Agent 2: Spelling check                    │
│ • Live      │ • Preview   │                                                 │
│   feedback  │ • Metadata  │ ⚠️  Missing Ovals (2)                         │
│             │             │ ❌ Spelling Errors (1)                         │
│             │             │ ℹ️  Other Issues (1)                           │
│             │             │                                                 │
│             │             │ 📋 Detailed Analysis (collapsible)             │
│             │             │ ├─ === MISSING OVALS ANALYSIS ===             │
│             │             │ └─ === SPELLING ANALYSIS ===                  │
└─────────────┴─────────────┴─────────────────────────────────────────────────┘
                                   │
                          [Analyze Ballot] (Multi-Agent)
```

### Backend (Flask + Threading)
```
┌─────────────────────────────────────────────────────────────┐
│                Flask Application (app.py)                   │
├─────────────────────────────────────────────────────────────┤
│  API Routes:                                                │
│  • POST /api/upload-image     - Handle PNG upload          │
│  • POST /api/upload-contests  - Handle contest text data   │
│  • POST /api/validate-contests - Real-time validation      │
│  • POST /api/analyze-ballot   - Trigger multi-agent flow   │
│  • GET  /api/analysis/{id}/status - Progress tracking      │
│  • GET  /api/analysis/{id}/results - Combined results      │
│  • GET  /api/analysis/{id}/logs - OpenAI session logs      │
├─────────────────────────────────────────────────────────────┤
│  Agent Functions:                                           │
│  • analyze_ballot_for_missing_ovals()                      │
│    - Specialized prompt for oval detection                 │
│    - parse_missing_ovals_results()                         │
│  • analyze_ballot_for_spelling()                           │
│    - Compares image text vs. contest data                  │
│    - parse_spelling_results()                              │
│  • combine_agent_results()                                 │
├─────────────────────────────────────────────────────────────┤
│  Data Management:                                           │
│  • In-memory job storage (analysis_jobs{})                 │
│  • File uploads (uploaded_files{})                         │
│  • Contest data linking to jobs                            │
│  • Comprehensive OpenAI session logging                    │
└─────────────────────────────────────────────────────────────┘
```

## Technical Stack

### Frontend
- **Implementation**: Pure HTML/CSS/JavaScript (not React as originally planned)
- **Styling**: Custom CSS with responsive grid layout
- **State Management**: Global JavaScript variables and DOM manipulation
- **File Handling**: HTML5 file input with drag-and-drop support
- **HTTP Client**: Fetch API for all backend communication
- **Features**: Real-time contest data validation, progress tracking, multi-agent result display

### Backend
- **Framework**: Flask (Python) with threading for background processing
- **File Handling**: Werkzeug secure filename handling with UUID generation
- **Image Processing**: Pillow for validation and resizing
- **API Integration**: OpenAI Python SDK (GPT-4o model)
- **Data Storage**: In-memory dictionaries (analysis_jobs, uploaded_files)
- **Logging**: Comprehensive OpenAI session logging to files
- **Architecture**: Multi-agent system with specialized functions

### External Services
- **LLM**: OpenAI GPT-4o (not GPT-5 as originally planned)
- **Storage**: Local filesystem for uploaded images and logs
- **Development**: Local development servers (Flask dev server + Python http.server)

## Current Data Models

### Multi-Agent Results Structure
```json
{
  "combined_analysis": {
    "summary": "Found 2 missing ovals, 1 spelling error requiring attention before printing.",
    "total_issues": 3,
    "issues_by_type": {
      "missing_ovals": [
        {
          "description": "Missing oval for John Doe in State Superintendent",
          "candidate": "John Doe",
          "contest": "State Superintendent", 
          "confidence": "high",
          "raw_text": "..."
        }
      ],
      "spelling_errors": [
        {
          "description": "Candidate name misspelled: 'Jill Underly' appears as 'Jil Underly'",
          "candidate": "Jill Underly",
          "contest": "State Superintendent",
          "confidence": "medium",
          "raw_text": "..."
        }
      ],
      "other_issues": []
    },
    "agent_summaries": {
      "missing_ovals": "No issues detected. All candidates appear to have proper voting ovals.",
      "spelling": "Found 1 spelling error that requires attention."
    },
    "confidence_summary": "Missing ovals: Analysis completed successfully. Spelling: 1 medium-confidence finding",
    "completed_at": "2025-12-07T..."
  },
  "agent_results": {
    "missing_ovals": {
      "agent": "missing_ovals",
      "raw_analysis": "I carefully examined the ballot...",
      "findings": { ... },
      "completed_at": "..."
    },
    "spelling": {
      "agent": "spelling", 
      "raw_analysis": "I compared the candidate names...",
      "findings": { ... },
      "completed_at": "..."
    }
  }
}
```

### Contest Data Format
**Input Format (Text)**:
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
```json
{
  "contests": [
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

## Development Insights & Next Session Context

### Key Implementation Decisions Made
1. **Agent Architecture**: Chose sequential execution over parallel for better debugging and progress tracking
2. **Backward Compatibility**: Frontend handles both old single-agent and new multi-agent result structures
3. **Prompt Separation**: Currently prompts are embedded in agent functions (needs refactoring)
4. **Error Handling**: Each agent has individual error handling with comprehensive logging
5. **Progress Tracking**: Real-time updates showing which agent is currently running

### Known Issues for Next Session
1. **False Positive Error Reporting**: 
   - Backend/OpenAI reporting "Everything looks good" but UI flags as errors
   - Need to improve result parsing to distinguish between "no issues found" and "analysis failed"
   - Current parsing logic may be too aggressive in flagging text as problems

2. **Prompt Management**: 
   - Prompts are currently hardcoded in agent functions
   - Need to externalize prompts to separate files/configuration
   - Will improve prompt editing and testing workflow

### Current Prompt Structures

**Missing Ovals Prompt** (in `analyze_ballot_for_missing_ovals()`):
- Focus: Visual analysis of ballot image only
- Looking for: Missing ovals, visual anomalies
- Output: Structured report with confidence levels

**Spelling Prompt** (in `analyze_ballot_for_spelling()`):
- Focus: Comparing image text against official contest data
- Input: Both image and contest text data
- Looking for: Spelling discrepancies, name mismatches
- Output: Comparison report with specific candidate/contest references

### Recommended Next Steps
1. **Extract Prompts**: Move prompts to external files (JSON/YAML) for easier editing
2. **Improve Result Parsing**: Fix false positive error detection when "no issues found"
3. **Enhance Error Classification**: Better distinguish between analysis failures and successful "no issues" results
4. **Prompt Optimization**: Refine prompts based on real-world testing results
5. **Add Confidence Tuning**: Allow adjustment of confidence thresholds for different issue types

## Development Workflow

### Setup Instructions
```bash
# Backend setup
cd ballot-llm-ui
source .venv/bin/activate
cd backend
python app.py  # Runs on http://localhost:5000

# Frontend setup (separate terminal)
cd ballot-llm-ui/frontend  
python3 -m http.server 8000  # Serves on http://localhost:8000
```

### File Structure
```
ballot-llm-ui/
├── backend/
│   ├── app.py                 # Main Flask application with all agents
│   ├── requirements.txt       # Python dependencies
│   ├── uploads/              # Uploaded ballot images
│   └── openai-sessions/      # Detailed API call logs
├── frontend/
│   ├── index.html            # Complete frontend application
│   └── test-results.html     # Testing/development page
├── PROJECT.md               # This documentation
├── README.md                # Basic project info
└── .venv/                   # Python virtual environment
```

### Key Functions to Understand for Next Session
- `analyze_ballot_with_openai()`: Main orchestrator function
- `analyze_ballot_for_missing_ovals()`: Agent 1 implementation  
- `analyze_ballot_for_spelling()`: Agent 2 implementation
- `parse_missing_ovals_results()` / `parse_spelling_results()`: Result parsing logic
- `combine_agent_results()`: Multi-agent result combination
- `displayAnalysisResults()`: Frontend result rendering (JavaScript)

### Debugging & Logging
- **OpenAI Sessions**: All API calls logged to `backend/openai-sessions/{job_id}.log`
- **Browser Console**: Frontend debugging and API response inspection
- **Flask Debug Mode**: Enabled for development with auto-restart
- **Job Status Tracking**: Real-time progress via `/api/analysis/{job_id}/status`

### Testing Tips
- Use test contest data from existing examples
- Upload PNG ballot images (JPG not supported)
- Monitor browser network tab for API calls
- Check backend terminal for Python errors
- Review OpenAI session logs for detailed prompt/response analysis

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

## Current Status Summary

**✅ WORKING SYSTEM**: The multi-agent ballot verification tool is fully functional with:
- Two specialized agents (missing ovals + spelling errors) 
- Complete frontend with multi-agent result display
- Background job processing with real-time progress tracking
- Comprehensive OpenAI session logging
- Contest data parsing and validation

**🔧 NEXT PRIORITIES**:
1. **Prompt Externalization**: Move hardcoded prompts to external configuration files
2. **False Positive Fix**: Improve result parsing to distinguish "no issues found" from "analysis failed"  
3. **Prompt Optimization**: Refine prompts based on testing results

**📁 DEPLOYMENT**: Both frontend and backend run on local development servers and are ready for testing with real ballot images.
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

### ✅ Completed (Sessions 1-2)

**Phase 1: Core Infrastructure ✅**
- [x] Flask backend setup with proper project structure
- [x] File upload functionality (PNG images)
- [x] Contest text parsing (handles indented format)
- [x] Basic three-panel frontend UI
- [x] API endpoints for health, validation, uploads
- [x] Image validation and resizing
- [x] CORS configuration for frontend-backend communication
- [x] Error handling and file security

**Phase 2: OpenAI Integration - Missing Ovals Detection ✅**
- [x] OpenAI GPT-4o with vision integration
- [x] Comprehensive session logging system (`backend/openai-sessions/`)
- [x] Background job processing with threading
- [x] Visual analysis prompt implementation (from OVAL_PROMPT.md)
- [x] Smart results parsing and structuring
- [x] Real-time status polling in frontend
- [x] Enhanced results display with organized sections

**UI/UX Improvements ✅**
- [x] Structured results display (Summary, Missing Ovals, Other Issues)
- [x] Markdown-to-HTML conversion for readable formatting
- [x] Scrollable results container with proper styling
- [x] Color-coded sections and confidence badges
- [x] Collapsible raw analysis section
- [x] Professional, clean interface matching election software standards

### 🏗️ Architecture Implementation

**Backend Job Processing System**
```python
# In-memory job tracking (current implementation)
analysis_jobs = {
    'job_id': {
        'status': 'queued|processing|completed|error',
        'progress': 0-100,
        'message': 'Current status message',
        'image_file_id': 'uuid',
        'contest_data_id': 'uuid',
        'created_at': 'ISO timestamp',
        'results': {  # Only when completed
            'raw_analysis': 'OpenAI response text',
            'findings': {
                'missing_ovals': [...],
                'other_issues': [...],
                'summary': 'text',
                'total_issues': int,
                'confidence_summary': 'text'
            },
            'completed_at': 'ISO timestamp'
        }
    }
}
```

**OpenAI Session Logging**
- Location: `backend/openai-sessions/{job_id}.log`
- Format: JSON entries separated by `---`
- Thread-safe append-only logging
- Captures: requests, responses, metadata, errors
- Base64 image data is redacted for readability
- Added to .gitignore for security

**API Endpoints (Current)**
```bash
POST /api/upload-image          # Upload PNG ballot
POST /api/upload-contests       # Upload contest text data
POST /api/analyze-ballot        # Start OpenAI analysis
GET  /api/analysis/{id}/status  # Check job progress
GET  /api/analysis/{id}/results # Get structured findings
GET  /api/analysis/{id}/logs    # Debug logs (development)
GET  /api/health               # System status
```

**Frontend Architecture**
- Polling-based status updates (2-second intervals)
- Structured results rendering with sections
- Markdown conversion for OpenAI response text
- Confidence badge system (high/medium/low)
- Scrollable, organized display replacing plain text

### 🔧 Key Functions for Extension

**Adding New Analysis Types (Pattern)**
1. Create analysis function: `analyze_ballot_with_[type](image_path, job_id, **kwargs)`
2. Add logging calls: `log_openai_session(job_id, event_type, data)`
3. Update parsing: `parse_[type]_results(analysis_text)`
4. Extend frontend: Add new result section type

**OpenAI Integration Pattern**
```python
# 1. Log session start
log_openai_session(job_id, 'metadata', {'action': 'start_[type]_analysis'})

# 2. Prepare and log request
messages = [...] # Build prompt with image/text
log_openai_request(job_id, model, messages, **params)

# 3. Call OpenAI and log response
response = client.chat.completions.create(...)
log_openai_response(job_id, response)

# 4. Parse and structure results
findings = parse_results(response.choices[0].message.content)
log_openai_session(job_id, 'metadata', {'action': 'analysis_completed'})
```

### 🎯 Next Session: Spelling Analysis Implementation

**Goal**: Implement Pass 2 analysis for candidate name spelling validation

**Required Implementation**:
1. **New Analysis Function**: `analyze_ballot_spelling(image_path, contest_data, job_id)`
   - Combines image + contest text data
   - Uses OCR-style prompt to extract ballot text
   - Compares against expected candidate names
   - Reports spelling mismatches with confidence

2. **Enhanced Job System**: 
   - Support for multi-pass analysis (visual + spelling)
   - Sequential job execution within single analysis request
   - Combined results aggregation

3. **Contest Data Integration**:
   - Access parsed contest data from `analysis_jobs[f"contests_{data_id}"]`
   - Format candidate names for comparison
   - Handle fuzzy string matching for typos

4. **Frontend Updates**:
   - New "Spelling Issues" section in results
   - Display expected vs. found name comparisons
   - Integrate with existing structured display

**Prompt Strategy for Spelling Analysis**:
```
Compare the candidate names in this ballot image against the expected list.

Expected candidates by contest:
{formatted_contest_data}

Tasks:
1. Extract all candidate names from the ballot using OCR
2. Group by contest/race
3. Compare extracted names to expected names
4. Report any spelling differences with confidence levels
5. Use fuzzy matching to catch common typos

Focus on candidate name accuracy - this is critical for ballot validation.
```

### 🔧 Development Environment

**Current Setup**:
- Backend: Flask dev server on http://localhost:5000
- Frontend: Python HTTP server on http://localhost:8000
- OpenAI: GPT-4o with vision, configured for low temperature (0.1)
- Logging: Comprehensive session logs in `backend/openai-sessions/`
- Virtual env: `.venv` in project root

**Environment Files**:
- `.env`: Contains OPENAI_API_KEY (not in repo)
- `.env.example`: Template for required environment variables
- `.gitignore`: Includes openai-sessions/ and .env

**Key Dependencies**:
```
flask
werkzeug
pillow
python-dotenv
flask-cors
uuid
openai
```

### 🐛 Known Considerations

**Current Limitations**:
- In-memory job storage (will need persistence for production)
- Single-threaded background processing (works for demo)
- Basic error handling (needs enhancement for production)
- No user authentication (appropriate for current scope)

**Performance Notes**:
- OpenAI API calls: ~10-30 seconds for ballot analysis
- Image processing: <1 second for validation/resize
- Frontend polling: 2-second intervals for status updates

**Security**:
- OpenAI sessions contain sensitive ballot data (properly gitignored)
- Image uploads stored in backend/uploads/ (cleanup needed)
- API key properly protected in environment variables

---

*Updated through Session 2. Ready for spelling analysis implementation in Session 3.*
