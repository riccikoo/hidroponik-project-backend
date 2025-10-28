from flask import Flask
from flask_migrate import Migrate
from extensions import db, bcrypt
from routes.auth_routes import auth_bp
from flask_cors import CORS
from flask_jwt_extended import JWTManager

def create_app():
    app = Flask(__name__)

    from models.user_model import User
    from models.sensor_model import Sensor

    # Konfigurasi database MySQL
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/hidroponik_db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'supersecretkey'

    # Inisialisasi ekstensi
    db.init_app(app)
    bcrypt.init_app(app)
    Migrate(app, db)

    # ⬅️ Aktifkan CORS untuk semua route
    CORS(app)

    # Register blueprint
    app.register_blueprint(auth_bp, url_prefix="/api")

    #JWT
    app.config["JWT_SECRET_KEY"] = "super-secret-key-replace-with-env-var"
    jwt = JWTManager(app)

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
