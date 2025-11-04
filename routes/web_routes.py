from flask import Blueprint
from controllers.web_controller import (
    landing_page, login_page, register_page, dashboard_page, logout, login
)

web_bp = Blueprint('web_bp', __name__)

# Routing untuk tampilan halaman
web_bp.route('/', methods=['GET'])(landing_page)
web_bp.route('/login', methods=['GET'])(login_page)
web_bp.route('/login', methods=['POST'])(login)
web_bp.route('/register', methods=['GET'])(register_page)
web_bp.route('/dashboard', methods=['GET'])(dashboard_page)
web_bp.route('/logout', methods=['GET'])(logout)
