# rf_waterfall_plot_v6.py

import os
import time
import csv
import numpy as np
import matplotlib.pyplot as plt
from rtlsdr import RtlSdr
import threading
import copy
from datetime import datetime

# --- KML Generation Helper ---
def generate_kml(lat, lon, freq_mhz, power_dbm):
    kml_folder = 'kml_detections'
    os.makedirs(kml_folder, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ")
    filename = f"{kml_folder}/rf_event_{timestamp}.kml"

    kml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Placemark>
    <name>📡 RF Spike {freq_mhz:.2f} MHz</name>
    <description>Detected power: {power_dbm:.2f} dBm</description>
    <Style>
      <IconStyle>
        <color>ff0000ff</color>
        <scale>1.2</scale>
        <Icon>
          <href>http://maps.google.com/mapfiles/kml/shapes/target.png</href>
        </Icon>
      </IconStyle>
    </Style>
    <Point>
      <coordinates>{lon},{lat},10</coordinates>
    </Point>
    <TimeStamp>
      <when>{timestamp}</when>
    </TimeStamp>
  </Placemark>
</kml>"""

    with open(filename, 'w') as f:
        f.write(kml_content)
    print(f"✅ KML created: {filename}")

# --- Safe Snapshot Saver ---
def save_snapshot(fig, filename):
    try:
        folder = os.path.dirname(filename)
        os.makedirs(folder, exist_ok=True)
        fig_copy = copy.deepcopy(fig)
        def save_fig():
            fig_copy.savefig(filename)
        threading.Thread(target=save_fig).start()
    except Exception as e:
        print(f"❌ Error saving snapshot: {e}")

# --- Initialize SDR ---
sdr = RtlSdr()
sdr.sample_rate = 2.4e6
sdr.center_freq = 915e6
sdr.gain = 'auto'

# --- Waterfall Setup ---
waterfall_depth = 100
waterfall = []

plt.ion()
fig, ax = plt.subplots()

freq_axis = np.linspace(sdr.center_freq - sdr.sample_rate/2,
                        sdr.center_freq + sdr.sample_rate/2,
                        1024) / 1e6

threshold_dB = -40
csv_filename = "detections/detections_log.csv"

# --- CSV Setup ---
os.makedirs(os.path.dirname(csv_filename), exist_ok=True)
if not os.path.exists(csv_filename):
    with open(csv_filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "Frequency_MHz", "Power_dB"])

print("\n🎯 Starting tactical RF waterfall scan...")

# --- Static Location (placeholder) ---
static_lat = 37.8080  # Example: San Francisco lat
static_lon = -122.4210  # Example: San Francisco lon

frame_ready = False

try:
    while True:
        samples = sdr.read_samples(256*1024)
        power_spectrum = 20 * np.log10(np.abs(np.fft.fftshift(np.fft.fft(samples))))
        downsampled = power_spectrum[::int(len(power_spectrum)/1024)]

        waterfall.append(downsampled)
        if len(waterfall) > waterfall_depth:
            waterfall.pop(0)

        ax.clear()
        ax.imshow(waterfall, aspect='auto', extent=[freq_axis[0], freq_axis[-1], 0, waterfall_depth],
                  origin='lower', cmap='viridis')
        ax.set_title('📡 Tactical RF Waterfall')
        ax.set_xlabel('Frequency (MHz)')
        ax.set_ylabel('Time (scrolling up)')
        ax.set_xlim(900, 930)
        ax.set_ylim(0, waterfall_depth)
        plt.pause(0.05)

        frame_ready = True

        # --- Spike Detection ---
        if frame_ready:
            spikes_idx = np.where(downsampled > threshold_dB)[0]
            if len(spikes_idx) > 0:
                timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
                dominant_freq = freq_axis[spikes_idx[0]]

                snapshot_filename = f"detections/event_{timestamp}.png"
                save_snapshot(fig, snapshot_filename)
                print(f"🚨 Snapshot saved: {snapshot_filename}")

                # Log CSV
                try:
                    with open(csv_filename, mode='a', newline='') as file:
                        writer = csv.writer(file)
                        writer.writerow([timestamp, f"{dominant_freq:.3f}", f"{downsampled[spikes_idx[0]]:.2f}"])
                except Exception as e:
                    print(f"❌ Error writing to CSV: {e}")

                # --- Generate KML! ---
                generate_kml(lat=static_lat, lon=static_lon, freq_mhz=dominant_freq, power_dbm=downsampled[spikes_idx[0]])

except KeyboardInterrupt:
    print("\n🔕 Stopping tactical scan...")

finally:
    sdr.close()
    plt.close()
