# rf_waterfall_plot_v9_refreshed.py

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

# Default location fallback
default_lat = 37.823
default_lon = -122.441

# Directories
DETECTIONS_FOLDER = "detections"
os.makedirs(DETECTIONS_FOLDER, exist_ok=True)
csv_filename = os.path.join(DETECTIONS_FOLDER, "detections_log.csv")

# ===== Helper Functions =====

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

def upload_kml_file(local_file_path):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(scp_server, username=scp_username, password=scp_password)

        sftp = ssh.open_sftp()
        remote_path = os.path.join(scp_remote_folder, os.path.basename(local_file_path))
        sftp.put(local_file_path, remote_path)

        sftp.close()
        ssh.close()

        print(f"✅ SCP Upload Successful: {os.path.basename(local_file_path)}")

    except Exception as e:
        print(f"❌ SCP Upload Failed: {e}")

def generate_kml(filename, lat, lon, freq_mhz, power_dbm):
    kml_content = f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<kml xmlns=\"http://www.opengis.net/kml/2.2\">
  <Placemark>
    <name>RF Spike {freq_mhz:.2f} MHz</name>
    <description>Power: {power_dbm:.2f} dBm</description>
    <Point>
      <coordinates>{lon},{lat},0</coordinates>
    </Point>
  </Placemark>
</kml>"""
    with open(filename, 'w') as f:
        f.write(kml_content)

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

# Create CSV if missing
if not os.path.exists(csv_filename):
    with open(csv_filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "Frequency_MHz", "Power_dB"])

print("\n🎯 Starting tactical RF waterfall scan...")

# ===== Main Loop =====
try:
    while True:
        samples = sdr.read_samples(256*1024)
        power_spectrum = 20 * np.log10(np.abs(np.fft.fftshift(np.fft.fft(samples))))
        downsampled = power_spectrum[::int(len(power_spectrum)/1024)]

        waterfall.append(downsampled)
        if len(waterfall) > WATERFALL_DEPTH:
            waterfall.pop(0)

        ax.clear()
        ax.imshow(waterfall, aspect='auto', extent=[freq_axis[0], freq_axis[-1], 0, WATERFALL_DEPTH],
                  origin='lower', cmap='viridis')
        ax.set_title('📡 Tactical RF Waterfall')
        ax.set_xlabel('Frequency (MHz)')
        ax.set_ylabel('Time (scrolling up)')
        ax.set_xlim(900, 930)
        ax.set_ylim(0, WATERFALL_DEPTH)
        plt.pause(0.05)

        # Spike detection
        spikes_idx = np.where(downsampled > THRESHOLD_DB)[0]
        if len(spikes_idx) > 0:
            timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ")
            dominant_freq = freq_axis[spikes_idx[0]]
            power_db = downsampled[spikes_idx[0]]

            snapshot_filename = os.path.join(DETECTIONS_FOLDER, f"event_{timestamp}.png")
            save_snapshot(fig, snapshot_filename)
            print(f"🚨 Snapshot + KML saved for RF Spike {dominant_freq:.2f} MHz!")

            try:
                with open(csv_filename, mode='a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow([timestamp, f"{dominant_freq:.3f}", f"{power_db:.2f}"])
            except Exception as e:
                print(f"❌ Error writing to CSV: {e}")

            # Generate KML
            kml_filename = os.path.join(DETECTIONS_FOLDER, f"rf_event_{timestamp}.kml")
            generate_kml(kml_filename, default_lat, default_lon, dominant_freq, power_db)

            # Upload KML to WebTAK
            upload_kml_file(kml_filename)

except KeyboardInterrupt:
    print("\n🛑 Stopping tactical scan...")

finally:
    sdr.close()
    plt.close()
