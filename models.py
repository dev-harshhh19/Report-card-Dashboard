from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc, asc
from datetime import datetime
import json

db = SQLAlchemy()

class User(db.Model):
    """User model for authentication"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with student data
    student = db.relationship('Student', backref='user', uselist=False, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.username}>'

class Student(db.Model):
    """Student model for storing academic data"""
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    current_semester = db.Column(db.Integer, nullable=False, default=1)  # Current semester (1-8)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with semesters
    semesters = db.relationship('Semester', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    
    def get_latest_semester(self):
        """Get the most recent semester"""
        return Semester.query.filter_by(student_id=self.id).order_by(desc(Semester.created_at)).first()
    
    def get_all_semesters(self):
        """Get all semesters ordered by creation date"""
        return Semester.query.filter_by(student_id=self.id).order_by(asc(Semester.created_at)).all()
    
    def get_sgpa_growth(self):
        """Get SGPA values for all semesters"""
        return [sem.sgpa for sem in self.get_all_semesters()]
    
    def __repr__(self):
        return f'<Student {self.user.username}>'

class Semester(db.Model):
    """Semester model for storing semester-wise academic data"""
    __tablename__ = 'semesters'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    semester_number = db.Column(db.Integer, nullable=False)
    subjects = db.Column(db.Text, nullable=False)  # JSON string of subjects list
    marks = db.Column(db.Text, nullable=False)     # JSON string of marks list
    sgpa = db.Column(db.Float, nullable=False)
    total_marks = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_subjects(self):
        """Get subjects as a list"""
        return json.loads(self.subjects)
    
    def set_subjects(self, subjects_list):
        """Set subjects from a list"""
        self.subjects = json.dumps(subjects_list)
    
    def get_marks(self):
        """Get marks as a list"""
        return json.loads(self.marks)
    
    def set_marks(self, marks_list):
        """Set marks from a list"""
        self.marks = json.dumps(marks_list)
        self.total_marks = sum(marks_list)
        self.sgpa = round(sum(marks_list) / len(marks_list) / 10, 2)
    
    def to_dict(self):
        """Convert semester to dictionary (similar to JSON format)"""
        return {
            'subjects': self.get_subjects(),
            'marks': self.get_marks(),
            'sgpa': self.sgpa,
            'total': self.total_marks,
            'timestamp': self.created_at.isoformat()
        }
    
    def __repr__(self):
        return f'<Semester {self.semester_number} for Student {self.student_id}>'