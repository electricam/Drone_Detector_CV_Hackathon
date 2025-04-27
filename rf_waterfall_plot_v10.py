# rf_waterfall_plot_v10.py

import os
import time
import csv
import numpy as np
import matplotlib.pyplot as plt
from rtlsdr import RtlSdr
import threading
import copy
import paramiko
from datetime import datetime, timedelta

# ===== Settings =====
CENTER_FREQ = 915e6
SAMPLE_RATE = 2.4e6
GAIN = 'auto'
WATERFALL_DEPTH = 100
THRESHOLD_DB = -40

# KML Upload settings
scp_server = "134.199.213.125"
scp_username = "sk123"
scp_password = "9uBQxP@fPsV5#D0p#k2BrJ#gdrK3QrcM4%DuYKvM!8w"
scp_remote_folder = "/home/sk123/uploads/"

# Default fallback location
default_lat = 37.823
default_lon = -122.441

# Folders
DETECTIONS_FOLDER = "detections"
os.makedirs(DETECTIONS_FOLDER, exist_ok=True)
csv_filename = os.path.join(DETECTIONS_FOLDER, "detections_log.csv")

# ===== Helper Functions =====

def save_snapshot(fig, filename):
    try:
        fig_copy = copy.deepcopy(fig)
        def _save():
            fig_copy.savefig(filename)
        threading.Thread(target=_save).start()
    except Exception as e:
        print(f"\u274c Error saving snapshot: {e}")

def generate_kml(filepath, lat, lon, freq_mhz, power_dbm):
    kml_data = f'''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Placemark>
    <name>RF Spike {freq_mhz:.2f} MHz</name>
    <description>Power: {power_dbm:.2f} dBm</description>
    <Point>
      <coordinates>{lon},{lat},0</coordinates>
    </Point>
  </Placemark>
</kml>'''
    with open(filepath, 'w') as f:
        f.write(kml_data)

def upload_kml_file(filepath):
    try:
        if not os.path.exists(filepath):
            print(f"\u274c No file to upload: {filepath}")
            return
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(scp_server, username=scp_username, password=scp_password)

        sftp = ssh.open_sftp()
        remote_path = os.path.join(scp_remote_folder, os.path.basename(filepath))
        sftp.put(filepath, remote_path)

        sftp.close()
        ssh.close()
        print(f"\u2705 SCP Upload Successful: {os.path.basename(filepath)}")
    except Exception as e:
        print(f"\u274c SCP Upload Failed: {e}")

# ===== Initialize SDR =====
sdr = RtlSdr()
sdr.sample_rate = SAMPLE_RATE
sdr.center_freq = CENTER_FREQ
sdr.gain = GAIN

# Waterfall data
waterfall = []

# Plotting setup
plt.ion()
fig, ax = plt.subplots()

freq_axis = np.linspace(
    sdr.center_freq - sdr.sample_rate / 2,
    sdr.center_freq + sdr.sample_rate / 2,
    1024
) / 1e6  # MHz

# Initialize CSV if needed
if not os.path.exists(csv_filename):
    with open(csv_filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Timestamp", "Frequency_MHz", "Power_dBm"])

print("\n\ud83c\udfaf Starting tactical RF waterfall scan...")

# ===== Main Loop =====
try:
    while True:
        samples = sdr.read_samples(256*1024)
        spectrum = 20 * np.log10(np.abs(np.fft.fftshift(np.fft.fft(samples))))
        downsampled = spectrum[::int(len(spectrum)/1024)]

        waterfall.append(downsampled)
        if len(waterfall) > WATERFALL_DEPTH:
            waterfall.pop(0)

        ax.clear()
        ax.imshow(waterfall, aspect='auto', extent=[freq_axis[0], freq_axis[-1], 0, WATERFALL_DEPTH],
                  origin='lower', cmap='viridis')
        ax.set_title('\ud83d\udce1 Tactical RF Waterfall')
        ax.set_xlabel('Frequency (MHz)')
        ax.set_ylabel('Time (scrolling up)')
        ax.set_xlim(900, 930)
        ax.set_ylim(0, WATERFALL_DEPTH)
        plt.pause(0.05)

        spikes = np.where(downsampled > THRESHOLD_DB)[0]
        if len(spikes) > 0:
            timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ")
            freq_mhz = freq_axis[spikes[0]]
            power_dbm = downsampled[spikes[0]]

            png_path = os.path.join(DETECTIONS_FOLDER, f"event_{timestamp}.png")
            kml_path = os.path.join(DETECTIONS_FOLDER, f"rf_event_{timestamp}.kml")

            save_snapshot(fig, png_path)
            generate_kml(kml_path, default_lat, default_lon, freq_mhz, power_dbm)
            upload_kml_file(kml_path)

            print(f"\ud83d\udea8 Detection saved: {freq_mhz:.2f} MHz!")

            with open(csv_filename, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([timestamp, f"{freq_mhz:.3f}", f"{power_dbm:.2f}"])

except KeyboardInterrupt:
    print("\n\ud83d\uded1 Stopping tactical scan...")

finally:
    sdr.close()
    plt.close()
