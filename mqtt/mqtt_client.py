import json
import threading
from paho.mqtt import client as mqtt
from models.sensor_model import Sensor
from extensions import db
from datetime import datetime

MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT   = 1883
MQTT_TOPIC  = "wokwi/iot-hidroponik-kel3/test"

client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    print("[MQTT] Connected with code:", rc)
    client.subscribe(MQTT_TOPIC)
    print(f"[MQTT] Subscribed to: {MQTT_TOPIC}")


def on_message(client, userdata, msg):
    payload = json.loads(msg.payload.decode())
    print("[MQTT RECEIVED]:", payload)

    # Ambil Flask app dari userdata
    app = userdata.get("app")
    if app is None:
        print("[FATAL] userdata['app'] = None → Flask app tidak diterima")
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
        # HARUS MASUK APP CONTEXT
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


def mqtt_loop():
    print("[MQTT] Loop started...")
    client.loop_forever()


def init_mqtt(app):
    print("[MQTT] Initializing...")

    # KIRIM FLASK APP KE MQTT USERDATA
    client.user_data_set({"app": app})

    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT, 60)

    # Jalankan dalam thread supaya Flask tidak ke-block
    thread = threading.Thread(target=mqtt_loop, daemon=True)
    thread.start()

    print("[MQTT] Background MQTT thread started!")
