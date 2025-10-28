from flask import jsonify, request
from extensions import db, bcrypt
from models.user_model import User
from datetime import datetime
from validations.user_schema import validate_register, validate_login
from flask_jwt_extended import create_access_token

def register():
    errors = validate_register(request.json)
    if errors:
        return jsonify({"status": False, "errors": errors}), 422

    data = request.json
    hashed_pw = bcrypt.generate_password_hash(data['password']).decode('utf-8')

    user = User(
        name=data['name'],
        email=data['email'],
        password=hashed_pw,
        role='user',              # default role user
        status='inactive',          # default status active
        timestamp=datetime.utcnow()  # waktu pembuatan akun
    )

    db.session.add(user)
    db.session.commit()

    return jsonify({
        "status": True,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "status": user.status,
            "timestamp": user.timestamp.isoformat()
        },
        "message": "User registered successfully wait for admin applying"
    }), 201


def login():
    # 1. Validate incoming data (assuming validate_login handles this)
    errors = validate_login(request.json)
    if errors:
        return jsonify({"status": False, "errors": errors}), 422

    data = request.json
    user = User.query.filter_by(email=data['email']).first()

    # --- 1. Email Check ---
    if not user:
        # It's better security practice to give a generic failure message
        # to avoid letting attackers guess valid emails.
        return jsonify({"status": False, "message": "Invalid credentials"}), 401

    # --- 2. Status Check (THE NEW REQUIREMENT) ---
    if user.status != 'active':
        # Block login if status is 'inactive'
        return jsonify({"status": False, "message": "Account is currently inactive. Please contact support."}), 403 # Use 403 Forbidden

    # --- 3. Password Check ---
    if not bcrypt.check_password_hash(user.password, data['password']):
        return jsonify({"status": False, "message": "Invalid credentials"}), 401

    # --- SUCCESS ---
    # Generate token only if all checks pass
    access_token = create_access_token(identity=user.id)
    return jsonify({
        "status": True,
        "message": "Login successful",
        # 🔑 CRITICAL: Make sure 'token' is present and holds the access_token value
        "token": access_token, 
        "user": {
            "id": user.id, 
            "name": user.name, 
            "email": user.email,
            "role": user.role, 
            "status": user.status,
            # Ensure timestamp is serialized
            "timestamp": user.timestamp if isinstance(user.timestamp, str) else (user.timestamp.isoformat() if user.timestamp else None)
        }
    }), 200