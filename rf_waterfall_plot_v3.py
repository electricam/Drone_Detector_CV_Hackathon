import os
import time
import csv
import numpy as np
import matplotlib.pyplot as plt
from rtlsdr import RtlSdr
import threading
import copy

# Helper function to safely save snapshots
def save_snapshot(fig, filename):
    os.makedirs(os.path.dirname(filename), exist_ok=True)    
    fig_copy = copy.deepcopy(fig)
    def save_fig():
        fig_copy.savefig(filename)
    threading.Thread(target=save_fig).start()

# Initialize SDR
sdr = RtlSdr()
sdr.sample_rate = 2.4e6  # Hz
sdr.center_freq = 915e6  # Hz (adjust if needed)
sdr.gain = 'auto'

# Create output folders if they don't exist
os.makedirs('detections', exist_ok=True)

# Waterfall buffer
waterfall_depth = 100
waterfall = []

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
if not os.path.exists(csv_filename):
    with open(csv_filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "Frequency_MHz", "Power_dB"])

print("🎯 Starting tactical RF waterfall scan...")
frame_ready = False  # New flag to track if plot is drawn at least once

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

        frame_ready = True  # ✅ After first frame is drawn, allow saving

        # Detect strong spikes and save if triggered
        if frame_ready:
            spikes_idx = np.where(downsampled > threshold_dB)[0]
            if len(spikes_idx) > 0:
                timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
                dominant_freq = freq_axis[spikes_idx[0]]

                # Save snapshot using background thread
                snapshot_filename = f"detections/event_{timestamp}.png"
                save_snapshot(fig, snapshot_filename)
                print(f"🚨 Snapshot saved: {snapshot_filename}")

                # Log to CSV
                with open(csv_filename, mode='a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow([timestamp, f"{dominant_freq:.3f}", f"{downsampled[spikes_idx[0]]:.2f}"])

except KeyboardInterrupt:
    print("\n🛑 Stopping tactical scan...")
finally:
    sdr.close()
    plt.close()
