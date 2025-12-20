# models/message_model.py
from extensions import db
from datetime import datetime

class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)

    sender_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=False
    )
    receiver_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=False
    )

    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)

    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    sender = db.relationship(
        'User',
        foreign_keys=[sender_id],
        backref='sent_messages'
    )
    receiver = db.relationship(
        'User',
        foreign_keys=[receiver_id],
        backref='received_messages'
    )
