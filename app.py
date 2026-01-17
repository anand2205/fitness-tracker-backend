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

app = Flask(__name__)
app.config.from_object(Config)

# JWT config
app.config["JWT_SECRET_KEY"] = "super-secret-key"
jwt = JWTManager(app)

# Initialize DB
db.init_app(app)


@app.route("/")
def index():
    return jsonify({"app": "fitness_tracker", "status": "running"})


# =========================
# REGISTER
# =========================
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    if not all(k in data for k in ("name", "email", "password", "role")):
        return jsonify({"message": "name, email, password, role required"}), 400

    if data["role"] not in ["trainer", "client"]:
        return jsonify({"message": "role must be trainer or client"}), 400

    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"message": "User already exists"}), 400

    user = User(
        name=data["name"],
        email=data["email"],
        password=generate_password_hash(data["password"]),
        role=data["role"]
    )

    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"}), 201


# =========================
# LOGIN
# =========================
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    user = User.query.filter_by(email=data.get("email")).first()

    if not user or not check_password_hash(user.password, data.get("password")):
        return jsonify({"message": "Invalid credentials"}), 401

    token = create_access_token(identity=str(user.id))

    return jsonify({
        "message": "Login successful",
        "access_token": token,
        "role": user.role
    }), 200


# =========================
# TRAINER → ASSIGN WORKOUT
# =========================
@app.route("/workouts", methods=["POST"])
@jwt_required()
def add_workout():
    trainer_id = int(get_jwt_identity())
    trainer = User.query.get(trainer_id)

    if trainer.role != "trainer":
        return jsonify({"message": "Only trainers can create workouts"}), 403

    data = request.get_json()

    if not all(k in data for k in ("title", "duration", "calories", "client_id")):
        return jsonify({"message": "Missing workout data"}), 400

    client = User.query.get(data["client_id"])

    if not client or client.role != "client":
        return jsonify({"message": "Invalid client"}), 400

    workout = Workout(
        title=data["title"],
        duration=data["duration"],
        calories=data["calories"],
        user_id=data["client_id"]
    )

    db.session.add(workout)
    db.session.commit()

    return jsonify({"message": "Workout assigned to client"}), 201


# =========================
# CLIENT → VIEW WORKOUTS
# =========================
@app.route("/workouts", methods=["GET"])
@jwt_required()
def get_workouts():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    if user.role != "client":
        return jsonify({"message": "Only clients can view workouts"}), 403

    workouts = Workout.query.filter_by(user_id=user_id).all()

    return jsonify([
        {
            "id": w.id,
            "title": w.title,
            "duration": w.duration,
            "calories": w.calories
        } for w in workouts
    ])


# =========================
# START SERVER
# =========================
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run()
