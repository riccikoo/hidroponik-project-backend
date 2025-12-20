from flask import Blueprint
from controllers.mobile_controller import (
    register, login, get_sensor_data, user_get_messages, user_send_message, user_delete_message
)
from mqtt.mqtt_client import control_actuator

mobile_bp = Blueprint('mobile_bp', __name__)

mobile_bp.route('/register', methods=['POST'])(register)
mobile_bp.route('/login', methods=['POST'])(login)
mobile_bp.route('/get_sensor_data', methods=['GET'])(get_sensor_data)
mobile_bp.route('/control_actuator', methods=['POST'])(control_actuator)

# User message endpoints (with JWT)
mobile_bp.route("/user/messages", methods=["GET"])(user_get_messages)
mobile_bp.route("/user/messages", methods=["POST"])(user_send_message)
mobile_bp.route("/user/messages/<int:message_id>", methods=["DELETE"])(user_delete_message)