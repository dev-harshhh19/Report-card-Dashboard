from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from database import create_app, init_db, create_tables
from models import db, User, Student, Semester
from werkzeug.security import generate_password_hash, check_password_hash
import re
import time
from functools import wraps
from datetime import datetime, timedelta
import os
# pyrefly: ignore [missing-import]
import google.generativeai as genai
from flask_limiter import Limiter

# Setup Gemini AI
gemini_api_key = os.getenv("GEMINI_API_KEY")
if gemini_api_key:
    genai.configure(api_key=gemini_api_key)
    gemini_model = genai.GenerativeModel('gemini-2.5-flash')
else:
    gemini_model = None

# Initialize Flask app with database
app = create_app()
db_instance, migrate = init_db(app)

# Production security configurations
if os.getenv('FLASK_ENV') == 'production':
    app.config.update(
        SESSION_COOKIE_SECURE=True,  # HTTPS only
        SESSION_COOKIE_HTTPONLY=True,  # Prevent XSS
        SESSION_COOKIE_SAMESITE='Strict',  # CSRF protection
        PERMANENT_SESSION_LIFETIME=timedelta(hours=2),  # Session timeout
    )

# Create tables on first run
with app.app_context():
    create_tables(app, db)

# Security constants
MIN_PASSWORD_LENGTH = 8
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION = 300  # 5 minutes in seconds

# Store failed login attempts (in production, use Redis or database)
failed_attempts = {}

# Security utility functions
def hash_password(password):
    return generate_password_hash(password)

def verify_password(stored_password, provided_password):
    return check_password_hash(stored_password, provided_password)

def validate_password_strength(password):
    """Validate password meets security requirements"""
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    
    return True, "Password is strong"

def sanitize_input(input_string, max_length=100):
    """Sanitize user input to prevent injection attacks"""
    if not input_string:
        return ""
    
    sanitized = re.sub(r'[<>"\';()&+]', '', str(input_string))
    return sanitized[:max_length].strip()

def validate_username(username):
    """Validate username format"""
    if not username:
        return False, "Username is required"
    
    if len(username) < 3:
        return False, "Username must be at least 3 characters long"
    
    if len(username) > 30:
        return False, "Username must be less than 30 characters"
    
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        return False, "Username can only contain letters, numbers, hyphens, and underscores"
    
    return True, "Username is valid"

def check_rate_limit(username):
    """Check if user has exceeded login attempts"""
    current_time = time.time()
    
    if username in failed_attempts:
        attempts, last_attempt = failed_attempts[username]
        
        if current_time - last_attempt > LOCKOUT_DURATION:
            del failed_attempts[username]
            return True, "Rate limit reset"
        
        if attempts >= MAX_LOGIN_ATTEMPTS:
            remaining_time = int(LOCKOUT_DURATION - (current_time - last_attempt))
            return False, f"Too many failed attempts. Try again in {remaining_time} seconds"
    
    return True, "Rate limit OK"

def record_failed_attempt(username):
    """Record a failed login attempt"""
    current_time = time.time()
    if username in failed_attempts:
        attempts, _ = failed_attempts[username]
        failed_attempts[username] = (attempts + 1, current_time)
    else:
        failed_attempts[username] = (1, current_time)

def clear_failed_attempts(username):
    """Clear failed attempts for successful login"""
    if username in failed_attempts:
        del failed_attempts[username]

def require_login(f):
    """Decorator to require login for protected routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def get_client_ip():
    """Get client IP address for logging"""
    if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
        return request.environ.get('REMOTE_ADDR', 'Unknown')
    else:
        return request.environ.get('HTTP_X_FORWARDED_FOR')

def log_security_event(event_type, username=None, details=None):
    """Log security events (in production, use proper logging)"""
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    ip = get_client_ip()
    log_entry = {
        'timestamp': timestamp,
        'event': event_type,
        'username': username,
        'ip': ip,
        'details': details
    }
    print(f"SECURITY LOG: {log_entry}")

@app.route('/', methods=['GET'])
def index():
    # If user is already logged in based on session, we can render normal template
    # JS will fetch dashboard
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    # Get and sanitize inputs
    username = sanitize_input(request.form.get('username'), 30)
    password = request.form.get('password')
    
    # Validate inputs
    if not username or not password:
        log_security_event('LOGIN_FAILED', username, 'Missing credentials')
        return jsonify({'error': 'Username and password required.'}), 400
    
    # Validate username format
    username_valid, username_msg = validate_username(username)
    if not username_valid:
        log_security_event('LOGIN_FAILED', username, f'Invalid username: {username_msg}')
        return jsonify({'error': username_msg}), 400
    
    # Check rate limiting
    rate_limit_ok, rate_msg = check_rate_limit(username)
    if not rate_limit_ok:
        log_security_event('RATE_LIMITED', username, rate_msg)
        return jsonify({'error': rate_msg}), 429

    # Check if user exists
    user = User.query.filter_by(username=username).first()
    
    if user:
        # Existing user: verify password
        if not verify_password(user.password, password):
            record_failed_attempt(username)
            log_security_event('LOGIN_FAILED', username, 'Invalid password')
            return jsonify({'error': 'Invalid username or password.'}), 401
        
        # Clear failed attempts on successful login
        clear_failed_attempts(username)
    else:
        # New user registration: validate password strength
        password_valid, password_msg = validate_password_strength(password)
        if not password_valid:
            log_security_event('REGISTRATION_FAILED', username, f'Weak password: {password_msg}')
            return jsonify({'error': f'Password requirements not met: {password_msg}'}), 400
        
        # Hash password for new user
        hashed_password = hash_password(password)
        
        # Create user and student
        user = User(username=username, password=hashed_password)
        db.session.add(user)
        db.session.flush()
        
        student = Student(user_id=user.id, current_semester=0)
        db.session.add(student)
        db.session.commit()
        log_security_event('USER_REGISTERED', username, 'New user registered')
    
    # Set secure session
    session['username'] = username
    session['login_time'] = datetime.now().isoformat()
    session.permanent = True
    
    log_security_event('LOGIN_SUCCESS', username, 'Logged in')
    return ('', 204)

@app.route('/add_semester', methods=['POST'])
@require_login
def add_semester():
    username = session.get('username')
    user = User.query.filter_by(username=username).first()
    if not user or not user.student:
        return jsonify({'error': 'Student data not found'}), 404
        
    data = request.get_json()
    semester_num = data.get('semester_number')
    subjects = data.get('subjects')
    marks = data.get('marks')
    
    if not semester_num or not subjects or not marks or len(subjects) != len(marks):
        return jsonify({'error': 'Invalid data provided'}), 400
        
    try:
        semester_num = int(semester_num)
        marks = [int(m) for m in marks]
    except ValueError:
        return jsonify({'error': 'Marks and semester must be numbers'}), 400
        
    # Check if semester already exists
    existing = Semester.query.filter_by(student_id=user.student.id, semester_number=semester_num).first()
    if existing:
        return jsonify({'error': f'Semester {semester_num} already exists'}), 400
        
    semester = Semester(student_id=user.student.id, semester_number=semester_num)
    semester.set_subjects(subjects)
    semester.set_marks(marks)
    
    # Update student's current semester if this is higher
    if user.student.current_semester < semester_num:
        user.student.current_semester = semester_num
        
    db.session.add(semester)
    db.session.commit()
    
    log_security_event('SEMESTER_ADDED', username, f'Added semester {semester_num}')
    return jsonify({'success': True}), 200

@app.route('/dashboard', methods=['GET'])
@require_login
def dashboard():
    username = session.get('username')
    username = sanitize_input(username, 30)  # Extra safety
    
    # Get user and student data
    user = User.query.filter_by(username=username).first()
    if not user or not user.student:
        log_security_event('DASHBOARD_ERROR', username, 'Student data not found')
        return jsonify({'error': 'Student data not found'}), 404
    
    student = user.student
    semesters = student.get_all_semesters()
    
    if not semesters:
        # Return empty dashboard payload instead of 404 so UI can show "Add your first semester"
        return jsonify({
            'username': username,
            'current_semester': student.current_semester,
            'semesters': [],
            'marks': [],
            'sgpa': 0,
            'growth': []
        })
    
    # Get latest semester data
    latest_semester = semesters[-1]
    
    # Prepare response data
    student_data = {
        'username': username,
        'current_semester': student.current_semester,
        'semesters': [sem.to_dict() for sem in semesters],
        'marks': latest_semester.get_marks(),
        'sgpa': latest_semester.sgpa,
        'growth': student.get_sgpa_growth()
    }
    
    log_security_event('DASHBOARD_ACCESS', username, f'Accessed dashboard with {len(semesters)} semesters')
    
    if request.args.get('json') == '1':
        return jsonify(student_data)
    return render_template('dashboard.html', student=student_data)

@app.route('/chat', methods=['POST'])
def chat():
    if not gemini_model:
        return jsonify({"error": "Chat is currently disabled. Missing API key."}), 503

    user_message = request.json.get('message')
    if not user_message:
        return jsonify({"error": "Message is required."}), 400

    system_instruction = (
        "You are an AI assistant exclusively designed for the Academic Survival Planner portfolio project created by Harshad Nikam. "
        "Your sole purpose is to answer questions related to this specific application, its features, how to use it, and its architecture. "
        "If a user asks about anything unrelated to this specific app (like coding help, general knowledge, math, etc.), you MUST politely decline and remind them of your limitation to only discuss the Academic Survival Planner."
    )

    try:
        response = gemini_model.generate_content(
            system_instruction + "\nUser question: " + user_message
        )
        return jsonify({"response": response.text})
    except Exception as e:
        app.logger.error(f"Gemini API error: {e}")
        return jsonify({"error": "The assistant is currently unavailable."}), 500

@app.route('/logout', methods=['POST'])
@require_login
def logout():
    username = session.get('username')
    session.clear()
    log_security_event('LOGOUT', username, 'User logged out')
    return ('', 204)

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Page not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    log_security_event('SERVER_ERROR', None, f'Internal server error: {str(error)}')
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(429)
def rate_limit_error(error):
    return jsonify({'error': 'Too many requests. Please try again later.'}), 429

# Security headers middleware
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; img-src 'self' data: https:; font-src 'self' https://cdn.jsdelivr.net"
    return response

if __name__ == '__main__':
    debug_mode = os.getenv('FLASK_ENV') != 'production'
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
