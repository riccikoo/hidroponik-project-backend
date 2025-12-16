from flask import jsonify, request
from extensions import db, bcrypt
from models.user_model import User
from models.sensor_model import Sensor
from models.message_model import Message
from datetime import datetime
from validations.user_schema import validate_register, validate_login
from flask_jwt_extended import create_access_token


# =========================
# REGISTER
# =========================
def register():
    errors = validate_register(request.json)
    if errors:
        return jsonify({"status": False, "errors": errors}), 422

    data = request.json
    hashed_pw = bcrypt.generate_password_hash(data['password']).decode('utf-8')

    now = datetime.utcnow()

    user = User(
        name=data['name'],
        email=data['email'],
        password=hashed_pw,
        role='user',
        status='inactive',
        create_at=now,
        update_at=now
    )

    db.session.add(user)
    db.session.commit()

    return jsonify({
        "status": True,
        "message": "User registered successfully, wait for admin approval",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "status": user.status,
            "create_at": user.create_at.isoformat(),
            "update_at": user.update_at.isoformat()
        }
    }), 201


# =========================
# LOGIN
# =========================
def login():
    errors = validate_login(request.json)
    if errors:
        return jsonify({"status": False, "errors": errors}), 422

    data = request.json
    user = User.query.filter_by(email=data['email']).first()

    if not user:
        return jsonify({"status": False, "message": "Invalid credentials"}), 401

    if user.status != 'active':
        return jsonify({
            "status": False,
            "message": "Account is inactive. Please contact admin."
        }), 403

    if not bcrypt.check_password_hash(user.password, data['password']):
        return jsonify({"status": False, "message": "Invalid credentials"}), 401

    # update last activity
    user.update_at = datetime.utcnow()
    db.session.commit()

    access_token = create_access_token(identity=user.id)

    return jsonify({
        "status": True,
        "message": "Login successful",
        "token": access_token,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "status": user.status,
            "create_at": user.create_at.isoformat(),
            "update_at": user.update_at.isoformat()
        }
    }), 200


# =========================
# SENSOR DATA
# =========================
def get_sensor_data():
    sensor_name = request.args.get('name')
    limit = request.args.get('limit', 50, type=int)

    query = Sensor.query
    if sensor_name:
        query = query.filter_by(sensor_name=sensor_name)

    data = query.order_by(Sensor.timestamp.desc()).limit(limit).all()

    return jsonify({
        "status": True,
        "sensor": sensor_name,
        "data_count": len(data),
        "data": [
            {
                "id": row.id,
                "sensor_name": row.sensor_name,
                "value": float(row.value),
                "timestamp": row.timestamp.isoformat()
            } for row in reversed(data)
        ]
    }), 200


# =========================
# ADMIN UPDATE USER STATUS
# =========================
def admin_update_user_status(user_id):
    data = request.get_json()
    new_status = data.get("status")

    if new_status not in ["active", "inactive"]:
        return jsonify({"error": "Invalid status"}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    user.status = new_status
    user.update_at = datetime.utcnow()
    db.session.commit()

    return jsonify({
        "status": True,
        "message": f"User {user.name} status updated to {new_status}"
    }), 200


# =========================
# USER GET MESSAGE
# =========================
def user_get_messages():
    user_id = request.headers.get("X-User-ID")
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    msgs = Message.query.filter_by(user_id=user_id)\
        .order_by(Message.timestamp.desc()).all()

    return jsonify({
        "messages": [
            {
                "id": m.id,
                "message": m.message,
                "timestamp": m.timestamp.isoformat()
            } for m in msgs
        ]
    }), 200


# =========================
# ADMIN SEND MESSAGE
# =========================
def admin_send_message(user_id):
    data = request.get_json()
    msg = data.get("message")

    if not msg:
        return jsonify({"error": "Message cannot be empty"}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    message = Message(
        user_id=user.id,
        message=msg,
        timestamp=datetime.utcnow()
    )

    db.session.add(message)
    db.session.commit()

    return jsonify({
        "status": True,
        "message": "Message sent to user"
    }), 201
