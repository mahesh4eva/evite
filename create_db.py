from app import app, db
from app import User, Invitation, Guest  # Import all your models

with app.app_context():
    db.drop_all()  # This will drop all existing tables
    db.create_all()  # This will create all tables
    print("Database tables created successfully!")