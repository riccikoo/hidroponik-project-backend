from flask import render_template, session, redirect, url_for, jsonify, request

from extensions import db, bcrypt
from models.user_model import User
from datetime import datetime
from validations.user_schema import validate_register, validate_login


def register():
    errors = validate_register(request.json)
    if errors:
        return jsonify({"status": False, "errors": errors}), 422

    data = request.json
    hashed_pw = bcrypt.generate_password_hash(data['password']).decode('utf-8')

    user = User(
        name=data['name'],
        email=data['email'],
        password=hashed_pw,
        role='user',
        status='inactive',          # harus disetujui admin
        timestamp=datetime.utcnow()
    )

    db.session.add(user)
    db.session.commit()

    return jsonify({
        "status": True,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "status": user.status,
            "timestamp": user.timestamp.isoformat()
        },
        "message": "User registered successfully. Wait for admin approval."
    }), 201



def login():
    errors = validate_login(request.json)
    if errors:
        return jsonify({"status": False, "errors": errors}), 422

    data = request.json
    user = User.query.filter_by(email=data['email']).first()

    # cek email
    if not user:
        return jsonify({"status": False, "message": "Invalid credentials"}), 401

    # cek status
    if user.status != 'active':
        return jsonify({
            "status": False,
            "message": "Account is inactive. Please contact admin."
        }), 403

    # cek password
    if not bcrypt.check_password_hash(user.password, data['password']):
        return jsonify({"status": False, "message": "Invalid credentials"}), 401

    # ✅ set session
    session['user_id'] = user.id
    session['user_name'] = user.name
    session['user_email'] = user.email
    session['user_role'] = user.role
    session['user_status'] = user.status

    return jsonify({
        "status": True,
        "message": "Login successful",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "status": user.status,
            "timestamp": user.timestamp.isoformat()
        }
    }), 200

def landing_page():
    return render_template('landing.html')

def login_page():
    # kalau user sudah login → langsung ke dashboard
    if 'user_id' in session:
        return redirect(url_for('web_bp.dashboard_page'))
    return render_template('login.html')

def register_page():
    # kalau user sudah login → langsung ke dashboard
    if 'user_id' in session:
        return redirect(url_for('web_bp.dashboard_page'))
    return render_template('registrasi.html')

def dashboard_page():
    # pastikan user login
    if 'user_id' not in session:
        return redirect(url_for('web_bp.login_page'))

    user_name = session.get('user_name', 'User')
    return render_template('dashboard.html', user_name=user_name)

def logout():
    session.clear()
    return redirect(url_for('web_bp.login_page'))