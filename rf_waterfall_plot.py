from rtlsdr import RtlSdr
import matplotlib.pyplot as plt
import numpy as np
import time

# Initialize SDR
sdr = RtlSdr()

# SDR Settings
sdr.sample_rate = 2.4e6  # Hz
sdr.center_freq = 915e6  # Hz
sdr.gain = 'auto'

# Waterfall buffer
waterfall_depth = 100  # How many lines deep the waterfall will be
waterfall = []

plt.ion()
fig, ax = plt.subplots()

# Frequency axis setup
freq_axis = np.linspace(sdr.center_freq - sdr.sample_rate/2,
                        sdr.center_freq + sdr.sample_rate/2,
                        1024) / 1e6  # MHz

try:
    print("🎯 Starting waterfall RF scan...")
    while True:
        samples = sdr.read_samples(256*1024)
        power_spectrum = 20 * np.log10(np.abs(np.fft.fftshift(np.fft.fft(samples))))
        downsampled = power_spectrum[::int(len(power_spectrum)/1024)]  # Downsample to 1024 bins

        waterfall.append(downsampled)
        if len(waterfall) > waterfall_depth:
            waterfall.pop(0)  # Keep waterfall at set depth

        ax.clear()
        ax.imshow(waterfall, aspect='auto', extent=[freq_axis[0], freq_axis[-1], 0, waterfall_depth],
                  origin='lower', cmap='viridis')
        ax.set_title('📡 RF Waterfall (Spectrogram)')
        ax.set_xlabel('Frequency (MHz)')
        ax.set_ylabel('Time (scrolling up)')
        ax.set_ylim(0, waterfall_depth)
        ax.set_xlim(900, 930)
        plt.pause(0.05)

except KeyboardInterrupt:
    print("\n🛑 Stopping waterfall...")
finally:
    sdr.close()
    plt.close()
