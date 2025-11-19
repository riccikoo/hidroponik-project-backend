from flask import jsonify, request
from extensions import db, bcrypt
from models.user_model import User
from models.sensor_model import Sensor
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
        role='user',       
        status='inactive',        
        timestamp=datetime.utcnow()
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
    errors = validate_login(request.json)
    if errors:
        return jsonify({"status": False, "errors": errors}), 422

    data = request.json
    user = User.query.filter_by(email=data['email']).first()

    if not user:
        return jsonify({"status": False, "message": "Invalid credentials"}), 401

    if user.status != 'active':
        return jsonify({"status": False, "message": "Account is currently inactive. Please contact support."}), 403 # Use 403 Forbidden

    if not bcrypt.check_password_hash(user.password, data['password']):
        return jsonify({"status": False, "message": "Invalid credentials"}), 401

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
            # Ensure timestamp is serialized
            "timestamp": user.timestamp if isinstance(user.timestamp, str) else (user.timestamp.isoformat() if user.timestamp else None)
        }
    }), 200

def get_sensor_data():
    sensor_name = request.args.get('name', None)
    limit = request.args.get('limit', 50, type=int)

    query = Sensor.query

    if sensor_name:
        query = query.filter_by(sensor_name=sensor_name)

    data = query.order_by(Sensor.timestamp.desc()).limit(limit).all()

    result = []
    for row in data:
        result.append({
            "id": row.id,
            "sensor_name": row.sensor_name,
            "value": float(row.value),
            "timestamp": row.timestamp.isoformat()
        })

    return jsonify({
        "status": True,
        "sensor": sensor_name,
        "data_count": len(result),
        "data": result[::-1]
    }), 200
