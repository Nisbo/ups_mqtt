# ups_mqtt

`ups_mqtt` ist ein kleines Python-Skript, das die Statusinformationen einer **an eine Synology NAS angeschlossenen USV** (z. B. über USB) abfragt und über **MQTT** an ein Smart-Home-System wie **Home Assistant** überträgt.

Das Skript läuft in einem **Docker-Container** direkt auf der Synology (oder einem anderen Docker-fähigen Gerät) und sendet regelmäßig die Daten der USV über das MQTT-Protokoll.

---

## 🧩 Voraussetzungen

- Eine Synology NAS mit:
  - Docker installiert
  - Einer über USB angeschlossenen und unterstützten USV
  - Dem aktivierten **UPS-Server** (`Systemsteuerung > Hardware & Energie > USV`)
- Ein MQTT-Broker im Netzwerk (z. B. Mosquitto)
- Optional: Home Assistant zur Anzeige der Werte

---

## 🛠️ Einrichtung (zum "Selberbauen") --> Fertiges Image kommt später mal (kann hier keine tar Dateien hochladen)

Auf einem Gerät mit Docker (z. B. Synology NAS oder Debian/Ubuntu Server) folgende Schritte ausführen:

### 📁 Projektstruktur erstellen
Wer nano nicht installiert hat, kann auch vi oder den Editor seiner Wahl nutzen.
Installation von nano auf einer Synology: https://think.unblog.ch/nano-auf-synology-nas-installieren/

Den Inhalt für die 3 Dateien die ihr gleich erstellt, findet ihr hier im Repository.

```bash
sudo mkdir ups_mqtt
cd ups_mqtt

sudo nano ups_mqtt.py         # Python-Skript (siehe Code im Repository)
sudo nano Dockerfile          # Dockerfile zum Erstellen des Containers
sudo nano requirements.txt    # Python-Abhängigkeiten
```

### 🐳 Docker-Image bauen

```bash
sudo docker build -t ups_mqtt .
```

Optional: Für spätere Wiederverwendung exportieren:

```bash
sudo docker save -o ups_mqtt_image.tar ups_mqtt
```

---

## ⚙️ Konfigurierbare Umgebungsvariablen

| Variable              | Beschreibung                                                                 | Standardwert              |
|-----------------------|------------------------------------------------------------------------------|---------------------------|
| `MQTT_BROKER`         | IP-Adresse oder Hostname des MQTT-Brokers                                    | `192.168.178.27`          |
| `MQTT_PORT`           | Port des MQTT-Brokers                                                        | `1883`                    |
| `MQTT_USER`           | *(Optional)* Benutzername für den MQTT-Broker                                | *(leer)*                  |
| `MQTT_PASSWORD`       | *(Optional)* Passwort für den MQTT-Broker                                    | *(leer)*                  |
| `MQTT_TOPIC_BASE`     | Basis-Topic für MQTT-Nachrichten                                             | `home/ups`                |
| `UPS_NAME`            | UPS-Name (muss mit dem Namen im UPS-Server übereinstimmen)                   | `ups`                     |
| `UPS_HOST`            | Hostname/IP des UPS-Servers                                                  | `localhost`               |
| `POLL_INTERVAL`       | Abfrageintervall für wichtige Variablen (in Sekunden)                        | `1`                       |
| `FULL_UPDATE_INTERVAL`| Intervall für das Senden **aller** Variablen (in Sekunden)                   | `30`                      |
| `IMPORTANT_VARS`      | Kommagetrennte Liste wichtiger Variablen, die häufiger gesendet werden sollen| `battery.runtime,ups.status` |
'POLL_INTERVAL' - hier werten nur Werte gesendet, wenn sich diese auch geändert haben
'FULL_UPDATE_INTERVAL' - hier werden immer alle Werte gesendet
---

## ▶️ Container starten (über die Synology GUI)

Alternativ zur Kommandozeile (weiter unten beschrieben) kannst du den Container auch direkt über die Synology-Oberfläche starten:

1. Öffne das **Docker-Paketzentrum** auf deiner Synology NAS.
2. Gehe zu **"Image"** und lade das zuvor erstellte Image hoch (`ups_mqtt_image.tar`), falls noch nicht vorhanden:
   - Klicke auf **"Importieren"** oder **"Hinzufügen"**, um das `.tar`-Image auszuwählen.
3. Wechsle zu **"Container"** und klicke auf **"Erstellen"**:
   - Wähle das `ups_mqtt`-Image aus.
   - Vergib einen Namen, z. B. `ups_mqtt`.

### 🔧 Einstellungen

- Container im Host Netzwerk erstellen
- ![grafik](https://github.com/user-attachments/assets/dc2c0b89-4985-4548-98da-a650f5b97d85)

- **Erweiterte Einstellungen aktivieren**
  - Aktiviere **"Automatisch neu starten"**.
  - Unter **"Umgebungsvariablen"** füge die folgenden (angepassten) Schlüssel/Werte hinzu:

    | Name                 | Wert (Beispiel)              |
    |----------------------|------------------------------|
    | `MQTT_BROKER`        | `192.168.178.27`             |
    | `MQTT_PORT`          | `1883`                       |
    | `MQTT_USER`          | `dein_benutzername`          |
    | `MQTT_PASSWORD`      | `dein_passwort`              |
    | `UPS_NAME`           | `ups`                        |
    | `UPS_HOST`           | `localhost`                  |
    | `MQTT_TOPIC_BASE`    | `home/ups`                   |
    | `POLL_INTERVAL`      | `2`                          |
    | `FULL_UPDATE_INTERVAL` | `30`                       |
    | `IMPORTANT_VARS`     | `battery.runtime,ups.status` |
    Beispiel-Screenshot. Ich nutze einen anderen MQTT Port und keine Login-Daten, also nicht verwirren lassen.
    ![grafik](https://github.com/user-attachments/assets/fe8c8510-0e45-4d60-8084-5b0f4ef4da8e)


4. Klicke auf **"Übernehmen"** und starte den Container.

Nach dem Start beginnt das Skript automatisch mit der Abfrage der USV-Daten und sendet sie über MQTT.

---



## ▶️ Container starten (von der Shell zum testen)

```bash
sudo docker run -d \
  --name ups_mqtt \
  --restart unless-stopped \
  -e MQTT_BROKER=192.168.178.27 \
  -e MQTT_PORT=1884 \
  -e MQTT_USER=benutzername \
  -e MQTT_PASSWORD=passwort \
  -e UPS_NAME=ups \
  -e UPS_HOST=localhost \
  -e MQTT_TOPIC_BASE=home/ups \
  -e POLL_INTERVAL=2 \
  -e FULL_UPDATE_INTERVAL=30 \
  -e IMPORTANT_VARS="battery.runtime,ups.status" \
  ups_mqtt
```

---

## 🏡 Home Assistant MQTT Discovery

Beim ersten Start sendet das Skript automatisch MQTT Discovery-Payloads für Home Assistant an Topics wie:

```
homeassistant/sensor/ups_battery_runtime/config
homeassistant/sensor/ups_ups_status/config
```

Damit Home Assistant die Sensoren korrekt erkennt, muss MQTT Discovery aktiviert sein.

Die Sensordaten werden regelmäßig an Topics unterhalb von `MQTT_TOPIC_BASE` gesendet, z. B.:

```
home/ups/battery.runtime
home/ups/ups.status
```

---

