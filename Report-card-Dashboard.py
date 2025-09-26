from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from database import create_app, init_db, create_tables
from models import db, User, Student, Semester
import random
import hashlib
import secrets
import re
import time
from functools import wraps
from datetime import datetime, timedelta
import os

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

# Constants
SEMESTER_MONTHS = 6
MAX_SEMESTERS = 8
CS_SUBJECTS = ['CS101', 'CS102', 'CS103', 'CS104', 'CS105']

# Security constants
MIN_PASSWORD_LENGTH = 8
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION = 300  # 5 minutes in seconds

# Store failed login attempts (in production, use Redis or database)
failed_attempts = {}

# Security utility functions
def hash_password(password):
    """Hash password using SHA-256 with salt"""
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}:{pwd_hash}"

def verify_password(stored_password, provided_password):
    """Verify password against stored hash"""
    try:
        salt, stored_hash = stored_password.split(':')
        pwd_hash = hashlib.sha256((provided_password + salt).encode()).hexdigest()
        return pwd_hash == stored_hash
    except ValueError:
        # Handle legacy plain text passwords (migration case)
        return stored_password == provided_password

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
    
    # Remove potentially harmful characters
    sanitized = re.sub(r'[<>"\';()&+]', '', str(input_string))
    
    # Limit length
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
        
        # Reset attempts if lockout period has passed
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

def validate_semester(semester_str):
    """Validate semester input"""
    try:
        semester = int(semester_str)
        if 1 <= semester <= 8:
            return True, semester
        else:
            return False, "Semester must be between 1 and 8"
    except (ValueError, TypeError):
        return False, "Invalid semester format"

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
        return request.environ['REMOTE_ADDR']
    else:
        return request.environ['HTTP_X_FORWARDED_FOR']

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
    
    # In production, write to secure log file or monitoring system
    print(f"SECURITY LOG: {log_entry}")

def create_new_semester_data(semester_number):
    """Create new semester data"""
    marks = [random.randint(50, 100) for _ in range(5)]
    subjects = random.sample(CS_SUBJECTS, 5)
    return subjects, marks

def create_historical_semesters(student_id, current_semester):
    """Create historical semester data for a student based on their current semester"""
    semesters = []
    
    for sem_num in range(1, current_semester + 1):
        subjects, marks = create_new_semester_data(sem_num)
        semester = Semester(student_id=student_id, semester_number=sem_num)
        semester.set_subjects(subjects)
        semester.set_marks(marks)
        
        # Set creation date to simulate past semesters (6 months apart)
        if sem_num < current_semester:
            months_ago = (current_semester - sem_num) * 6
            semester.created_at = datetime.now() - timedelta(days=months_ago * 30)
        
        semesters.append(semester)
    
    return semesters

def get_or_create_student(username):
    """Get existing student or create new one"""
    user = User.query.filter_by(username=username).first()
    if user and user.student:
        return user.student
    elif user:
        # User exists but no student record
        student = Student(user_id=user.id)
        db.session.add(student)
        db.session.commit()
        return student
    return None

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    # Get and sanitize inputs
    username = sanitize_input(request.form.get('username'), 30)
    password = request.form.get('password')  # Don't sanitize password
    current_semester = sanitize_input(request.form.get('current_semester'), 2)
    
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
    
    # Validate semester input
    semester_valid, semester_result = validate_semester(current_semester)
    if not semester_valid:
        log_security_event('LOGIN_FAILED', username, f'Invalid semester: {semester_result}')
        return jsonify({'error': semester_result}), 400
    
    current_semester = int(semester_result)  # Ensure it's an integer

    # Check if user exists
    user = User.query.filter_by(username=username).first()
    now = datetime.now()
    
    if user:
        # Existing user: verify password
        if not verify_password(user.password, password):
            record_failed_attempt(username)
            log_security_event('LOGIN_FAILED', username, 'Invalid password')
            return jsonify({'error': 'Invalid username or password.'}), 401
        
        # Clear failed attempts on successful login
        clear_failed_attempts(username)
        
        # Get or create student record
        student = user.student
        if not student:
            student = Student(user_id=user.id, current_semester=current_semester)
            db.session.add(student)
            db.session.flush()
            
            # Create historical semesters based on current semester
            historical_semesters = create_historical_semesters(student.id, current_semester)
            for semester in historical_semesters:
                db.session.add(semester)
        else:
            # Update current semester if different
            if student.current_semester != current_semester:
                student.current_semester = current_semester
                
                # Check if we need to add more semesters
                existing_count = student.semesters.count()
                if current_semester > existing_count:
                    for sem_num in range(existing_count + 1, current_semester + 1):
                        subjects, marks = create_new_semester_data(sem_num)
                        new_semester = Semester(student_id=student.id, semester_number=sem_num)
                        new_semester.set_subjects(subjects)
                        new_semester.set_marks(marks)
                        
                        # Set creation date for past semesters
                        if sem_num < current_semester:
                            months_ago = (current_semester - sem_num) * 6
                            new_semester.created_at = datetime.now() - timedelta(days=months_ago * 30)
                        
                        db.session.add(new_semester)
        
        db.session.commit()
        
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
        
        student = Student(user_id=user.id, current_semester=current_semester)
        db.session.add(student)
        db.session.flush()
        
        # Create historical semesters
        historical_semesters = create_historical_semesters(student.id, current_semester)
        for semester in historical_semesters:
            db.session.add(semester)
        
        db.session.commit()
        log_security_event('USER_REGISTERED', username, f'New user registered with semester {current_semester}')
    
    # Set secure session
    session['username'] = username
    session['login_time'] = datetime.now().isoformat()
    session.permanent = True
    
    log_security_event('LOGIN_SUCCESS', username, f'Logged in with semester {current_semester}')
    return ('', 204)

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
        log_security_event('DASHBOARD_ERROR', username, 'No semester data found')
        return jsonify({'error': 'No semester data found'}), 404
    
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
    # Production should never use debug=True
    debug_mode = os.getenv('FLASK_ENV') != 'production'
    port = int(os.getenv('PORT', 5000))
    
    if debug_mode:
        print("\n🔒 SECURITY FEATURES ENABLED:")
        print("✅ Password hashing with SHA-256 + salt")
        print("✅ Input sanitization and validation")
        print("✅ Rate limiting (5 attempts, 5-min lockout)")
        print("✅ Secure session management")
        print("✅ Security headers (CSP, HSTS, XSS protection)")
        print("✅ Comprehensive logging")
        print("\n🚀 Application starting with security enhancements...\n")
    
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
