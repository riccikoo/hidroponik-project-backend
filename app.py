from flask import Flask, jsonify
from flask_migrate import Migrate
from extensions import db, bcrypt
from routes.mobile_routes import mobile_bp
from routes.web_routes import web_bp
from routes.admin_routes import admin_bp
from dummy import test_bp
from flask_cors import CORS
from mqtt.mqtt_client import init_mqtt
from flask_jwt_extended import JWTManager

def create_app():
    app = Flask(__name__)

    from models.user_model import User
    from models.sensor_model import Sensor
    from models.aktuator_model import Aktuator

    # Konfigurasi database MySQL
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/hidroponik_db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'supersecretkey'
    app.config["JWT_TOKEN_LOCATION"] = ["headers"]  # penting! header, bukan cookie
    app.config["JWT_HEADER_NAME"] = "Authorization"
    app.config["JWT_HEADER_TYPE"] = "Bearer"
    app.config["JWT_SECRET_KEY"] = "super-secret-key-replace-with-env-var"  # Pindah ke sini

    # Inisialisasi ekstensi
    db.init_app(app)
    bcrypt.init_app(app)
    Migrate(app, db)
    
    init_mqtt(app) 

    # Aktifkan CORS untuk semua route
    CORS(app, supports_credentials=True)
    
    # Register blueprint
    app.register_blueprint(mobile_bp, url_prefix="/api")
    app.register_blueprint(web_bp, url_prefix="/")
    app.register_blueprint(test_bp, url_prefix="/api")
    app.register_blueprint(admin_bp)

    return app

app = create_app()
jwt = JWTManager(app)  # BUAT JWTManager DI SINI

# ========== JWT CALLBACKS ==========
# IMPORTANT: These callbacks must be defined AFTER jwt = JWTManager(app)

@jwt.user_identity_loader
def user_identity_lookup(user):
    """
    Dipanggil saat create_access_token() dipanggil.
    Pastikan identity selalu string.
    """
    # Debug
    print(f"🔧 user_identity_lookup called with: {user} (type: {type(user).__name__})")
    
    # Jika user adalah User object
    if hasattr(user, 'id'):
        identity = str(user.id)
    # Jika user adalah integer (dari user.id)
    elif isinstance(user, int):
        identity = str(user)
    # Jika sudah string
    elif isinstance(user, str):
        identity = user
    else:
        # Fallback
        identity = str(user)
    
    print(f"🔧 JWT identity set to: '{identity}'")
    return identity

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    """
    Dipanggil saat @jwt_required() digunakan.
    Convert JWT identity (string) back to user object.
    """
    from models.user_model import User
    
    identity = jwt_data["sub"]
    print(f"🔧 user_lookup_callback called with identity: '{identity}' (type: {type(identity).__name__})")
    
    try:
        # Identity harus string, convert ke int
        user_id = int(identity)
        user = User.query.get(user_id)
        print(f"🔧 User found: {user}")
        return user
    except (ValueError, TypeError) as e:
        print(f"❌ Error converting identity to int: '{identity}' - {e}")
        return None

@jwt.additional_claims_loader
def add_claims_to_access_token(identity):
    """
    Tambahkan custom claims ke token.
    """
    from models.user_model import User
    
    try:
        user_id = int(identity) if isinstance(identity, str) else identity
        user = User.query.get(user_id)
        
        if user:
            return {
                'email': user.email,
                'role': user.role if hasattr(user, 'role') else 'user',
                'name': user.name if hasattr(user, 'name') else '',
            }
    except Exception as e:
        print(f"❌ Error adding claims: {e}")
    
    return {}

# ========== ERROR HANDLERS ==========
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_data):
    return jsonify({
        'status': False,
        'message': 'Token has expired'
    }), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({
        'status': False,
        'message': f'Invalid token: {error}'
    }), 422

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({
        'status': False,
        'message': 'Missing authorization token'
    }), 401

if __name__ == "__main__":
    print("🚀 Starting Flask app with JWT callbacks...")
    app.run('0.0.0.0', debug=True)