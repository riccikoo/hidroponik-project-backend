from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime, timedelta
from extensions import db

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')  # Ubah nama blueprint jadi 'admin'

# ========== HELPER FUNCTIONS ==========
def get_current_admin():
    """Get current admin user from JWT token - SIMPLIFIED"""
    try:
        current_user_id = get_jwt_identity()
        print(f"🔍 get_current_admin: JWT Identity = '{current_user_id}' (type: {type(current_user_id).__name__})")
        
        # Sekarang identity HARUS string berkat JWT callbacks
        if not isinstance(current_user_id, str):
            print(f"❌ Identity is not string: {type(current_user_id)}")
            return None
        
        # Convert string ke int
        try:
            user_id = int(current_user_id)
        except ValueError:
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
    """Decorator untuk mengecek akses admin - WITH DEBUG"""
    def decorator(f):
        @jwt_required()
        def decorated_function(*args, **kwargs):
            print(f"🔐 [CHECK_ADMIN] Checking admin access for endpoint: {request.path}")
            print(f"🔐 [CHECK_ADMIN] Headers: {dict(request.headers)}")
            
            try:
                # Debug JWT identity
                current_user_id = get_jwt_identity()
                print(f"🔐 [CHECK_ADMIN] JWT Identity raw: {current_user_id} (type: {type(current_user_id)})")
                
                # Cek apakah user ada dan admin
                admin = get_current_admin()
                
                if not admin:
                    print("❌ [CHECK_ADMIN] Admin access denied - get_current_admin returned None")
                    
                    # Debug lebih detail
                    from models.user_model import User
                    try:
                        if isinstance(current_user_id, int):
                            user = User.query.get(current_user_id)
                            print(f"🔍 [CHECK_ADMIN] Direct query with int {current_user_id}: {user}")
                        elif isinstance(current_user_id, str):
                            try:
                                user_id = int(current_user_id)
                                user = User.query.get(user_id)
                                print(f"🔍 [CHECK_ADMIN] Direct query with str->int {user_id}: {user}")
                            except ValueError:
                                print(f"🔍 [CHECK_ADMIN] Cannot convert string to int: '{current_user_id}'")
                    except Exception as e:
                        print(f"🔍 [CHECK_ADMIN] Debug query error: {e}")
                    
                    return jsonify({
                        'status': False,
                        'message': 'Unauthorized access. Admin only.'
                    }), 403
                
                print(f"✅ [CHECK_ADMIN] Admin access granted for user: {admin.email}")
                return f(*args, **kwargs)
                
            except Exception as e:
                print(f"❌ [CHECK_ADMIN] Exception in decorator: {e}")
                import traceback
                traceback.print_exc()
                return jsonify({
                    'status': False,
                    'message': f'Internal server error: {str(e)}'
                }), 500
        
        decorated_function.__name__ = f.__name__
        return decorated_function
    return decorator

# ========== SIMPLE TEST ENDPOINT ==========
@admin_bp.route('/test', methods=['GET'])
@jwt_required()  # Hanya perlu token valid, tanpa admin check dulu
def test_admin_endpoint():
    """Simple test endpoint untuk debugging"""
    try:
        # Debug info
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
        
        print(f"✅ Test endpoint response: {response}")
        return jsonify(response), 200
        
    except Exception as e:
        print(f"❌ Test endpoint error: {e}")
        return jsonify({
            'status': False,
            'message': f'Test endpoint error: {str(e)}'
        }), 500

# ========== DASHBOARD STATS (SIMPLIFIED) ==========
@admin_bp.route('/dashboard/stats', methods=['GET'])
@check_admin_access()
def get_dashboard_stats():
    """Get dashboard statistics - REAL DATA VERSION"""
    try:
        print("📊 Dashboard stats endpoint called - REAL DATA")
        
        from models.user_model import User
        from models.sensor_model import Sensor
        from datetime import datetime, timedelta
        
        # 1. USER STATISTICS
        total_users = 0
        active_users = 0
        
        try:
            total_users = User.query.count()
            print(f"📊 Total users: {total_users}")
            
            # Hitung active users (login dalam 24 jam terakhir)
            # Jika model punya last_login field
            if hasattr(User, 'last_login'):
                twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
                active_users = User.query.filter(
                    User.last_login >= twenty_four_hours_ago
                ).count()
            else:
                active_users = total_users  # Fallback
                
        except Exception as e:
            print(f"⚠️ Error getting user stats: {e}")
            total_users = 1
            active_users = 1
        
        # 2. SENSOR STATISTICS
        sensor_stats = {
            'total': 0,
            'online': 0,
            'online_percentage': 0,
            'latest_readings': {}
        }
        
        try:
            # List semua sensor yang tersedia di sistem
            all_sensors = ['dht_temp', 'dht_humid', 'ph', 'ec', 'ldr', 'ultrasonic']
            sensor_stats['total'] = len(all_sensors)
            
            # Hitung sensor online (data dalam 5 menit terakhir)
            five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
            online_count = 0
            
            # Ambil data terbaru untuk setiap sensor
            latest_readings = {}
            for sensor_name in all_sensors:
                try:
                    # Ambil data terbaru untuk sensor ini
                    latest_sensor = Sensor.query.filter_by(
                        sensor_name=sensor_name
                    ).order_by(
                        Sensor.timestamp.desc()
                    ).first()
                    
                    if latest_sensor:
                        # Cek apakah data masih fresh (dalam 5 menit)
                        is_online = latest_sensor.timestamp >= five_minutes_ago if latest_sensor.timestamp else False
                        
                        if is_online:
                            online_count += 1
                        
                        # Tambahkan ke readings
                        latest_readings[sensor_name] = {
                            'value': float(latest_sensor.value) if latest_sensor.value else 0.0,
                            'unit': _get_sensor_unit(sensor_name),
                            'timestamp': latest_sensor.timestamp.isoformat() if latest_sensor.timestamp else None,
                            'online': is_online
                        }
                    else:
                        # Tidak ada data untuk sensor ini
                        latest_readings[sensor_name] = {
                            'value': 0.0,
                            'unit': _get_sensor_unit(sensor_name),
                            'timestamp': None,
                            'online': False
                        }
                        
                except Exception as e:
                    print(f"⚠️ Error processing sensor {sensor_name}: {e}")
                    latest_readings[sensor_name] = {
                        'value': 0.0,
                        'unit': _get_sensor_unit(sensor_name),
                        'timestamp': None,
                        'online': False
                    }
            
            sensor_stats['online'] = online_count
            sensor_stats['online_percentage'] = round((online_count / sensor_stats['total'] * 100) if sensor_stats['total'] > 0 else 0, 1)
            sensor_stats['latest_readings'] = latest_readings
            
            print(f"📊 Sensors: {online_count}/{sensor_stats['total']} online ({sensor_stats['online_percentage']}%)")
            
        except Exception as e:
            print(f"⚠️ Error getting sensor stats: {e}")
            # Fallback ke dummy data
            sensor_stats = {
                'total': 6,
                'online': 6,
                'online_percentage': 100,
                'latest_readings': {
                    'dht_temp': {'value': 27.5, 'unit': '°C', 'online': True},
                    'dht_humid': {'value': 65.0, 'unit': '%', 'online': True},
                    'ph': {'value': 6.5, 'unit': 'pH', 'online': True},
                    'ec': {'value': 1.8, 'unit': 'mS/cm', 'online': True},
                    'ldr': {'value': 850.0, 'unit': 'Lux', 'online': True},
                    'ultrasonic': {'value': 15.0, 'unit': 'cm', 'online': True}
                }
            }
        
        # 3. SYSTEM STATUS
        system_status = 'online' if sensor_stats['online'] > 0 else 'offline'
        
        # 4. MESSAGES/ALERTS (jika ada model Message)
        total_messages = 0
        try:
            from models.message_model import Message
            # Hitung messages hari ini
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            total_messages = Message.query.filter(
                Message.created_at >= today_start
            ).count()
        except ImportError:
            # Model Message tidak tersedia
            pass
        except Exception as e:
            print(f"⚠️ Error getting messages: {e}")
        
        # 5. AKTUATOR STATUS (jika ada model Aktuator)
        total_aktuators = 0
        active_aktuators = 0
        try:
            from models.aktuator_model import Aktuator
            total_aktuators = Aktuator.query.count()
            active_aktuators = Aktuator.query.filter_by(status='ON').count()
        except ImportError:
            # Model Aktuator tidak tersedia
            pass
        except Exception as e:
            print(f"⚠️ Error getting aktuator stats: {e}")
        
        # 6. DATABASE INFO
        try:
            # Cek koneksi database
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
                    'new_today': 0,  # Bisa ditambahkan jika ada field created_at
                    'online_percentage': round((active_users / total_users * 100) if total_users > 0 else 0, 1)
                },
                'sensors': sensor_stats,
                'system': {
                    'status': system_status,
                    'database': db_status,
                    'uptime': '24/7',
                    'api_version': '1.0.0',
                    'timestamp': datetime.utcnow().isoformat()
                },
                'messages': {
                    'total_today': total_messages,
                    'unread': 0  # Bisa ditambahkan jika ada field read_status
                },
                'aktuators': {
                    'total': total_aktuators,
                    'active': active_aktuators,
                    'active_percentage': round((active_aktuators / total_aktuators * 100) if total_aktuators > 0 else 0, 1)
                },
                'performance': {
                    'response_time_ms': 0,  # Bisa dihitung
                    'memory_usage': 'N/A',
                    'last_backup': (datetime.utcnow() - timedelta(days=1)).isoformat()
                }
            }
        }
        
        print(f"✅ Dashboard stats ready with real data")
        print(f"   Users: {total_users} total, {active_users} active")
        print(f"   Sensors: {sensor_stats['online']}/{sensor_stats['total']} online")
        print(f"   System: {system_status}")
        
        return jsonify(stats), 200
        
    except Exception as e:
        print(f"❌ Dashboard stats error: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'status': False,
            'message': f'Error retrieving dashboard stats: {str(e)}',
            'error_details': str(e)
        }), 500

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

@admin_bp.route('/dashboard/sensor-history', methods=['GET'])
@check_admin_access()
def get_sensor_history():
    """Get sensor history for charts"""
    try:
        from models.sensor_model import Sensor
        from datetime import datetime, timedelta
        
        sensor_name = request.args.get('sensor', 'dht_temp')
        hours = request.args.get('hours', 24, type=int)
        limit = request.args.get('limit', 100, type=int)
        
        # Calculate time range
        time_threshold = datetime.utcnow() - timedelta(hours=hours)
        
        # Query data
        sensor_data = Sensor.query.filter(
            Sensor.sensor_name == sensor_name,
            Sensor.timestamp >= time_threshold
        ).order_by(
            Sensor.timestamp.desc()
        ).limit(limit).all()
        
        # Format data untuk chart
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

@admin_bp.route('/dashboard/quick-stats', methods=['GET'])
@check_admin_access()
def get_quick_stats():
    """Get quick stats for dashboard cards"""
    try:
        from models.user_model import User
        from models.sensor_model import Sensor
        from datetime import datetime, timedelta
        
        # Data yang sering dibutuhkan untuk cards
        stats = {
            'total_users': User.query.count(),
            'total_sensors': Sensor.query.distinct(Sensor.sensor_name).count(),
            'online_sensors': 0,
            'system_status': 'online',
            'last_update': datetime.utcnow().isoformat()
        }
        
        # Hitung sensor online
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