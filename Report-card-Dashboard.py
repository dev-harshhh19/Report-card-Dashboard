from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import json
import os
import random
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for session
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False

DATA_FILE = 'data.json'
SEMESTER_MONTHS = 6
MAX_SEMESTERS = 8
CS_SUBJECTS = ['CS101', 'CS102', 'CS103', 'CS104', 'CS105']

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def new_semester_result():
    marks = [random.randint(50, 100) for _ in range(5)]
    subjects = random.sample(CS_SUBJECTS, 5)
    sgpa = round(sum(marks) / len(marks) / 10, 2)
    total = sum(marks)
    return {
        'subjects': subjects,
        'marks': marks,
        'sgpa': sgpa,
        'total': total,
        'timestamp': datetime.now().isoformat()
    }

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    print(f"LOGIN ATTEMPT: username={username}, password={password}")
    if not username or not password:
        print("LOGIN ERROR: Missing username or password")
        return jsonify({'error': 'Username and password required.'}), 400

    data = load_data()
    if 'users' not in data:
        data['users'] = []
    if 'students' not in data:
        data['students'] = {}

    # Check if user exists
    user_record = next((user for user in data['users'] if user['username'] == username), None)

    now = datetime.now()
    if user_record:
        # Existing user: verify password
        if user_record['password'] != password:
            print(f"LOGIN ERROR: Invalid password for user '{username}'")
            return jsonify({'error': 'Invalid username or password.'}), 401

        # MIGRATION and semester update logic for existing user
        student_rec = data['students'][username]
        if 'semesters' not in student_rec: # Fallback for old data
            marks = student_rec.get('marks', [random.randint(50, 100) for _ in range(5)])
            subjects = random.sample(CS_SUBJECTS, 5)
            sgpa = student_rec.get('sgpa', round(sum(marks) / 5 / 10, 2))
            total = sum(marks)
            semesters = [{'subjects': subjects, 'marks': marks, 'sgpa': sgpa, 'total': total, 'timestamp': now.isoformat()}]
        else:
            semesters = student_rec['semesters']
            for sem in semesters: # Migration for older semesters
                if 'subjects' not in sem or not isinstance(sem['subjects'], list):
                    sem['subjects'] = random.sample(CS_SUBJECTS, 5)
                if 'total' not in sem:
                    sem['total'] = sum(sem.get('marks', [0,0,0,0,0]))

        # Check if a new semester should be added
        last_sem = semesters[-1]
        last_date = datetime.fromisoformat(last_sem['timestamp'])
        while len(semesters) < MAX_SEMESTERS and (now - last_date).days >= SEMESTER_MONTHS * 30:
            semesters.append(new_semester_result())
            last_date = datetime.fromisoformat(semesters[-1]['timestamp'])

        data['students'][username]['semesters'] = semesters

    else:
        # New user: create user and first semester
        data['users'].append({'username': username, 'password': password})
        semesters = [new_semester_result()]
        data['students'][username] = { 'semesters': semesters }

    save_data(data)
    session['username'] = username
    print(f"LOGIN SUCCESS: session={dict(session)}")
    return ('', 204)

@app.route('/dashboard', methods=['GET'])
def dashboard():
    print(f"DASHBOARD: session={dict(session)}")
    username = session.get('username')
    if not username:
        print("DASHBOARD ERROR: Not logged in")
        if request.args.get('json') == '1':
            return jsonify({'error': 'Not logged in'}), 401
        return redirect(url_for('index'))
    data = load_data()
    student = data['students'].get(username)
    semesters = student['semesters']
    marks = [s['marks'] for s in semesters]
    sgpas = [s['sgpa'] for s in semesters]
    latest = semesters[-1]
    student_data = {
        'username': username,
        'semesters': semesters,
        'marks': latest['marks'],
        'sgpa': latest['sgpa'],
        'growth': sgpas
    }
    print(f"DASHBOARD SUCCESS: user={username}, semesters={len(semesters)}")
    if request.args.get('json') == '1':
        return jsonify(student_data)
    return render_template('dashboard.html', student=student_data)

@app.route('/logout', methods=['POST'])
def logout():
    print(f"LOGOUT: session before clear={dict(session)}")
    session.clear()
    print("LOGOUT: session cleared")
    return ('', 204)

if __name__ == '__main__':
    app.run(debug=True)
