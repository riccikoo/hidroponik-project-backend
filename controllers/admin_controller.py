from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime, timedelta
from extensions import db
from models.message_model import Message

# ========== USER MANAGEMENT ENDPOINTS ==========
@jwt_required()
def get_users():
    """Get all users with pagination and search"""
    try:
        # Get current admin
        current_user_id = get_jwt_identity()
        admin = get_current_admin(current_user_id)
        
        if not admin:
            return jsonify({
                'status': False,
                'message': 'Unauthorized access. Admin only.'
            }), 403
        
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '').strip()
        
        # Base query
        from models.user_model import User
        query = User.query
        
        # Apply search filter
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                db.or_(
                    User.name.ilike(search_term),
                    User.email.ilike(search_term)
                )
            )
        
        # Get paginated results - PAKAI create_at (bukan created_at)
        paginated_users = query.order_by(
            User.create_at.desc()  # ✅ PAKAI create_at
        ).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        # Prepare user data
        users_data = []
        for user in paginated_users.items:
            user_data = {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'role': user.role,
                'status': user.status,
                'create_at': user.create_at.isoformat() if user.create_at else None,  # ✅ create_at
                'update_at': user.update_at.isoformat() if user.update_at else None,  # ✅ update_at
                'last_login': None,  # Model tidak punya last_login
            }
            
            users_data.append(user_data)
        
        # Build response
        response = {
            'status': True,
            'message': 'Users retrieved successfully',
            'data': {
                'users': users_data,
                'total': paginated_users.total,
                'page': paginated_users.page,
                'per_page': paginated_users.per_page,
                'total_pages': paginated_users.pages
            }
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        print(f"❌ Error fetching users: {e}")
        import traceback
        print(traceback.format_exc())
        return jsonify({
            'status': False,
            'message': f'Error fetching users: {str(e)}'
        }), 500

@jwt_required()
def update_user(user_id):
    """Update user status from Flutter"""
    try:
        # Get current admin
        current_user_id = get_jwt_identity()
        admin = get_current_admin(current_user_id)
        
        if not admin:
            return jsonify({
                'status': False,
                'message': 'Unauthorized access. Admin only.'
            }), 403
        
        # Get update data
        data = request.get_json()
        if not data:
            return jsonify({
                'status': False,
                'message': 'No data provided'
            }), 400
        
        print(f"📥 Received data for update: {data}")  # Debug
        
        # Get user
        from models.user_model import User
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'status': False,
                'message': 'User not found'
            }), 404
        
        # Prevent admin from modifying themselves
        if user.id == admin.id:
            return jsonify({
                'status': False,
                'message': 'Cannot modify your own account from admin panel'
            }), 400
        
        # HANDLE STATUS UPDATE (INI YANG PENTING!)
        if 'is_active' in data:
            # Flutter mengirim is_active (boolean)
            is_active_bool = data['is_active']
            
            # Convert boolean to string sesuai ENUM di database
            new_status = 'active' if is_active_bool else 'inactive'
            
            print(f"🔄 Updating user {user_id} status: {user.status} -> {new_status}")
            
            # Update status di database
            user.status = new_status
            
            # Update timestamp
            user.update_at = datetime.utcnow()  # ✅ PAKAI update_at (bukan updated_at)
            
            db.session.commit()
            
            response = {
                'status': True,
                'message': f'User status updated to {new_status}',
                'data': {
                    'id': user.id,
                    'name': user.name,
                    'email': user.email,
                    'status': new_status,
                    'is_active': is_active_bool,  # Kirim balik boolean untuk Flutter
                    'update_at': user.update_at.isoformat() if user.update_at else None
                }
            }
            
            print(f"✅ Update successful: {response}")
            return jsonify(response), 200
        
        # Jika ada field lain yang diupdate
        allowed_fields = ['role', 'name']
        updated_fields = []
        
        for field in allowed_fields:
            if field in data:
                if field == 'role' and data[field] not in ['admin', 'user']:
                    return jsonify({
                        'status': False,
                        'message': 'Role must be either "admin" or "user"'
                    }), 400
                
                setattr(user, field, data[field])
                updated_fields.append(field)
        
        if updated_fields:
            user.update_at = datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                'status': True,
                'message': f'User updated ({len(updated_fields)} fields)',
                'data': {
                    'id': user.id,
                    'updated_fields': updated_fields,
                    'name': user.name,
                    'email': user.email,
                    'role': user.role,
                    'status': user.status
                }
            }), 200
        
        return jsonify({
            'status': False,
            'message': 'No valid fields to update'
        }), 400
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error updating user: {e}")
        import traceback
        print(traceback.format_exc())
        return jsonify({
            'status': False,
            'message': f'Error updating user: {str(e)}'
        }), 500

@jwt_required()
def create_user():
    """Create a new user (admin only)"""
    try:
        # Get current admin
        current_user_id = get_jwt_identity()
        admin = get_current_admin(current_user_id)
        
        if not admin:
            return jsonify({
                'status': False,
                'message': 'Unauthorized access. Admin only.'
            }), 403
        
        # Get user data
        data = request.get_json()
        if not data:
            return jsonify({
                'status': False,
                'message': 'No data provided'
            }), 400
        
        print(f"📥 Create user data: {data}")  # Debug
        
        # Required fields
        required_fields = ['name', 'email', 'password']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    'status': False,
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Check if email already exists
        from models.user_model import User
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user:
            return jsonify({
                'status': False,
                'message': 'Email already registered'
            }), 400
        
        # Get status from request data
        status_value = data.get('status', 'active')  # Default to active
        
        # Hash password (gunakan hashing yang sama dengan register user biasa)
        from werkzeug.security import generate_password_hash
        hashed_password = generate_password_hash(data['password'])
        
        # Create new user - HANYA PAKAI FIELD YANG ADA DI MODEL
        current_time = datetime.utcnow()
        new_user = User(
            name=data['name'],
            email=data['email'],
            role=data.get('role', 'user'),
            status=status_value,  # ✅ HANYA status, BUKAN is_active
            password=hashed_password,  # Password sudah di-hash
            create_at=current_time,
            update_at=current_time
        )
        
        # Save to database
        db.session.add(new_user)
        db.session.commit()
        
        # Prepare response
        response = {
            'status': True,
            'message': 'User created successfully',
            'data': {
                'id': new_user.id,
                'name': new_user.name,
                'email': new_user.email,
                'role': new_user.role,
                'status': new_user.status,
                'create_at': new_user.create_at.isoformat(),
                'update_at': new_user.update_at.isoformat()
            }
        }
        
        print(f"✅ User created: {response}")
        return jsonify(response), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error creating user: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': False,
            'message': f'Error creating user: {str(e)}'
        }), 500

@jwt_required()
def get_user_details(user_id):
    """Get user details - simple version"""
    try:
        # Authentication
        current_user_id = get_jwt_identity()
        admin = get_current_admin(current_user_id)
        
        if not admin:
            return jsonify({'status': False, 'message': 'Admin access required'}), 403
        
        # Get user
        from models.user_model import User
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'status': False, 'message': 'User not found'}), 404
        
        # Build response data
        user_data = {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'role': user.role,
            'status': user.status,
            'create_at': user.create_at.isoformat() if user.create_at else None,
            'update_at': user.update_at.isoformat() if user.update_at else None,
            'is_active': user.status == 'active',  # Boolean untuk frontend
        }
        
        # Optional: Add password last updated info (jika ada)
        if hasattr(user, 'password_updated_at'):
            user_data['password_updated_at'] = user.password_updated_at.isoformat() if user.password_updated_at else None
        
        return jsonify({
            'status': True,
            'message': 'User details retrieved',
            'data': user_data
        }), 200
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'status': False, 'message': str(e)}), 500
    
@jwt_required()
def delete_user(user_id):
    """Delete a user"""
    try:
        # Get current admin
        current_user_id = get_jwt_identity()
        admin = get_current_admin(current_user_id)
        
        if not admin:
            return jsonify({
                'status': False,
                'message': 'Unauthorized access. Admin only.'
            }), 403
        
        # Get user
        from models.user_model import User
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'status': False,
                'message': 'User not found'
            }), 404
        
        # Prevent admin from deleting themselves
        if user.id == admin.id:
            return jsonify({
                'status': False,
                'message': 'Cannot delete your own account'
            }), 400
        
        # Check if user is admin (optional: prevent deleting other admins)
        if user.role == 'admin' and user.id != admin.id:
            return jsonify({
                'status': False,
                'message': 'Cannot delete another admin account'
            }), 400
        
        # Delete user
        db.session.delete(user)
        db.session.commit()
        
        response = {
            'status': True,
            'message': 'User deleted successfully',
            'data': {
                'deleted_user_id': user_id,
                'deleted_email': user.email
            }
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error deleting user: {e}")
        return jsonify({
            'status': False,
            'message': f'Error deleting user: {str(e)}'
        }), 500

@jwt_required()
def create_user():
    """Create a new user (admin only)"""
    try:
        # Get current admin
        current_user_id = get_jwt_identity()
        admin = get_current_admin(current_user_id)
        
        if not admin:
            return jsonify({
                'status': False,
                'message': 'Unauthorized access. Admin only.'
            }), 403
        
        # Get user data
        data = request.get_json()
        if not data:
            return jsonify({
                'status': False,
                'message': 'No data provided'
            }), 400
        
        # Required fields
        required_fields = ['name', 'email', 'password']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    'status': False,
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Check if email already exists
        from models.user_model import User
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user:
            return jsonify({
                'status': False,
                'message': 'Email already registered'
            }), 400
        
        # Create new user
        new_user = User(
            name=data['name'],
            email=data['email'],
            role=data.get('role', 'user'),
            status=data.get('status', 'active'),  # ✅ Gunakan status, bukan is_active
            password=data['password'],  # Jangan lupa password!
            create_at=datetime.utcnow(),
            update_at=datetime.utcnow()  # Jangan lupa update_at
        )
        
        # Set password (assuming User model has password field)
        if hasattr(new_user, 'password'):
            # You might need to hash the password here
            new_user.password = data['password']  # In production, use password hashing!
        
        # Save to database
        db.session.add(new_user)
        db.session.commit()
        
        # Prepare response
        response = {
            'status': True,
            'message': 'User created successfully',
            'data': {
                'id': new_user.id,
                'name': new_user.name,
                'email': new_user.email,
                'role': new_user.role,
                'status': new_user.status,  # ✅ PAKAI status, BUKAN is_active
                'is_active': new_user.status == 'active',  # ✅ Optional: tambah boolean untuk frontend
                'create_at': new_user.create_at.isoformat() if new_user.create_at else None,  # ✅ create_at (tanpa 'd')
                'update_at': new_user.update_at.isoformat() if new_user.update_at else None  # ✅ Jangan lupa update_at
            }
        }
        
        return jsonify(response), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error creating user: {e}")
        return jsonify({
            'status': False,
            'message': f'Error creating user: {str(e)}'
        }), 500

def get_current_admin(current_user_id):

    try:
        print(f"🔍 get_current_admin called with user_id: {current_user_id}")
        
        if not current_user_id:
            print("❌ No user_id provided")
            return None
        
        # Convert ke int
        try:
            user_id = int(current_user_id)
        except (ValueError, TypeError):
            print(f"❌ Cannot convert to int: '{current_user_id}'")
            return None
        
        from models.user_model import User
        user = User.query.get(user_id)
        
        if not user:
            print(f"❌ User not found with ID: {user_id}")
            return None
        
        # Cek role
        if not hasattr(user, 'role') or user.role != 'admin':
            print(f"❌ User is not admin: {getattr(user, 'role', 'no role')}")
            return None
        
        print(f"✅ Admin user found: {user.email}")
        return user
        
    except Exception as e:
        print(f"❌ Error in get_current_admin: {e}")
        import traceback
        traceback.print_exc()
        return None

def check_admin_access():
    """Decorator untuk mengecek akses admin"""
    def decorator(f):
        @jwt_required()
        def decorated_function(*args, **kwargs):
            current_user_id = get_jwt_identity()
            admin = get_current_admin(current_user_id)
            
            if not admin:
                return jsonify({
                    'status': False,
                    'message': 'Unauthorized access. Admin only.'
                }), 403
            
            return f(*args, **kwargs)
        
        decorated_function.__name__ = f.__name__
        return decorated_function
    return decorator

def _get_sensor_unit(sensor_name):
    """Get unit for sensor based on name"""
    units = {
        'dht_temp': '°C',
        'dht_humid': '%',
        'ph': 'pH',
        'ec': 'mS/cm',
        'ldr': 'Lux',
        'ultrasonic': 'cm',
        'temperature': '°C',
        'humidity': '%',
        'ph_level': 'pH',
        'ec_level': 'mS/cm',
        'light': 'Lux',
        'water_level': 'cm'
    }
    return units.get(sensor_name, 'unit')

# ========== SIMPLE TEST ENDPOINT ==========
@jwt_required()
def test_admin_endpoint():
    """Simple test endpoint untuk debugging"""
    try:
        current_user_id = get_jwt_identity()
        jwt_data = get_jwt()
        
        response = {
            'status': True,
            'message': 'Test endpoint reached',
            'debug': {
                'jwt_identity': current_user_id,
                'jwt_type': type(current_user_id).__name__,
                'jwt_data_keys': list(jwt_data.keys()) if jwt_data else None,
                'endpoint': '/api/admin/test',
                'timestamp': datetime.utcnow().isoformat(),
            }
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        print(f"❌ Test endpoint error: {e}")
        return jsonify({
            'status': False,
            'message': f'Test endpoint error: {str(e)}'
        }), 500

# ========== DASHBOARD STATS ==========
def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        from models.user_model import User
        from models.sensor_model import Sensor
        
        # 1. USER STATISTICS
        total_users = User.query.count()
        
        active_users = total_users
        if hasattr(User, 'last_login'):
            twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
            active_users = User.query.filter(
                User.last_login >= twenty_four_hours_ago
            ).count()
        
        # 2. SENSOR STATISTICS
        all_sensors = ['dht_temp', 'dht_humid', 'ph', 'ec', 'ldr', 'ultrasonic']
        sensor_stats = {
            'total': len(all_sensors),
            'online': 0,
            'online_percentage': 0,
            'latest_readings': {}
        }
        
        five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
        online_count = 0
        latest_readings = {}
        
        for sensor_name in all_sensors:
            latest_sensor = Sensor.query.filter_by(
                sensor_name=sensor_name
            ).order_by(
                Sensor.timestamp.desc()
            ).first()
            
            if latest_sensor:
                is_online = latest_sensor.timestamp >= five_minutes_ago if latest_sensor.timestamp else False
                
                if is_online:
                    online_count += 1
                
                latest_readings[sensor_name] = {
                    'value': float(latest_sensor.value) if latest_sensor.value else 0.0,
                    'unit': _get_sensor_unit(sensor_name),
                    'timestamp': latest_sensor.timestamp.isoformat() if latest_sensor.timestamp else None,
                    'online': is_online
                }
            else:
                latest_readings[sensor_name] = {
                    'value': 0.0,
                    'unit': _get_sensor_unit(sensor_name),
                    'timestamp': None,
                    'online': False
                }
        
        sensor_stats['online'] = online_count
        sensor_stats['online_percentage'] = round((online_count / sensor_stats['total'] * 100) if sensor_stats['total'] > 0 else 0, 1)
        sensor_stats['latest_readings'] = latest_readings
        
        # 3. SYSTEM STATUS
        system_status = 'online' if sensor_stats['online'] > 0 else 'offline'
        
        # 4. MESSAGES/ALERTS
        total_messages = 0
        unread_messages = 0
        try:
            current_user_id = get_jwt_identity()
            admin = get_current_admin(current_user_id)
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            total_messages = Message.query.filter(
                Message.timestamp >= today_start
            ).count()
            unread_messages = Message.query.filter_by(
                receiver_id=admin.id,
                is_read=False
            ).count()
        except Exception:
            pass
        
        # 5. DATABASE INFO
        try:
            db.session.execute('SELECT 1')
            db_status = 'connected'
        except:
            db_status = 'disconnected'
        
        # BUILD RESPONSE
        stats = {
            'status': True,
            'message': 'Dashboard statistics retrieved successfully',
            'data': {
                'users': {
                    'total': total_users,
                    'active': active_users,
                    'online_percentage': round((active_users / total_users * 100) if total_users > 0 else 0, 1)
                },
                'sensors': sensor_stats,
                'system': {
                    'status': system_status,
                    'database': db_status,
                    'timestamp': datetime.utcnow().isoformat()
                },
                'messages': {
                    'total_today': total_messages,
                    'unread': unread_messages
                }
            }
        }
        
        return jsonify(stats), 200
        
    except Exception as e:
        print(f"❌ Dashboard stats error: {e}")
        return jsonify({
            'status': False,
            'message': f'Error retrieving dashboard stats: {str(e)}'
        }), 500

def get_sensor_history():
    """Get sensor history for charts"""
    try:
        from models.sensor_model import Sensor
        
        sensor_name = request.args.get('sensor', 'dht_temp')
        hours = request.args.get('hours', 24, type=int)
        limit = request.args.get('limit', 100, type=int)
        
        time_threshold = datetime.utcnow() - timedelta(hours=hours)
        
        sensor_data = Sensor.query.filter(
            Sensor.sensor_name == sensor_name,
            Sensor.timestamp >= time_threshold
        ).order_by(
            Sensor.timestamp.desc()
        ).limit(limit).all()
        
        chart_data = []
        for reading in sensor_data:
            chart_data.append({
                'timestamp': reading.timestamp.isoformat() if reading.timestamp else None,
                'value': float(reading.value) if reading.value else 0.0,
                'unit': _get_sensor_unit(sensor_name)
            })
        
        return jsonify({
            'status': True,
            'message': f'Sensor history for {sensor_name} retrieved',
            'data': {
                'sensor': sensor_name,
                'unit': _get_sensor_unit(sensor_name),
                'readings': chart_data,
                'count': len(chart_data),
                'time_range_hours': hours
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': False,
            'message': f'Error retrieving sensor history: {str(e)}'
        }), 500

def get_quick_stats():
    """Get quick stats for dashboard cards"""
    try:
        from models.user_model import User
        from models.sensor_model import Sensor
        
        stats = {
            'total_users': User.query.count(),
            'total_sensors': Sensor.query.distinct(Sensor.sensor_name).count(),
            'online_sensors': 0,
            'system_status': 'online',
            'last_update': datetime.utcnow().isoformat()
        }
        
        five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
        unique_sensors = db.session.query(
            Sensor.sensor_name.distinct()
        ).filter(
            Sensor.timestamp >= five_minutes_ago
        ).count()
        
        stats['online_sensors'] = unique_sensors
        
        return jsonify({
            'status': True,
            'message': 'Quick stats retrieved',
            'data': stats
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': False,
            'message': f'Error retrieving quick stats: {str(e)}'
        }), 500

# ========== MESSAGES ENDPOINTS ==========
@jwt_required()
def get_admin_messages():
    """Get all messages received by admin"""
    try:
        current_user_id = get_jwt_identity()
        admin = get_current_admin(current_user_id)

        messages = Message.query.filter_by(
            receiver_id=admin.id
        ).order_by(Message.timestamp.desc()).all()

        result = []
        for msg in messages:
            message_data = {
                "id": msg.id,
                "sender_id": msg.sender_id,
                "receiver_id": msg.receiver_id,
                "message": msg.message,
                "is_read": bool(msg.is_read) if msg.is_read is not None else False,
                "timestamp": msg.timestamp.isoformat() if msg.timestamp else None,
            }
            
            if hasattr(msg, 'sender') and msg.sender:
                message_data["sender"] = {
                    "id": msg.sender.id,
                    "name": msg.sender.name,
                    "email": msg.sender.email
                }
            else:
                from models.user_model import User
                sender = User.query.get(msg.sender_id)
                if sender:
                    message_data["sender"] = {
                        "id": sender.id,
                        "name": sender.name,
                        "email": sender.email
                    }
            
            result.append(message_data)

        return jsonify({
            "success": True,
            "total": len(result),
            "data": result
        }), 200

    except Exception as e:
        print(f"❌ Failed to fetch messages: {e}")
        return jsonify({
            "success": False,
            "message": "Failed to fetch messages",
            "error": str(e)
        }), 500

@jwt_required()
def mark_message_read(message_id):
    """Mark message as read"""
    try:
        # 1. Get current user from JWT
        current_user_id = get_jwt_identity()
        
        # 2. Check if user is admin
        admin = get_current_admin(current_user_id)
        if not admin:
            return jsonify({
                "success": False,
                "message": "Admin access required"
            }), 403

        # 3. Find message belonging to this admin
        message = Message.query.filter_by(
            id=message_id,
            receiver_id=admin.id  # Only messages sent to this admin
        ).first()

        if not message:
            return jsonify({
                "success": False,
                "message": "Message not found"
            }), 404

        # 4. Mark as read
        message.is_read = True
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Message marked as read"
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"❌ Error marking message as read: {e}")
        return jsonify({
            "success": False,
            "message": "Server error",
            "error": str(e)
        }), 500

@jwt_required()
def delete_message(message_id):
    """Delete message"""
    try:
        current_user_id = get_jwt_identity()
        admin = get_current_admin(current_user_id)

        message = Message.query.filter_by(
            id=message_id,
            receiver_id=admin.id
        ).first()

        if not message:
            return jsonify({
                "success": False,
                "message": "Message not found"
            }), 404

        db.session.delete(message)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Message deleted"
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"❌ Error deleting message: {e}")
        return jsonify({
            "success": False,
            "message": "Failed to delete message",
            "error": str(e)
        }), 500

@jwt_required()
def admin_unread_count():
    """Get unread messages count"""
    try:
        current_user_id = get_jwt_identity()
        admin = get_current_admin(current_user_id)
        
        count = Message.query.filter_by(
            receiver_id=admin.id,
            is_read=False
        ).count()
        
        return jsonify({
            "success": True,
            "unread": count
        }), 200
        
    except Exception as e:
        print(f"❌ Error getting unread count: {e}")
        return jsonify({
            "success": False,
            "unread": 0,
            "error": str(e)
        }), 500

# ========== MESSAGE REPLIES ==========
@jwt_required()
def get_message_replies(message_id):
    """Get all replies for a specific message"""
    try:
        current_user_id = get_jwt_identity()
        admin = get_current_admin(current_user_id)

        original_message = Message.query.filter_by(
            id=message_id,
            receiver_id=admin.id
        ).first()

        if not original_message:
            return jsonify({
                "status": True,
                "data": []
            }), 200

        user_id = original_message.sender_id
        
        user_replies = Message.query.filter(
            Message.sender_id == user_id,
            Message.receiver_id == admin.id,
            Message.id != message_id,
            Message.timestamp > original_message.timestamp
        ).order_by(Message.timestamp.asc()).all()
        
        admin_replies = Message.query.filter(
            Message.sender_id == admin.id,
            Message.receiver_id == user_id,
            Message.timestamp >= original_message.timestamp
        ).order_by(Message.timestamp.asc()).all()

        all_messages = list(user_replies) + list(admin_replies)
        all_messages.sort(key=lambda x: x.timestamp)

        result = []
        
        result.append({
            "id": original_message.id,
            "content": original_message.message,
            "sender_name": original_message.sender.name if original_message.sender else "User",
            "sender_email": original_message.sender.email if original_message.sender else "user@email.com",
            "is_admin": False,
            "timestamp": original_message.timestamp.isoformat() if original_message.timestamp else None
        })
        
        for msg in all_messages:
            is_admin_sender = msg.sender_id == admin.id
            result.append({
                "id": msg.id,
                "content": msg.message,
                "sender_name": "Admin" if is_admin_sender else (msg.sender.name if msg.sender else "User"),
                "sender_email": admin.email if is_admin_sender else (msg.sender.email if msg.sender else "user@email.com"),
                "is_admin": is_admin_sender,
                "timestamp": msg.timestamp.isoformat() if msg.timestamp else None
            })

        return jsonify({
            "status": True,
            "data": result
        }), 200

    except Exception as e:
        print(f"❌ Failed to fetch replies: {e}")
        return jsonify({
            "status": False,
            "message": "Failed to fetch replies",
            "data": []
        }), 500

@jwt_required()
def send_message_reply(message_id):
    """Send a reply to a message"""
    try:
        current_user_id = get_jwt_identity()
        admin = get_current_admin(current_user_id)
        data = request.get_json()
        
        if not data or 'content' not in data:
            return jsonify({
                "status": False,
                "message": "Content is required"
            }), 400

        content = data['content'].strip()
        if not content:
            return jsonify({
                "status": False,
                "message": "Content cannot be empty"
            }), 400

        original_message = Message.query.filter_by(
            id=message_id,
            receiver_id=admin.id
        ).first()

        if not original_message:
            return jsonify({
                "status": False,
                "message": "Original message not found"
            }), 404
        
        user_id = original_message.sender_id
        
        new_message = Message(
            sender_id=admin.id,
            receiver_id=user_id,
            message=content,
            is_read=False,
            timestamp=datetime.utcnow()
        )
        db.session.add(new_message)
        
        if not original_message.is_read:
            original_message.is_read = True
        
        db.session.commit()

        return jsonify({
            "status": True,
            "message": "Reply sent successfully",
            "data": {
                "id": new_message.id,
                "content": new_message.message,
                "sender_name": "Admin",
                "sender_email": admin.email,
                "is_admin": True,
                "timestamp": new_message.timestamp.isoformat() if new_message.timestamp else datetime.utcnow().isoformat()
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"❌ Error sending reply: {e}")
        return jsonify({
            "status": False,
            "message": "Failed to send reply"
        }), 500

@jwt_required()
def get_simple_replies(message_id):
    """Simplified version - hanya ambil original + admin replies"""
    try:
        current_user_id = get_jwt_identity()
        admin = get_current_admin(current_user_id)
        
        original = Message.query.filter_by(
            id=message_id,
            receiver_id=admin.id
        ).first()
        
        if not original:
            return jsonify({"success": False, "message": "Not found"}), 404
        
        user_id = original.sender_id
        admin_replies = Message.query.filter(
            Message.sender_id == admin.id,
            Message.receiver_id == user_id,
            Message.timestamp > original.timestamp
        ).order_by(Message.timestamp.asc()).all()
        
        user_replies = Message.query.filter(
            Message.sender_id == user_id,
            Message.receiver_id == admin.id,
            Message.timestamp > original.timestamp
        ).order_by(Message.timestamp.asc()).all()
        
        all_replies = admin_replies + user_replies
        all_replies.sort(key=lambda x: x.timestamp)
        
        thread = []
        
        thread.append({
            "id": original.id,
            "content": original.message,
            "sender_id": original.sender_id,
            "sender_name": original.sender.name if original.sender else "User",
            "is_admin": False,
            "timestamp": original.timestamp.isoformat() if original.timestamp else None
        })
        
        for msg in all_replies:
            is_admin_sender = msg.sender_id == admin.id
            thread.append({
                "id": msg.id,
                "content": msg.message,
                "sender_id": msg.sender_id,
                "sender_name": "Admin" if is_admin_sender else (msg.sender.name if msg.sender else "User"),
                "is_admin": is_admin_sender,
                "timestamp": msg.timestamp.isoformat() if msg.timestamp else None
            })
        
        return jsonify({
            "success": True,
            "data": thread
        }), 200
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@jwt_required()
def get_all_threads():
    """Get all conversation threads for admin"""
    try:
        current_user_id = get_jwt_identity()
        admin = get_current_admin(current_user_id)
        
        # Cari semua user yang pernah mengirim pesan ke admin
        from sqlalchemy import distinct
        user_ids = db.session.query(distinct(Message.sender_id)).filter(
            Message.receiver_id == admin.id
        ).union(
            db.session.query(distinct(Message.receiver_id)).filter(
                Message.sender_id == admin.id
            )
        ).all()
        
        threads = []
        
        for (user_id,) in user_ids:
            if user_id == admin.id:
                continue
                
            # Get user info
            from models.user_model import User
            user = User.query.get(user_id)
            if not user:
                continue
            
            # Get last message in conversation
            last_message = Message.query.filter(
                db.or_(
                    db.and_(
                        Message.sender_id == user_id,
                        Message.receiver_id == admin.id
                    ),
                    db.and_(
                        Message.sender_id == admin.id,
                        Message.receiver_id == user_id
                    )
                )
            ).order_by(Message.timestamp.desc()).first()
            
            if last_message:
                # Generate consistent thread ID
                thread_id = f"{min(user_id, admin.id)}-{max(user_id, admin.id)}"
                
                # Count unread messages
                unread_count = Message.query.filter(
                    Message.sender_id == user_id,
                    Message.receiver_id == admin.id,
                    Message.is_read == False
                ).count()
                
                # Count total messages
                total_messages = Message.query.filter(
                    db.or_(
                        db.and_(
                            Message.sender_id == user_id,
                            Message.receiver_id == admin.id
                        ),
                        db.and_(
                            Message.sender_id == admin.id,
                            Message.receiver_id == user_id
                        )
                    )
                ).count()
                
                threads.append({
                    "thread_id": thread_id,  # Use consistent thread ID
                    "user_id": user_id,
                    "user_name": user.name,
                    "user_email": user.email,
                    "last_message": {
                        "id": last_message.id,
                        "content": last_message.message[:100] + "..." if len(last_message.message) > 100 else last_message.message,
                        "is_admin": last_message.sender_id == admin.id,
                        "timestamp": last_message.timestamp.isoformat() if last_message.timestamp else None
                    },
                    "unread_count": unread_count,
                    "total_messages": total_messages,
                    "last_message_id": last_message.id  # Important for replies
                })
        
        # Sort by last message timestamp
        threads.sort(key=lambda x: x['last_message']['timestamp'] or '', reverse=True)
        
        return jsonify({
            "success": True,
            "data": {
                "total_threads": len(threads),
                "total_unread": sum(t['unread_count'] for t in threads),
                "threads": threads
            }
        }), 200
        
    except Exception as e:
        print(f"Error getting threads: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@jwt_required()
def get_thread_messages():
    """Get all messages in a specific thread"""
    try:
        current_user_id = get_jwt_identity()
        admin = get_current_admin(current_user_id)
        
        # Get parameters
        user_id = request.args.get('user_id', type=int)
        thread_id = request.args.get('thread_id')
        
        if not user_id and not thread_id:
            return jsonify({"success": False, "message": "user_id or thread_id required"}), 400
        
        # If thread_id provided, parse it
        if thread_id:
            try:
                user_id = int(thread_id.split('-')[1])
                if user_id == admin.id:
                    user_id = int(thread_id.split('-')[0])
            except:
                return jsonify({"success": False, "message": "Invalid thread_id"}), 400
        
        # Get all messages between admin and user
        messages = Message.query.filter(
            db.or_(
                db.and_(
                    Message.sender_id == user_id,
                    Message.receiver_id == admin.id
                ),
                db.and_(
                    Message.sender_id == admin.id,
                    Message.receiver_id == user_id
                )
            )
        ).order_by(Message.timestamp.asc()).all()
        
        # Mark user messages as read
        Message.query.filter(
            Message.sender_id == user_id,
            Message.receiver_id == admin.id,
            Message.is_read == False
        ).update({Message.is_read: True})
        db.session.commit()
        
        # Get user info
        from models.user_model import User
        user = User.query.get(user_id)
        
        messages_data = []
        for msg in messages:
            messages_data.append({
                "id": msg.id,
                "content": msg.message,
                "sender_id": msg.sender_id,
                "receiver_id": msg.receiver_id,
                "is_admin": msg.sender_id == admin.id,
                "is_read": msg.is_read,
                "timestamp": msg.timestamp.isoformat() if msg.timestamp else None
            })
        
        return jsonify({
            "success": True,
            "data": {
                "thread_id": f"{min(user_id, admin.id)}-{max(user_id, admin.id)}",
                "user": {
                    "id": user_id,
                    "name": user.name if user else "User",
                    "email": user.email if user else "user@email.com"
                },
                "total_messages": len(messages),
                "messages": messages_data
            }
        }), 200
        
    except Exception as e:
        print(f"Error getting thread messages: {e}")
        return jsonify({"success": False, "message": str(e)}), 500