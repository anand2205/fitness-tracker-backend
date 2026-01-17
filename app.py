from flask import Flask, request, jsonify
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity
)
from werkzeug.security import generate_password_hash, check_password_hash

from config import Config
from models import db, User, Workout

# ---------------- APP SETUP ----------------
app = Flask(__name__)
app.config.from_object(Config)

# JWT
app.config["JWT_SECRET_KEY"] = "super-secret-key"
jwt = JWTManager(app)

# Database
db.init_app(app)

# ---------------- HEALTH CHECK ----------------
@app.route("/")
def index():
    return jsonify({
        "app": "fitness_tracker",
        "status": "running"
    })


# ---------------- REGISTER ----------------
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role", "client")  # trainer / client

    if not name or not email or not password:
        return jsonify({"message": "name, email, password required"}), 400

    if role not in ["trainer", "client"]:
        return jsonify({"message": "Invalid role"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"message": "User already exists"}), 400

    user = User(
        name=name,
        email=email,
        password=generate_password_hash(password),
        role=role
    )

    db.session.add(user)
    db.session.commit()

    return jsonify({
        "message": "User registered successfully",
        "role": role
    }), 201


# ---------------- LOGIN ----------------
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    if not data:
        return jsonify({"message": "Email and password required"}), 400

    user = User.query.filter_by(email=data.get("email")).first()

    if not user or not check_password_hash(user.password, data.get("password")):
        return jsonify({"message": "Invalid credentials"}), 401

    access_token = create_access_token(identity=str(user.id))

    return jsonify({
        "message": "Login successful",
        "access_token": access_token,
        "role": user.role
    }), 200


# ---------------- ADD WORKOUT ----------------
@app.route("/workouts", methods=["POST"])
@jwt_required()
def add_workout():
    user_id = int(get_jwt_identity())
    data = request.get_json()

    if not data or not all(k in data for k in ("title", "duration", "calories")):
        return jsonify({"message": "title, duration, calories required"}), 400

    workout = Workout(
        title=data["title"],
        duration=data["duration"],
        calories=data["calories"],
        user_id=user_id
    )

    db.session.add(workout)
    db.session.commit()

    return jsonify({
        "message": "Workout saved",
        "workout": {
            "id": workout.id,
            "title": workout.title,
            "duration": workout.duration,
            "calories": workout.calories
        }
    }), 201


# ---------------- GET WORKOUTS ----------------
@app.route("/workouts", methods=["GET"])
@jwt_required()
def get_workouts():
    user_id = int(get_jwt_identity())
    workouts = Workout.query.filter_by(user_id=user_id).all()

    return jsonify([
        {
            "id": w.id,
            "title": w.title,
            "duration": w.duration,
            "calories": w.calories
        }
        for w in workouts
    ]), 200


# ---------------- UPDATE WORKOUT ----------------
@app.route("/workouts/<int:workout_id>", methods=["PUT"])
@jwt_required()
def update_workout(workout_id):
    user_id = int(get_jwt_identity())
    data = request.get_json()

    workout = Workout.query.filter_by(
        id=workout_id,
        user_id=user_id
    ).first()

    if not workout:
        return jsonify({"message": "Workout not found"}), 404

    workout.title = data.get("title", workout.title)
    workout.duration = data.get("duration", workout.duration)
    workout.calories = data.get("calories", workout.calories)

    db.session.commit()

    return jsonify({"message": "Workout updated successfully"}), 200


# ---------------- DELETE WORKOUT ----------------
@app.route("/workouts/<int:workout_id>", methods=["DELETE"])
@jwt_required()
def delete_workout(workout_id):
    user_id = int(get_jwt_identity())

    workout = Workout.query.filter_by(
        id=workout_id,
        user_id=user_id
    ).first()

    if not workout:
        return jsonify({"message": "Workout not found"}), 404

    db.session.delete(workout)
    db.session.commit()

    return jsonify({"message": "Workout deleted successfully"}), 200


# ---------------- START SERVER ----------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run()
