from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
import os
import uuid
from datetime import datetime
from PIL import Image
import json
import base64
import threading
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# OpenAI Session Logging
OPENAI_SESSIONS_DIR = os.path.join(os.path.dirname(__file__), 'openai-sessions')
os.makedirs(OPENAI_SESSIONS_DIR, exist_ok=True)

def log_openai_session(job_id, event_type, data, error=None):
    """
    Log OpenAI API interactions to a job-specific file
    
    Args:
        job_id: Unique job identifier
        event_type: 'request', 'response', 'error', 'metadata'
        data: The data to log (request payload, response content, etc.)
        error: Optional error information
    """
    log_file = os.path.join(OPENAI_SESSIONS_DIR, f"{job_id}.log")
    
    timestamp = datetime.now().isoformat()
    log_entry = {
        'timestamp': timestamp,
        'job_id': job_id,
        'event_type': event_type,
        'data': data
    }
    
    if error:
        log_entry['error'] = error
    
    try:
        # Use append mode with explicit line separator for thread safety
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, indent=2, ensure_ascii=False))
            f.write('\n---\n')  # Separator between entries
        
    except Exception as e:
        # Fallback logging to prevent crashes
        print(f"Failed to log OpenAI session for job {job_id}: {e}")

def log_openai_request(job_id, model, messages, **kwargs):
    """Log the request being sent to OpenAI"""
    request_data = {
        'model': model,
        'messages': messages,
        'parameters': kwargs
    }
    
    # Redact base64 image data for readability (keep just metadata)
    sanitized_messages = []
    for msg in messages:
        if isinstance(msg.get('content'), list):
            sanitized_content = []
            for content_item in msg['content']:
                if content_item.get('type') == 'image_url':
                    # Replace base64 data with metadata
                    image_url = content_item.get('image_url', {})
                    url = image_url.get('url', '')
                    if url.startswith('data:image'):
                        # Extract just the metadata part
                        sanitized_content.append({
                            'type': 'image_url',
                            'image_url': {
                                'url': '[BASE64_IMAGE_DATA_REDACTED]',
                                'detail': image_url.get('detail', 'auto'),
                                'original_length': len(url)
                            }
                        })
                    else:
                        sanitized_content.append(content_item)
                else:
                    sanitized_content.append(content_item)
            sanitized_messages.append({
                'role': msg['role'],
                'content': sanitized_content
            })
        else:
            sanitized_messages.append(msg)
    
    request_data['messages'] = sanitized_messages
    log_openai_session(job_id, 'request', request_data)

def log_openai_response(job_id, response):
    """Log the response received from OpenAI"""
    try:
        # Convert response to dict for logging
        response_data = {
            'id': response.id,
            'object': response.object,
            'created': response.created,
            'model': response.model,
            'choices': [],
            'usage': response.usage.model_dump() if response.usage else None
        }
        
        for choice in response.choices:
            choice_data = {
                'index': choice.index,
                'message': {
                    'role': choice.message.role,
                    'content': choice.message.content
                },
                'finish_reason': choice.finish_reason
            }
            response_data['choices'].append(choice_data)
        
        log_openai_session(job_id, 'response', response_data)
        
    except Exception as e:
        # Fallback to raw response logging
        log_openai_session(job_id, 'response', str(response), error=str(e))

app = Flask(__name__)
CORS(app)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 52428800))
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', './uploads')
app.config['ALLOWED_EXTENSIONS'] = set(os.getenv('ALLOWED_EXTENSIONS', 'png').split(','))
app.config['MAX_IMAGE_DIMENSION'] = int(os.getenv('MAX_IMAGE_DIMENSION', 4096))

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# In-memory storage for demo (replace with database in production)
analysis_jobs = {}
uploaded_files = {}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def validate_and_resize_image(filepath):
    """Validate image and resize if necessary"""
    try:
        with Image.open(filepath) as img:
            # Check if image is valid
            img.verify()
            
        # Reopen for processing (verify closes the file)
        with Image.open(filepath) as img:
            # Check dimensions and resize if needed
            max_dim = app.config['MAX_IMAGE_DIMENSION']
            if img.width > max_dim or img.height > max_dim:
                img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
                img.save(filepath, 'PNG', optimize=True)
                
            return {
                'width': img.width,
                'height': img.height,
                'format': img.format,
                'mode': img.mode
            }
    except Exception as e:
        raise ValueError(f"Invalid image file: {str(e)}")

def parse_contest_text(text):
    """Parse contest and candidate data from text format"""
    contests = []
    current_contest = None
    
    lines = text.strip().split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i].rstrip()
        
        # Skip empty lines
        if not line:
            i += 1
            continue
            
        # If line doesn't start with space, it's a contest name
        if not line.startswith(' ') and not line.startswith('\t'):
            # Save previous contest if exists
            if current_contest:
                contests.append(current_contest)
            
            # Extract vote count from parentheses if present
            vote_for = 1
            contest_name = line
            if '(' in line and ')' in line:
                parts = line.split('(')
                contest_name = parts[0].strip()
                vote_count_str = parts[1].split(')')[0].strip()
                try:
                    vote_for = int(vote_count_str)
                except ValueError:
                    pass  # Keep default of 1
            
            current_contest = {
                'title': contest_name,
                'candidates': [],
                'reporting_units': '',
                'vote_for': vote_for
            }
        else:
            # Line starts with space/tab - it's either a candidate or reporting units
            content = line.strip()
            if content.startswith('Reporting Units:'):
                if current_contest:
                    current_contest['reporting_units'] = content.replace('Reporting Units:', '').strip()
            else:
                # It's a candidate name
                if current_contest and content:
                    current_contest['candidates'].append(content)
        
        i += 1
    
    # Don't forget the last contest
    if current_contest:
        contests.append(current_contest)
    
    return {'contests': contests}

def encode_image(image_path):
    """Encode image to base64 for OpenAI API"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_ballot_with_openai(image_path, job_id):
    """Analyze ballot image for missing ovals using OpenAI GPT-4o with vision"""
    try:
        # Log session start
        log_openai_session(job_id, 'metadata', {
            'action': 'start_analysis',
            'image_path': image_path,
            'image_size': os.path.getsize(image_path)
        })

        # Update job status
        if job_id in analysis_jobs:
            analysis_jobs[job_id]['status'] = 'processing'
            analysis_jobs[job_id]['progress'] = 10
            analysis_jobs[job_id]['message'] = 'Encoding image for analysis...'

        # Encode the image
        base64_image = encode_image(image_path)
        
        # Log image encoding completion
        log_openai_session(job_id, 'metadata', {
            'action': 'image_encoded',
            'base64_length': len(base64_image)
        })
        
        if job_id in analysis_jobs:
            analysis_jobs[job_id]['progress'] = 30
            analysis_jobs[job_id]['message'] = 'Sending to OpenAI for visual analysis...'

        # Create the visual analysis prompt
        prompt = """I am trying to proof some drafts of ballots for an upcoming election, before we send them to the printer to create the actual ballots. I am attaching a PNG file of one of the ballots, I would like you to look at it carefully and try to see if there are any mistakes. I am specifically worried that the ovals near each candidate might be missing - sometimes the software drops them. 

The ballot is laid out as three columns, read top to bottom and then left to right. There will be several contests in each column, with the election name starting each election and some instructions on how many to vote for, and then the candidates to vote for, and there should be an oval in front of each candidate. There may also be referendum questions present, which won't have candidates but will have a 'Yes' or a 'No' as an option - and again will have an oval in front of those choices.

Please examine the ballot systematically and report:
1. Any candidates or choices that appear to be missing their voting ovals
2. Your confidence level for each finding (high/medium/low)
3. The specific location where you found the issue (contest name and candidate name)
4. Any other visual anomalies you notice

Please be thorough but focus primarily on missing ovals as that is our main concern."""

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}",
                            "detail": "high"
                        }
                    }
                ]
            }
        ]

        # Log the request (with image data redacted)
        log_openai_request(
            job_id=job_id,
            model="gpt-4o",
            messages=messages,
            max_tokens=1500,
            temperature=0.1
        )

        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=1500,
            temperature=0.1  # Low temperature for consistent analysis
        )

        # Log the response
        log_openai_response(job_id, response)

        if job_id in analysis_jobs:
            analysis_jobs[job_id]['progress'] = 80
            analysis_jobs[job_id]['message'] = 'Processing analysis results...'

        # Extract the analysis content
        analysis_content = response.choices[0].message.content
        
        # Parse the response to extract structured findings
        findings = parse_analysis_results(analysis_content)
        
        # Log the parsed findings
        log_openai_session(job_id, 'metadata', {
            'action': 'analysis_parsed',
            'findings_summary': {
                'missing_ovals_count': len(findings['missing_ovals']),
                'other_issues_count': len(findings['other_issues']),
                'total_issues': findings['total_issues']
            }
        })
        
        # Update job with results
        if job_id in analysis_jobs:
            analysis_jobs[job_id]['status'] = 'completed'
            analysis_jobs[job_id]['progress'] = 100
            analysis_jobs[job_id]['message'] = 'Analysis completed successfully'
            analysis_jobs[job_id]['results'] = {
                'raw_analysis': analysis_content,
                'findings': findings,
                'completed_at': datetime.now().isoformat()
            }

        # Log completion
        log_openai_session(job_id, 'metadata', {
            'action': 'analysis_completed',
            'status': 'success'
        })

    except Exception as e:
        # Log the error
        log_openai_session(job_id, 'error', {
            'action': 'analysis_failed',
            'error_message': str(e),
            'error_type': type(e).__name__
        })
        
        # Update job with error
        if job_id in analysis_jobs:
            analysis_jobs[job_id]['status'] = 'error'
            analysis_jobs[job_id]['progress'] = 0
            analysis_jobs[job_id]['message'] = f'Analysis failed: {str(e)}'
            analysis_jobs[job_id]['error'] = str(e)

def parse_analysis_results(analysis_text):
    """Parse OpenAI analysis results into structured format with better organization"""
    findings = {
        'missing_ovals': [],
        'other_issues': [],
        'summary': '',
        'total_issues': 0,
        'confidence_summary': '',
        'detailed_analysis': analysis_text,
        'sections': {
            'general_observations': [],
            'specific_findings': [],
            'recommendations': []
        }
    }
    
    # Split the text into lines for parsing
    lines = analysis_text.split('\n')
    current_section = None
    current_item = None
    
    # Keywords for different types of issues
    missing_oval_keywords = ['missing oval', 'no oval', 'oval missing', 'without oval', 'lacks oval']
    confidence_keywords = ['confidence:', 'confidence level:', 'high confidence', 'medium confidence', 'low confidence']
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        
        # Detect sections
        if any(header in line.lower() for header in ['general observation', 'overall', 'summary']):
            current_section = 'general_observations'
            continue
        elif any(header in line.lower() for header in ['specific finding', 'findings', 'issues found']):
            current_section = 'specific_findings'
            continue
        elif any(header in line.lower() for header in ['recommendation', 'suggest', 'next steps']):
            current_section = 'recommendations'
            continue
        
        # Parse missing ovals specifically
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in missing_oval_keywords):
            # Extract candidate/contest info
            candidate_name = extract_candidate_name(line)
            contest_name = extract_contest_name(line, lines, i)
            confidence = extract_confidence(line)
            
            missing_oval = {
                'description': clean_markdown(line),
                'candidate': candidate_name,
                'contest': contest_name,
                'confidence': confidence,
                'raw_text': line
            }
            findings['missing_ovals'].append(missing_oval)
        
        # Check for confidence levels
        elif any(keyword in line_lower for keyword in confidence_keywords):
            confidence_info = extract_confidence_info(line)
            if current_item:
                current_item['confidence_details'] = confidence_info
        
        # Categorize other issues
        elif any(keyword in line_lower for keyword in ['issue', 'problem', 'error', 'anomaly', 'concern']):
            other_issue = {
                'description': clean_markdown(line),
                'type': classify_issue_type(line),
                'severity': extract_severity(line),
                'raw_text': line
            }
            findings['other_issues'].append(other_issue)
        
        # Add to appropriate section
        if current_section and line:
            findings['sections'][current_section].append(clean_markdown(line))
    
    # Generate improved summary
    missing_count = len(findings['missing_ovals'])
    other_count = len(findings['other_issues'])
    findings['total_issues'] = missing_count + other_count
    
    if missing_count == 0 and other_count == 0:
        findings['summary'] = 'No issues detected. All candidates and choices appear to have proper voting ovals.'
        findings['confidence_summary'] = 'Analysis completed successfully with no concerns found.'
    else:
        parts = []
        if missing_count > 0:
            parts.append(f"{missing_count} missing oval{'s' if missing_count != 1 else ''}")
        if other_count > 0:
            parts.append(f"{other_count} other issue{'s' if other_count != 1 else ''}")
        
        findings['summary'] = f"Found {' and '.join(parts)} that require attention."
        
        # Count confidence levels
        high_confidence = sum(1 for oval in findings['missing_ovals'] if oval.get('confidence') == 'high')
        if high_confidence > 0:
            findings['confidence_summary'] = f"{high_confidence} high-confidence finding{'s' if high_confidence != 1 else ''}"
        else:
            findings['confidence_summary'] = "Mixed confidence levels in findings"
    
    return findings

def clean_markdown(text):
    """Remove markdown formatting for cleaner display"""
    # Remove excessive asterisks and format basic markdown
    text = text.replace('**', '')  # Remove bold markers
    text = text.replace('*', '')   # Remove italic markers
    text = text.replace('##', '')  # Remove header markers
    text = text.replace('#', '')   # Remove header markers
    return text.strip()

def extract_candidate_name(text):
    """Extract candidate name from analysis text"""
    # Look for common patterns where candidate names appear
    text_lower = text.lower()
    
    # Pattern: "for [candidate name]" or "candidate [name]"
    if 'for ' in text_lower:
        parts = text.split('for ')
        if len(parts) > 1:
            candidate_part = parts[1].split(' ')[0:3]  # Take first few words
            return ' '.join(candidate_part).strip('.,')
    
    if 'candidate ' in text_lower:
        parts = text.split('candidate ')
        if len(parts) > 1:
            candidate_part = parts[1].split(' ')[0:3]
            return ' '.join(candidate_part).strip('.,')
    
    return None

def extract_contest_name(text, all_lines, current_index):
    """Extract contest name by looking at context around the line"""
    # Look in nearby lines for contest context
    context_range = 3
    start_idx = max(0, current_index - context_range)
    end_idx = min(len(all_lines), current_index + context_range + 1)
    
    contest_keywords = ['contest', 'race', 'election', 'office', 'position']
    
    for i in range(start_idx, end_idx):
        line = all_lines[i].lower()
        if any(keyword in line for keyword in contest_keywords):
            # Extract the contest name
            for keyword in contest_keywords:
                if keyword in line:
                    parts = all_lines[i].split(keyword)
                    if len(parts) > 1:
                        return parts[1].strip('.,: ').split(' ')[0:5]  # Take first few words
    
    return None

def extract_confidence(text):
    """Extract confidence level from text"""
    text_lower = text.lower()
    if 'high confidence' in text_lower or 'high' in text_lower:
        return 'high'
    elif 'medium confidence' in text_lower or 'medium' in text_lower:
        return 'medium'
    elif 'low confidence' in text_lower or 'low' in text_lower:
        return 'low'
    return 'medium'  # Default

def extract_confidence_info(text):
    """Extract detailed confidence information"""
    return text.strip()

def classify_issue_type(text):
    """Classify the type of issue found"""
    text_lower = text.lower()
    if any(word in text_lower for word in ['format', 'layout', 'alignment']):
        return 'formatting'
    elif any(word in text_lower for word in ['spelling', 'misspell', 'typo']):
        return 'spelling'
    elif any(word in text_lower for word in ['missing', 'absent', 'not found']):
        return 'missing_content'
    else:
        return 'general'

def extract_severity(text):
    """Extract severity level from issue description"""
    text_lower = text.lower()
    if any(word in text_lower for word in ['critical', 'severe', 'major']):
        return 'high'
    elif any(word in text_lower for word in ['minor', 'small', 'slight']):
        return 'low'
    else:
        return 'medium'

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/api/upload-image', methods=['POST'])
def upload_image():
    """Handle ballot image upload"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Only PNG files are allowed'}), 400
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        filename = secure_filename(f"{file_id}.png")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Save file
        file.save(filepath)
        
        # Validate and get image info
        try:
            image_info = validate_and_resize_image(filepath)
        except ValueError as e:
            os.remove(filepath)  # Clean up invalid file
            return jsonify({'error': str(e)}), 400
        
        # Store file info
        file_info = {
            'file_id': file_id,
            'original_filename': file.filename,
            'filename': filename,
            'filepath': filepath,
            'uploaded_at': datetime.now().isoformat(),
            'size': os.path.getsize(filepath),
            'image_info': image_info
        }
        uploaded_files[file_id] = file_info
        
        return jsonify({
            'file_id': file_id,
            'filename': file.filename,
            'size': file_info['size'],
            'dimensions': f"{image_info['width']}x{image_info['height']}",
            'uploaded_at': file_info['uploaded_at']
        })
        
    except RequestEntityTooLarge:
        return jsonify({'error': 'File too large'}), 413
    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route('/api/upload-contests', methods=['POST'])
def upload_contests():
    """Handle contest and candidate data upload"""
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({'error': 'Contest text data is required'}), 400
        
        contest_text = data['text'].strip()
        if not contest_text:
            return jsonify({'error': 'Contest text cannot be empty'}), 400
        
        # Parse the text into structured format
        try:
            parsed_data = parse_contest_text(contest_text)
        except Exception as e:
            return jsonify({'error': f'Failed to parse contest data: {str(e)}'}), 400
        
        # Generate data ID for tracking
        data_id = str(uuid.uuid4())
        
        # Store the data
        contest_data = {
            'data_id': data_id,
            'raw_text': contest_text,
            'parsed_data': parsed_data,
            'uploaded_at': datetime.now().isoformat()
        }
        
        # For now, store in memory (replace with database in production)
        # We'll use a simple approach and store in analysis_jobs with special key
        analysis_jobs[f"contests_{data_id}"] = contest_data
        
        return jsonify({
            'data_id': data_id,
            'contest_count': len(parsed_data['contests']),
            'contests': [c['title'] for c in parsed_data['contests']],
            'uploaded_at': contest_data['uploaded_at']
        })
        
    except Exception as e:
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500

@app.route('/api/validate-contests', methods=['POST'])
def validate_contests():
    """Validate contest text format without saving"""
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({'error': 'Contest text data is required'}), 400
        
        contest_text = data['text'].strip()
        
        # Try to parse the text
        try:
            parsed_data = parse_contest_text(contest_text)
            return jsonify({
                'valid': True,
                'contest_count': len(parsed_data['contests']),
                'preview': parsed_data
            })
        except Exception as e:
            return jsonify({
                'valid': False,
                'error': str(e)
            })
            
    except Exception as e:
        return jsonify({'error': f'Validation failed: {str(e)}'}), 500

@app.route('/api/image/<file_id>')
def get_image(file_id):
    """Serve uploaded image"""
    if file_id not in uploaded_files:
        return jsonify({'error': 'Image not found'}), 404
    
    file_info = uploaded_files[file_id]
    return send_from_directory(app.config['UPLOAD_FOLDER'], file_info['filename'])

@app.route('/api/analyze-ballot', methods=['POST'])
def analyze_ballot():
    """Start ballot analysis using OpenAI GPT-4o with vision"""
    try:
        data = request.get_json()
        
        if not data or 'image_file_id' not in data or 'contest_data_id' not in data:
            return jsonify({'error': 'Both image_file_id and contest_data_id are required'}), 400
        
        image_file_id = data['image_file_id']
        contest_data_id = data['contest_data_id']
        
        # Validate that both files exist
        if image_file_id not in uploaded_files:
            return jsonify({'error': 'Image not found'}), 404
        
        if f"contests_{contest_data_id}" not in analysis_jobs:
            return jsonify({'error': 'Contest data not found'}), 404
        
        # Get image file path
        image_info = uploaded_files[image_file_id]
        image_path = image_info['filepath']
        
        # Create analysis job
        job_id = str(uuid.uuid4())
        
        analysis_job = {
            'job_id': job_id,
            'status': 'queued',
            'image_file_id': image_file_id,
            'contest_data_id': contest_data_id,
            'created_at': datetime.now().isoformat(),
            'progress': 0,
            'message': 'Analysis queued for OpenAI processing...'
        }
        
        analysis_jobs[job_id] = analysis_job
        
        # Start analysis in background thread
        analysis_thread = threading.Thread(
            target=analyze_ballot_with_openai,
            args=(image_path, job_id),
            daemon=True
        )
        analysis_thread.start()
        
        return jsonify({
            'job_id': job_id,
            'status': 'queued',
            'message': 'Analysis job started - processing with OpenAI GPT-4o'
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to start analysis: {str(e)}'}), 500

@app.route('/api/analysis/<job_id>/status')
def get_analysis_status(job_id):
    """Get analysis job status"""
    if job_id not in analysis_jobs:
        return jsonify({'error': 'Analysis job not found'}), 404
    
    job = analysis_jobs[job_id]
    return jsonify({
        'job_id': job_id,
        'status': job['status'],
        'progress': job.get('progress', 0),
        'message': job.get('message', ''),
        'created_at': job['created_at'],
        'has_results': 'results' in job
    })

@app.route('/api/analysis/<job_id>/results')
def get_analysis_results(job_id):
    """Get detailed analysis results"""
    if job_id not in analysis_jobs:
        return jsonify({'error': 'Analysis job not found'}), 404
    
    job = analysis_jobs[job_id]
    
    if job['status'] != 'completed':
        return jsonify({'error': 'Analysis not completed yet'}), 400
    
    if 'results' not in job:
        return jsonify({'error': 'No results available'}), 404
    
    return jsonify({
        'job_id': job_id,
        'status': job['status'],
        'results': job['results'],
        'created_at': job['created_at'],
        'completed_at': job['results'].get('completed_at')
    })

@app.route('/api/analysis/<job_id>/logs')
def get_analysis_logs(job_id):
    """Get OpenAI session logs for a specific job (for debugging)"""
    log_file = os.path.join(OPENAI_SESSIONS_DIR, f"{job_id}.log")
    
    if not os.path.exists(log_file):
        return jsonify({'error': 'No logs found for this job'}), 404
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            log_content = f.read()
        
        # Parse log entries
        log_entries = []
        raw_entries = log_content.split('\n---\n')
        
        for entry in raw_entries:
            entry = entry.strip()
            if entry:
                try:
                    log_entries.append(json.loads(entry))
                except json.JSONDecodeError:
                    # Keep malformed entries as raw text
                    log_entries.append({'raw': entry})
        
        return jsonify({
            'job_id': job_id,
            'log_file': log_file,
            'entry_count': len(log_entries),
            'logs': log_entries
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to read logs: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)