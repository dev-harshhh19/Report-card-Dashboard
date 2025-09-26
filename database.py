import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Database configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your_secret_key_change_this_in_production')
    
    # Use SQLite for demo/testing if PostgreSQL URL not available
    database_url = os.getenv('DATABASE_URL')
    if not database_url or 'postgresql' in database_url:
        # Fallback to SQLite for demo
        database_url = 'sqlite:///report_card_demo.db'
        print("Using SQLite database for demo (report_card_demo.db)")
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_SECURE'] = False
    
    return app

def init_db(app):
    """Initialize database with the app"""
    from models import db
    
    db.init_app(app)
    migrate = Migrate(app, db)
    
    return db, migrate

def create_tables(app, db):
    """Create all database tables"""
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")

def get_db_connection_info():
    """Get database connection information for debugging"""
    db_url = os.getenv('DATABASE_URL')
    if db_url:
        # Hide password for security
        if '@' in db_url and '://' in db_url:
            protocol, rest = db_url.split('://', 1)
            if '@' in rest:
                credentials, host_part = rest.split('@', 1)
                username = credentials.split(':')[0]
                return f"{protocol}://{username}:***@{host_part}"
    return "No database URL configured"