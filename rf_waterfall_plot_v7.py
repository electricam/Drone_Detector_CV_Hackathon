
import os
import time
import csv
import json
import urllib.request
import numpy as np
import matplotlib.pyplot as plt
from rtlsdr import RtlSdr
import threading
import copy
from datetime import datetime

# Helper: Get dynamic Pi location
def get_pi_location():
    try:
        with urllib.request.urlopen("http://ip-api.com/json/") as url:
            data = json.loads(url.read().decode())
            if data['status'] == 'success':
                return float(data['lat']), float(data['lon'])
    except:
        pass
    # fallback (San Francisco)
    return 37.7749, -122.4194

# Helper function: Save snapshots
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

# Helper function: Save KML file
def save_kml(timestamp, lat, lon, freq_mhz, power_db):
    try:
        kml_template = f"""
        <?xml version="1.0" encoding="UTF-8"?>
        <kml xmlns="http://www.opengis.net/kml/2.2">
          <Placemark>
            <name>RF Spike {freq_mhz:.2f} MHz</name>
            <description>Power: {power_db:.2f} dB</description>
            <Point>
              <coordinates>{lon},{lat},0</coordinates>
            </Point>
          </Placemark>
        </kml>
        """
        filename = f"detections/rf_event_{timestamp}.kml"
        with open(filename, 'w') as file:
            file.write(kml_template.strip())
        print(f"🛰️ KML saved: {filename}")
    except Exception as e:
        print(f"❌ Error saving KML: {e}")

# Initialize SDR
sdr = RtlSdr()
sdr.sample_rate = 2.4e6  # Hz
sdr.center_freq = 915e6  # Hz
sdr.gain = 'auto'

# Waterfall buffer
waterfall_depth = 100
waterfall = []

# Set up plot
plt.ion()
fig, ax = plt.subplots()

# Frequency axis setup
freq_axis = np.linspace(sdr.center_freq - sdr.sample_rate/2,
                        sdr.center_freq + sdr.sample_rate/2,
                        1024) / 1e6  # MHz

# Threshold for spike detection
threshold_dB = -40

# Set up CSV logging
csv_filename = "detections/detections_log.csv"
try:
    os.makedirs(os.path.dirname(csv_filename), exist_ok=True)
    if not os.path.exists(csv_filename):
        with open(csv_filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Timestamp", "Latitude", "Longitude", "Frequency_MHz", "Power_dB"])
except Exception as e:
    print(f"❌ Error setting up CSV: {e}")

# Get Pi location once at start
pi_lat, pi_lon = get_pi_location()
print(f"📍 Using Pi location: {pi_lat}, {pi_lon}")

print("\n🎯 Starting tactical RF waterfall scan...")

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

        # Spike detection
        spikes_idx = np.where(downsampled > threshold_dB)[0]
        if len(spikes_idx) > 0:
            timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ")
            dominant_freq = freq_axis[spikes_idx[0]]
            power_detected = downsampled[spikes_idx[0]]

            snapshot_filename = f"detections/event_{timestamp}.png"
            save_snapshot(fig, snapshot_filename)
            save_kml(timestamp, pi_lat, pi_lon, dominant_freq, power_detected)

            # Log to CSV
            try:
                with open(csv_filename, mode='a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow([timestamp, pi_lat, pi_lon, f"{dominant_freq:.3f}", f"{power_detected:.2f}"])
            except Exception as e:
                print(f"❌ Error writing to CSV: {e}")

except KeyboardInterrupt:
    print("\n🛑 Stopping tactical scan...")

finally:
    sdr.close()
    plt.close()