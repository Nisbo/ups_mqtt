  GNU nano 8.3                                                                                                                                                           ups_mqtt.py                                                                                                                                                                      
import os
import subprocess
import time
import json
import paho.mqtt.client as mqtt

# === Konfiguration über Umgebungsvariablen mit Default-Werten ===
MQTT_BROKER = os.getenv("MQTT_BROKER", "192.168.178.27")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USER = os.getenv("MQTT_USER", "")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")
MQTT_TOPIC_BASE = os.getenv("MQTT_TOPIC_BASE", "home/ups")
UPS_NAME = os.getenv("UPS_NAME", "ups")
UPS_HOST = os.getenv("UPS_HOST", "localhost")

# Intervalle in Sekunden
POLL_INTERVAL = float(os.getenv("POLL_INTERVAL", "1"))          # Intervall für wichtige Variablen (Sekunden)
FULL_UPDATE_INTERVAL = float(os.getenv("FULL_UPDATE_INTERVAL", "30"))  # Intervall für alle Variablen (Sekunden)

# Wichtige Variablen als kommaseparierte Liste (z.B. "battery.runtime,ups.status")
IMPORTANT_VARS = os.getenv("IMPORTANT_VARS", "battery.runtime,ups.status")
IMPORTANT_VARS = [v.strip() for v in IMPORTANT_VARS.split(",") if v.strip()]

# MQTT Client Setup
client = mqtt.Client()

# Authentifizierung (nur setzen, wenn USER vorhanden)
if MQTT_USER:
    client.username_pw_set(MQTT_USER, MQTT_PASSWORD)

client.connect(MQTT_BROKER, MQTT_PORT, 60)

# Mapping für Home Assistant (kann erweitert werden)
DEVICE_CLASS_MAP = {
    "battery.charge": ("%", "battery"),
    "battery.runtime": ("s", "duration"),
    "input.voltage": ("V", "voltage"),
    "output.voltage": ("V", "voltage"),
    "input.frequency": ("Hz", None),
    "battery.voltage": ("V", "voltage"),
    "ups.load": ("%", "power_factor"),
    "ups.status": (None, None),
    "ups.temperature": ("°C", "temperature"),
}

def get_ups_data():
    try:
        result = subprocess.run(['upsc', f'{UPS_NAME}@{UPS_HOST}'], capture_output=True, text=True, timeout=5)

        if result.returncode != 0:
            print("Fehler beim Abfragen der UPS:", result.stderr.strip())
            return None
        data = {}
        for line in result.stdout.splitlines():
            if ':' in line:
                key, val = line.split(':', 1)
                data[key.strip()] = val.strip()
        return data
    except Exception as e:
        print("Exception beim Auslesen der UPS:", e)
        return None

def publish_discovery_config(data):
    for key in data.keys():
        sanitized_key = key.replace('.', '_').lower()
        discovery_topic = f"homeassistant/sensor/ups_{sanitized_key}/config"
        state_topic = f"{MQTT_TOPIC_BASE}/{key}"
        unit, device_class = DEVICE_CLASS_MAP.get(key, (None, None))

        payload = {
            "name": f"UPS {key}",
            "state_topic": state_topic,
            "unique_id": f"ups_{sanitized_key}",
            "device": {
                "identifiers": ["ups_synology"],
                "name": "Synology UPS",
                "manufacturer": "EATON",
                "model": "3S 850"
            }
        }

        if unit:
            payload["unit_of_measurement"] = unit
        if device_class:
            payload["device_class"] = device_class

        client.publish(discovery_topic, json.dumps(payload), retain=True)
        print(f"Discovery-Konfiguration gesendet: {discovery_topic}")

def publish_ups_data(data, last_sent, force=False):
    """Publish data via MQTT.
       Wenn force=True, werden alle Werte gesendet,
       sonst nur geänderte."""
    for key, value in data.items():
        if force or last_sent.get(key) != value:
            topic = f"{MQTT_TOPIC_BASE}/{key}"
            client.publish(topic, value)
            last_sent[key] = value
            print(f"MQTT Publish ({'force' if force else 'change'}): {topic} -> {value}")
    return last_sent

def main():
    first_run = True
    last_sent = {}
    last_full_update = 0

    while True:
        ups_data = get_ups_data()
        if ups_data:
            now = time.time()

            if first_run:
                publish_discovery_config(ups_data)
                first_run = False

            # Wichtige Variablen sofort senden, wenn geändert
            important_data = {k: v for k, v in ups_data.items() if k in IMPORTANT_VARS}
            last_sent = publish_ups_data(important_data, last_sent)

            # Alle Variablen nur alle FULL_UPDATE_INTERVAL Sekunden senden (erzwingen)
            if now - last_full_update > FULL_UPDATE_INTERVAL:
                last_sent = publish_ups_data(ups_data, last_sent, force=True)
                last_full_update = now

        else:
            print("Keine Daten erhalten.")

        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Script beendet.")
        client.disconnect()
