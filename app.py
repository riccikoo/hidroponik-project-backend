from flask import Flask
from flask_migrate import Migrate
from extensions import db, bcrypt
from routes.mobile_routes import auth_bp
from routes.web_routes import web_bp
from flask_cors import CORS
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

    # Inisialisasi ekstensi
    db.init_app(app)
    bcrypt.init_app(app)
    Migrate(app, db)

    # Aktifkan CORS untuk semua route
    CORS(app, supports_credentials=True)
    # Register blueprint
    app.register_blueprint(auth_bp, url_prefix="/api")
    app.register_blueprint(web_bp, url_prefix="/")

    # JWT
    app.config["JWT_SECRET_KEY"] = "super-secret-key-replace-with-env-var"
    jwt = JWTManager(app)

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
