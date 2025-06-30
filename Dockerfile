FROM python:3.11-slim

# Arbeitsverzeichnis im Container
WORKDIR /app

# System-Tools installieren, ups client wird für 'upsc' benötigt
RUN apt-get update && apt-get install -y \
    nut-client \
    && rm -rf /var/lib/apt/lists/*

# Kopiere requirements und installiere Python Pakete
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Kopiere das Script in den Container
COPY ups_mqtt.py ups_mqtt.py

# Script beim Containerstart ausführen
CMD ["python", "ups_mqtt.py"]
