import time
import json
import random
from paho.mqtt import client as mqtt

BROKER = "broker.hivemq.com"
PORT   = 1883
TOPIC  = "wokwi/iot-hidroponik-kel3/test"

client_id = "simulator-ayang"

# FIX: paho-mqtt v2.x requires ENUM, not int!
client = mqtt.Client(
    client_id=client_id,
    protocol=mqtt.MQTTv5,
    transport="tcp",
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2
)

def on_connect(client, userdata, flags, rc, properties=None):
    print("[SIM CONNECTED] Status:", rc)

client.on_connect = on_connect

client.connect(BROKER, PORT, 60)
client.loop_start()

print("ESP32 SIMULATOR STARTED...\n")

while True:
    data = {
        "temp": round(random.uniform(20, 30), 2),
        "humidity": round(random.uniform(50, 85), 2),
        "ldr": random.randint(200, 900),
        "ec": random.randint(800, 1800),
        "ph": random.randint(0, 10),
        "distance": random.randint(20, 60)
    }

    client.publish(TOPIC, json.dumps(data))
    print("[PUBLISH]", data)

    time.sleep(2)
