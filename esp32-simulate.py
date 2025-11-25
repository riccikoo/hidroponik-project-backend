import time
import json
import random
from paho.mqtt import client as mqtt

BROKER = "broker.hivemq.com"
PORT   = 1883

TOPIC_SENSOR = "wokwi/iot-hidroponik-kel3/test"
TOPIC_CMD    = "wokwi/iot-hidroponik-kel3/cmd"

client_id = "simulator-ayang"

# Status aktuator (simulasi)
actuators = {
    "led": False,
    "pump_ph_up": False,
    "pump_ph_down": False,
    "pump_nutrisi": False
}

client = mqtt.Client(
    client_id=client_id,
    protocol=mqtt.MQTTv5,
    transport="tcp",
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2
)

# ===========================================================
# CALLBACK SAAT CONNECT
# ===========================================================
def on_connect(client, userdata, flags, rc, properties=None):
    print("[SIM CONNECTED] Status:", rc)
    client.subscribe(TOPIC_CMD)
    print(f"[SIM] Subscribed ke: {TOPIC_CMD}")

client.on_connect = on_connect

# ===========================================================
# CALLBACK SAAT PESAN MASUK (AKTUATOR)
# ===========================================================
def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        print("[CMD RECEIVED]", payload)

        for key in actuators:
            if key in payload:
                actuators[key] = payload[key]
                print(f"  -> Aktuator '{key}' sekarang =", actuators[key])

    except Exception as e:
        print("[ERROR PARSE CMD]:", e)

client.on_message = on_message

# ===========================================================
# CONNECT
# ===========================================================
client.connect(BROKER, PORT, 60)
client.loop_start()

print("ESP32 SIMULATOR WITH ACTUATOR CONTROL STARTED...\n")

# ===========================================================
# LOOP KIRIM SENSOR
# ===========================================================
while True:
    data = {
        "temp": round(random.uniform(20, 30), 2),
        "humidity": round(random.uniform(50, 85), 2),
        "ldr": random.randint(200, 900),
        "ec": random.randint(800, 1800),
        "ph": random.randint(0, 10),
        "distance": random.randint(20, 60),
        "actuator_status": actuators
    }

    client.publish(TOPIC_SENSOR, json.dumps(data))
    print("[PUBLISH SENSOR]", data)

    time.sleep(5)
