from rtlsdr import RtlSdr
import matplotlib.pyplot as plt
import numpy as np
import time

# Initialize SDR
sdr = RtlSdr()

# SDR Settings
sdr.sample_rate = 2.4e6  # Hz
sdr.center_freq = 915e6  # 915 MHz (adjust as needed)
sdr.gain = 'auto'

plt.ion()  # Interactive mode ON
fig, ax = plt.subplots()

print("🎯 Starting live RF scan...")

try:
    while True:
        samples = sdr.read_samples(256*1024)
        power_spectrum = 20 * np.log10(np.abs(np.fft.fftshift(np.fft.fft(samples))))
        
        ax.clear()
        ax.plot(power_spectrum)
        ax.set_title('Live RF Spectrum')
        ax.set_xlabel('Frequency Bin')
        ax.set_ylabel('Power (dB)')
        plt.pause(0.05)

except KeyboardInterrupt:
    print("\n🛑 Stopping scan...")
finally:
    sdr.close()
    plt.close()

