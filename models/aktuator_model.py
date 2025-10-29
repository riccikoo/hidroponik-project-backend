from extensions import db

class Aktuator(db.Model):
    __tablename__ = 'aktuator'
    id = db.Column(db.Integer, primary_key=True)
    akt_name = db.Column(db.Enum("water","ph","lamp"), nullable=False)
    runtime = db.Column(db.TIMESTAMP, nullable=False)
    timestamp = db.Column(db.TIMESTAMP, nullable=False)