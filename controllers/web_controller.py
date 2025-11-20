import io
from flask import render_template, session, redirect, url_for, jsonify, request

from extensions import db, bcrypt
from models.user_model import User
from datetime import datetime, timedelta
from validations.user_schema import validate_register, validate_login
from models.sensor_model import Sensor



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

def splash_page():
    return render_template('splash.html')

def profile_page():
    # Cek apakah user sudah login
    if 'user_id' not in session:
        return redirect(url_for('web_bp.login_page'))

    # Ambil user_name dari session
    user_name = session.get('user_name', 'User')

    return render_template('profile.html', user_name=user_name)


def riwayat_page():
    """Halaman riwayat dengan data real dari database"""

    # Cek login
    if 'user_id' not in session:
        return redirect(url_for('web_bp.login_page'))

    user_name = session.get('user_name', 'User')

    # Get filter parameters
    time_range = request.args.get('time_range', 'week')
    sensor_type = request.args.get('sensor_type', 'all')

    now = datetime.now()

    # Tentukan start date filter
    if time_range == 'today':
        start_date = now.replace(hour=0, minute=0, second=0)
    elif time_range == 'yesterday':
        start_date = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0)
    elif time_range == 'month':
        start_date = now - timedelta(days=30)
    else:  # default week
        start_date = now - timedelta(days=7)

    # Query data dari database
    rows = Sensor.query.filter(
        Sensor.timestamp >= start_date
    ).order_by(Sensor.timestamp.desc()).all()

    # ------------------------------
    # 🔄 PIVOT DATA SENSOR PER TIMESTAMP
    # ------------------------------
    grouped = {}

    for row in rows:
        ts = row.timestamp

        if ts not in grouped:
            grouped[ts] = {
                "timestamp": ts,
                "suhu": None,
                "kelembapan": None,
                "ph": None,
                "ec": None,
                "cahaya": None,
                "level_air": None
            }

        if row.sensor_name == "dht_temp":
            grouped[ts]["suhu"] = float(row.value)

        elif row.sensor_name == "dht_humid":
            grouped[ts]["kelembapan"] = float(row.value)

        elif row.sensor_name == "ph":
            grouped[ts]["ph"] = float(row.value)

        elif row.sensor_name == "ec":
            grouped[ts]["ec"] = float(row.value)

        elif row.sensor_name == "ldr":
            grouped[ts]["cahaya"] = float(row.value)

        elif row.sensor_name == "ultrasonic":
            grouped[ts]["level_air"] = float(row.value)

    # jadikan list dan sort DESC
    sensor_data = sorted(grouped.values(), key=lambda x: x["timestamp"], reverse=True)

    # ------------------------------
    # 📊 HITUNG AVERAGE UNTUK STATS
    # ------------------------------
    def avg(values):
        values = [v for v in values if v is not None]
        return sum(values) / len(values) if values else 0

    avg_temp = avg([d["suhu"] for d in sensor_data])
    avg_humidity = avg([d["kelembapan"] for d in sensor_data])
    avg_ph = avg([d["ph"] for d in sensor_data])
    avg_ec = avg([d["ec"] for d in sensor_data])

    # perubahan dibanding kemarin
    yesterday_start = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0)
    yesterday_end = yesterday_start + timedelta(hours=23, minutes=59)

    yesterday_rows = Sensor.query.filter(
        Sensor.timestamp >= yesterday_start,
        Sensor.timestamp <= yesterday_end
    ).all()

    grouped_yesterday = {}
    for row in yesterday_rows:
        ts = row.timestamp
        if ts not in grouped_yesterday:
            grouped_yesterday[ts] = {
                "suhu": None,
                "kelembapan": None
            }
        if row.sensor_name == "dht_temp":
            grouped_yesterday[ts]["suhu"] = float(row.value)
        elif row.sensor_name == "dht_humid":
            grouped_yesterday[ts]["kelembapan"] = float(row.value)

    yesterday_list = list(grouped_yesterday.values())

    yesterday_avg_temp = avg([d["suhu"] for d in yesterday_list])
    yesterday_avg_humidity = avg([d["kelembapan"] for d in yesterday_list])

    temp_change = avg_temp - yesterday_avg_temp
    humidity_change = avg_humidity - yesterday_avg_humidity

    # ------------------------------
    # 🔔 NOTIFIKASI SENSOR
    # ------------------------------
    notifications = []

    if sensor_data:
        latest = sensor_data[0]

        # Suhu
        if latest["suhu"] is not None:
            if latest["suhu"] > 30:
                notifications.append({
                    "type": "danger",
                    "title": "Suhu Terlalu Tinggi!",
                    "message": f"Suhu saat ini {latest['suhu']}°C (maksimum 30°C)",
                    "time_ago": get_time_ago(latest["timestamp"])
                })
            elif latest["suhu"] > 28.5:
                notifications.append({
                    "type": "warning",
                    "title": "Suhu Mendekati Batas",
                    "message": f"Suhu saat ini {latest['suhu']}°C",
                    "time_ago": get_time_ago(latest["timestamp"])
                })

        # pH
        if latest["ph"] is not None:
            if latest["ph"] < 6.0:
                notifications.append({
                    "type": "warning",
                    "title": "pH Terlalu Rendah",
                    "message": f"pH = {latest['ph']}",
                    "time_ago": get_time_ago(latest["timestamp"])
                })
            elif latest["ph"] > 7.0:
                notifications.append({
                    "type": "warning",
                    "title": "pH Terlalu Tinggi",
                    "message": f"pH = {latest['ph']}",
                    "time_ago": get_time_ago(latest["timestamp"])
                })

        # Kelembapan
        if latest["kelembapan"] is not None and latest["kelembapan"] < 60:
            notifications.append({
                "type": "warning",
                "title": "Kelembapan Rendah",
                "message": f"Kelembapan {latest['kelembapan']}%",
                "time_ago": get_time_ago(latest["timestamp"])
            })

        # Level Air
        if latest["level_air"] is not None and latest["level_air"] < 50:
            notifications.append({
                "type": "danger",
                "title": "Level Air Rendah!",
                "message": f"Level air hanya {latest['level_air']}%",
                "time_ago": get_time_ago(latest["timestamp"])
            })

        if not notifications:
            notifications.append({
                "type": "success",
                "title": "Sistem Normal",
                "message": "Semua sensor dalam kondisi baik.",
                "time_ago": get_time_ago(latest["timestamp"])
            })

    return render_template(
        "riwayat.html",
        user_name=user_name,
        sensor_data=sensor_data,
        notifications=notifications,
        avg_temp=avg_temp,
        avg_humidity=avg_humidity,
        avg_ph=avg_ph,
        avg_ec=avg_ec,
        temp_change=temp_change,
        humidity_change=humidity_change
    )


# ======================================================
# ⏱ Helper Function
# ======================================================
def get_time_ago(timestamp):
    now = datetime.now()
    diff = now - timestamp

    if diff.days > 0:
        return f"{diff.days} hari lalu"
    if diff.seconds >= 3600:
        return f"{diff.seconds // 3600} jam lalu"
    if diff.seconds >= 60:
        return f"{diff.seconds // 60} menit lalu"
    return "Baru saja"


# ======================================================
# 📁 EXPORT CSV
# ======================================================
def export_riwayat_csv():
    if 'user_id' not in session:
        return redirect(url_for('web_bp.login_page'))

    rows = Sensor.query.order_by(Sensor.timestamp.desc()).limit(1000).all()

    # pivot lagi
    grouped = {}

    for row in rows:
        ts = row.timestamp
        if ts not in grouped:
            grouped[ts] = {
                "timestamp": ts,
                "suhu": None,
                "kelembapan": None,
                "ph": None,
                "ec": None,
                "cahaya": None,
                "level_air": None
            }

        if row.sensor_name == "dht_temp":
            grouped[ts]["suhu"] = row.value
        elif row.sensor_name == "dht_humid":
            grouped[ts]["kelembapan"] = row.value
        elif row.sensor_name == "ph":
            grouped[ts]["ph"] = row.value
        elif row.sensor_name == "ec":
            grouped[ts]["ec"] = row.value
        elif row.sensor_name == "ldr":
            grouped[ts]["cahaya"] = row.value
        elif row.sensor_name == "ultrasonic":
            grouped[ts]["level_air"] = row.value

    data = sorted(grouped.values(), key=lambda x: x["timestamp"], reverse=True)

    # Buat CSV
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(['Tanggal', 'Waktu', 'Suhu (°C)', 'Kelembapan (%)',
                     'pH', 'EC', 'Cahaya', 'Level Air'])

    for d in data:
        writer.writerow([
            d["timestamp"].strftime('%Y-%m-%d'),
            d["timestamp"].strftime('%H:%M:%S'),
            d["suhu"],
            d["kelembapan"],
            d["ph"],
            d["ec"],
            d["cahaya"],
            d["level_air"]
        ])

    output.seek(0)

    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f"riwayat_sensor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    )
