from extensions import db
class Sensor(db.Model):
    __tablename__ = 'sensor'
    id = db.Column(db.Integer, primary_key=True)
    sensor_name = db.Column(db.Enum("dht","ldr","ph","ec","ultrasonic"), nullable=False)
    value = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.TIMESTAMP, nullable=False)