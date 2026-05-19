import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Database configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your_secret_key_change_this_in_production')
    
    # Use SQLite directly as requested
    database_url = 'sqlite:///report_card_demo.db'
    print("Using SQLite database (report_card_demo.db)")
    
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