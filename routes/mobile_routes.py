from flask import Blueprint
from controllers.mobile_controller import register, login, get_sensor_data, admin_update_user_status, admin_send_message, user_get_messages
from mqtt.mqtt_client import control_actuator
mobile_bp = Blueprint('mobile_bp', __name__)

mobile_bp.route('/register', methods=['POST'])(register)
mobile_bp.route('/login', methods=['POST'])(login)
mobile_bp.route('/get_sensor_data', methods=['GET'])(get_sensor_data)
mobile_bp.route('/control_actuator', methods=['POST'])(control_actuator)
mobile_bp.route("/admin/user/<int:user_id>/status", methods=["PATCH"])(admin_update_user_status)
mobile_bp.route("/admin/user/<int:user_id>/message", methods=["POST"])(admin_send_message)
mobile_bp.route("/user/messages", methods=["GET"])(user_get_messages)
