import json
import threading
from paho.mqtt import client as mqtt
from models.sensor_model import Sensor
from extensions import db
from datetime import datetime

# ------------------------
# MQTT CONFIG
# ------------------------
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT   = 1883
MQTT_TOPIC  = "wokwi/iot-hidroponik-kel3/test"

client = mqtt.Client()
client.connected_flag = False


# ------------------------
# CALLBACK: CONNECT
# ------------------------
def on_connect(client, userdata, flags, rc):
    print("[MQTT] Connected with code:", rc)
    client.subscribe(MQTT_TOPIC)
    print(f"[MQTT] Subscribed to: {MQTT_TOPIC}")


# ------------------------
# CALLBACK: MESSAGE
# ------------------------
def on_message(client, userdata, msg):
    """ESP32 → MQTT → Simpan ke Database"""
    try:
        payload = json.loads(msg.payload.decode())
        print("[MQTT RECEIVED]:", payload)

        mapping = {
            "dht_temp": payload.get("temp"),
            "dht_humid": payload.get("humidity"),
            "ldr": payload.get("ldr"),
            "ec": payload.get("ec"),
            "ultrasonic": payload.get("distance")
        }

        for name, value in mapping.items():
            if value is not None:
                row = Sensor(
                    sensor_name=name,
                    value=float(value),
                    timestamp=datetime.utcnow()
                )
                db.session.add(row)

        db.session.commit()
        print("[DB] Saved successfully")

    except Exception as e:
        print("[ERROR MQTT SAVE]:", e)


# ------------------------
# MQTT LOOP THREAD
# ------------------------
def mqtt_loop():
    try:
        print("[MQTT] Loop started...")
        client.loop_forever()
    except Exception as e:
        print("[MQTT LOOP ERROR]:", e)


# ------------------------
# FUNCTION: INIT MQTT
# ------------------------
def init_mqtt():
    """Dipanggil sekali dari app.py"""
    client.on_connect = on_connect
    client.on_message = on_message

    print(f"[MQTT] Connecting to {MQTT_BROKER}:{MQTT_PORT} ...")
    client.connect(MQTT_BROKER, MQTT_PORT, 60)

    # thread supaya Flask tidak ke-block
    thread = threading.Thread(target=mqtt_loop, daemon=True)
    thread.start()

    print("[MQTT] Background MQTT thread started!")
