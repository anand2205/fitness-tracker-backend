from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    # NEW FIELD
    role = db.Column(db.String(20), default="client")  # trainer / client

class Workout(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    calories = db.Column(db.Integer, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
