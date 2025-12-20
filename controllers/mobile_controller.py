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


# =========================from flask import jsonify, request
from extensions import db, bcrypt
from models.user_model import User
from models.sensor_model import Sensor
from models.message_model import Message
from datetime import datetime
from validations.user_schema import validate_register, validate_login
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity


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
# USER GET MESSAGES (FIXED VERSION)
# =========================
@jwt_required()
def user_get_messages():
    """
    Get messages for the logged-in user using JWT token
    """
    try:
        # Get user ID from JWT token
        current_user_id = get_jwt_identity()
        
        print(f"📱 User {current_user_id} requesting messages")
        
        # Get user from database
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({
                "success": False,
                "message": "User not found"
            }), 404
        
        # Get messages where user is sender (messages sent to admin)
        sent_messages = Message.query.filter_by(
            sender_id=user.id
        ).order_by(Message.timestamp.desc()).all()
        
        # Get messages where user is receiver (replies from admin)
        received_messages = Message.query.filter_by(
            receiver_id=user.id
        ).order_by(Message.timestamp.desc()).all()
        
        # Combine all messages
        all_messages = sent_messages + received_messages
        all_messages.sort(key=lambda x: x.timestamp, reverse=True)
        
        result = []
        for msg in all_messages:
            # Get sender info
            sender = User.query.get(msg.sender_id)
            receiver = User.query.get(msg.receiver_id)
            
            message_data = {
                "id": msg.id,
                "sender_id": msg.sender_id,
                "receiver_id": msg.receiver_id,
                "message": msg.message,
                "is_read": bool(msg.is_read) if msg.is_read is not None else False,
                "timestamp": msg.timestamp.isoformat() if msg.timestamp else None,
                "sender": {
                    "id": sender.id if sender else None,
                    "name": sender.name if sender else "Unknown",
                    "email": sender.email if sender else ""
                } if msg.sender_id else None,
                "receiver": {
                    "id": receiver.id if receiver else None,
                    "name": receiver.name if receiver else "Unknown",
                    "email": receiver.email if receiver else ""
                } if msg.receiver_id else None,
                "is_user_sender": msg.sender_id == user.id
            }
            result.append(message_data)
        
        print(f"📱 Returning {len(result)} messages for user {user.email}")
        
        return jsonify({
            "success": True,
            "total": len(result),
            "data": result
        }), 200
        
    except Exception as e:
        print(f"❌ Error in user_get_messages: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            "success": False,
            "message": "Failed to fetch messages",
            "error": str(e)
        }), 500


# =========================
# USER SEND MESSAGE (NEW)
# =========================
@jwt_required()
def user_send_message():
    """
    Send a message from user to admin
    """
    try:
        # Get user ID from JWT token
        current_user_id = get_jwt_identity()
        
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({
                "success": False,
                "message": "Message content is required"
            }), 400
        
        message_content = data['message']
        
        print(f"📱 User {current_user_id} sending message: {message_content[:50]}...")
        
        # Get user
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({
                "success": False,
                "message": "User not found"
            }), 404
        
        # Find an admin (first admin in the system)
        admin = User.query.filter_by(role='admin').first()
        if not admin:
            return jsonify({
                "success": False,
                "message": "No admin available"
            }), 404
        
        # Create the message
        new_message = Message(
            sender_id=user.id,
            receiver_id=admin.id,
            message=message_content,
            is_read=False,
            timestamp=datetime.utcnow()
        )
        
        db.session.add(new_message)
        db.session.commit()
        
        print(f"✅ Message sent successfully. ID: {new_message.id}")
        
        return jsonify({
            "success": True,
            "message": "Message sent successfully",
            "data": {
                "id": new_message.id,
                "message": new_message.message,
                "timestamp": new_message.timestamp.isoformat()
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error in user_send_message: {e}")
        return jsonify({
            "success": False,
            "message": "Failed to send message",
            "error": str(e)
        }), 500


# =========================
# USER DELETE MESSAGE (NEW)
# =========================
@jwt_required()
def user_delete_message(message_id):
    """
    Delete a user's message
    """
    try:
        current_user_id = get_jwt_identity()
        
        print(f"📱 User {current_user_id} deleting message {message_id}")
        
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({
                "success": False,
                "message": "User not found"
            }), 404
        
        # Find message that belongs to this user
        # User can only delete their own sent messages
        message = Message.query.filter_by(
            id=message_id,
            sender_id=user.id
        ).first()
        
        if not message:
            return jsonify({
                "success": False,
                "message": "Message not found or access denied"
            }), 404
        
        db.session.delete(message)
        db.session.commit()
        
        print(f"✅ Message {message_id} deleted successfully")
        
        return jsonify({
            "success": True,
            "message": "Message deleted successfully"
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error in user_delete_message: {e}")
        return jsonify({
            "success": False,
            "message": "Failed to delete message",
            "error": str(e)
        }), 500