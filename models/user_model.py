from extensions import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    role = db.Column(db.Enum('user','admin'), default='user', nullable=False)
    status = db.Column(db.Enum('active','inactive'), default='active', nullable=False)
    password = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.TIMESTAMP, nullable=False)