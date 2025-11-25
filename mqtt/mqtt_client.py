import json
import threading
from paho.mqtt import client as mqtt
from models.sensor_model import Sensor
from extensions import db
from datetime import datetime
from flask import request

MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC_SENSOR = "wokwi/iot-hidroponik-kel3/test"
MQTT_TOPIC_ACTUATOR = "wokwi/iot-hidroponik-kel3/cmd"

# ======================
# MQTT CLIENT (AMAN)
# ======================
client = mqtt.Client(
    protocol=mqtt.MQTTv5,
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2
)

# ======================
# KIRIM PERINTAH AKTUATOR
# ======================
def send_actuator_command(name, state):
    payload = {
        name: True if state == "ON" else False
    }

    try:
        client.publish(MQTT_TOPIC_ACTUATOR, json.dumps(payload))
        print("[ACTUATOR PUBLISH]:", payload)
        return True
    except Exception as e:
        print("[ACTUATOR ERROR]:", e)
        return False

# ======================
# MQTT CONNECT
# ======================
def on_connect(client, userdata, flags, rc, properties=None):
    print("[MQTT] Connected with code:", rc)
    client.subscribe(MQTT_TOPIC_SENSOR)
    print(f"[MQTT] Subscribed to: {MQTT_TOPIC_SENSOR}")

# ======================
# MQTT MESSAGE HANDLER
# ======================
def on_message(client, userdata, msg):
    payload = json.loads(msg.payload.decode())
    print("[MQTT RECEIVED]:", payload)

    app = userdata.get("app")
    if app is None:
        print("[FATAL] userdata['app'] = None, tidak dapat akses db!")
        return

    mapping = {
        "dht_temp": payload.get("temp"),
        "dht_humid": payload.get("humidity"),
        "ldr": payload.get("ldr"),
        "ph": payload.get("ph"),
        "ec": payload.get("ec"),
        "ultrasonic": payload.get("distance")
    }

    try:
        with app.app_context():
            for name, value in mapping.items():
                if value is not None:
                    row = Sensor(
                        sensor_name=name,
                        value=float(value),
                        timestamp=datetime.utcnow()
                    )
                    db.session.add(row)

            db.session.commit()
            print("[DB] Saved successfully!")

    except Exception as e:
        print("[ERROR MQTT SAVE]:", e)

# ======================
# MQTT BACKGROUND LOOP
# ======================
def mqtt_loop():
    client.loop_forever()

# ======================
# INIT MQTT
# ======================
def init_mqtt(app):
    client.user_data_set({"app": app})
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT, 60)

    thread = threading.Thread(target=mqtt_loop, daemon=True)
    thread.start()

    print("[MQTT] Background thread started")

# ======================
# CONTROLLER AKTUATOR
# ======================
def control_actuator():
    data = request.get_json()

    name = data.get("name")
    state = data.get("state")

    valid_actuators = ["pump_ph_up", "pump_ph_down", "pump_nutrisi", "led"]

    if name not in valid_actuators:
        return {"error": "Aktuator tidak dikenal"}, 400

    if state not in ["ON", "OFF"]:
        return {"error": "State hanya boleh ON / OFF"}, 400

    success = send_actuator_command(name, state)

    if success:
        return {"message": f"Perintah {name} → {state} berhasil dikirim"}, 200

    return {"error": "Gagal mengirim perintah"}, 500
