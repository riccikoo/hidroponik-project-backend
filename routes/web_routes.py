from flask import Blueprint
from controllers.web_controller import (
    splash_page, landing_page, login_page, register_page, dashboard_page, logout, login, profile_page, riwayat_page, export_riwayat_csv
)

web_bp = Blueprint('web_bp', __name__)

# Routing untuk tampilan halaman

web_bp.route('/', methods=['GET'])(splash_page)
web_bp.route('/landing', methods=['GET'])(landing_page)
web_bp.route('/login', methods=['GET'])(login_page)
web_bp.route('/login', methods=['POST'])(login)
web_bp.route('/registrasi', methods=['GET'])(register_page)
web_bp.route('/dashboard', methods=['GET'])(dashboard_page)
web_bp.route('/logout', methods=['GET'])(logout)
web_bp.route('/profile', methods=['GET'])(profile_page)
web_bp.route('/riwayat', methods=['GET'])(riwayat_page)
web_bp.route('/riwayat/export', methods=['GET'])(export_riwayat_csv)