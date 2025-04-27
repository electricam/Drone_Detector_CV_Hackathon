# generate_kml.py

import os
from datetime import datetime

# Folder to save KML files
DETECTIONS_FOLDER = 'kml_detections'
os.makedirs(DETECTIONS_FOLDER, exist_ok=True)

# Sample detection info
lat = 37.8080        # Example latitude (San Francisco)
lon = -122.4210      # Example longitude
freq_mhz = 913.8     # Frequency in MHz
power_dbm = 23.5     # Power in dBm

# Timestamp formatting
now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
filename = f"{DETECTIONS_FOLDER}/rf_event_{now.replace(':', '-')}.kml"

# KML structure
kml_template = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Placemark>
    <name>📡 RF Spike {freq_mhz:.2f} MHz</name>
    <description>Detected power: {power_dbm:.2f} dBm</description>
    <Point>
      <coordinates>{lon},{lat},10</coordinates>
    </Point>
    <TimeStamp>
      <when>{now}</when>
    </TimeStamp>
  </Placemark>
</kml>
"""

# Save KML file
with open(filename, 'w') as f:
    f.write(kml_template)

print(f"✅ KML file created: {filename}")
