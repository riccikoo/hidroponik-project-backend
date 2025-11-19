import random
import datetime
import threading
import time

from flask import Blueprint, jsonify
from extensions import db
from models.sensor_model import Sensor

test_bp = Blueprint('test_bp', __name__)

SENSOR_RANGES = {
    "dht_temp": (20, 35),
    "dht_humid": (40, 90),
    "ldr": (100, 900),
    "ph": (5.5, 8.5),
    "ec": (1.0, 3.0),
    "ultrasonic": (5, 100)
}

# -------------------------------------------
# FUNCTION UTAMA GENERATE DATA DUMMY
# -------------------------------------------

def insert_dummy_loop(app):
    """Background thread untuk generate data tiap 5 detik."""
    with app.app_context():
        while True:
            for sensor_name, (low, high) in SENSOR_RANGES.items():

                value = round(random.uniform(low, high), 2)

                new_data = Sensor(
                    sensor_name=sensor_name,
                    value=value,
                    timestamp=datetime.datetime.now()
                )

                db.session.add(new_data)
                db.session.commit()

                print(f"[DUMMY] {sensor_name}: {value}")

            time.sleep(5)  # jeda 5 detik


# -------------------------------------------
# ROUTE UNTUK START AUTO GENERATE (OPSIONAL)
# -------------------------------------------

@test_bp.route('/start_dummy', methods=['GET'])
def start_background_dummy():
    """Jalankan background dummy jika mau trigger manual."""
    from flask import current_app

    thread = threading.Thread(target=insert_dummy_loop, args=(current_app._get_current_object(),))
    thread.daemon = True
    thread.start()

    return jsonify({"status": True, "message": "Background dummy generator started"}), 200
