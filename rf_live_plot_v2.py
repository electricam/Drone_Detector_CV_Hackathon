from rtlsdr import RtlSdr
import matplotlib.pyplot as plt
import numpy as np

# Initialize SDR
sdr = RtlSdr()

# SDR Settings
sdr.sample_rate = 2.4e6  # Hz
sdr.center_freq = 915e6  # Center frequency (adjust as needed)
sdr.gain = 'auto'

plt.ion()  # Turn on interactive mode
fig, ax = plt.subplots()

# Frequency axis setup
freq_axis = np.linspace(sdr.center_freq - sdr.sample_rate/2,
                        sdr.center_freq + sdr.sample_rate/2,
                        256*1024) / 1e6  # Convert Hz to MHz

print("🎯 Starting upgraded live RF scan...")

try:
    while True:
        samples = sdr.read_samples(256*1024)
        power_spectrum = 20 * np.log10(np.abs(np.fft.fftshift(np.fft.fft(samples))))
        
        ax.clear()
        ax.plot(freq_axis, power_spectrum)
        ax.set_title('📡 Live RF Spectrum (MHz)')
        ax.set_xlabel('Frequency (MHz)')
        ax.set_ylabel('Power (dB)')
        ax.set_xlim(900, 930)  # Set visible frequency window if desired
        ax.set_ylim(-80, 0)    # Set reasonable dB scale (adjust based on environment)
        
        # Highlight spikes
        threshold = -40  # dB threshold for "strong signal"
        spikes = freq_axis[power_spectrum > threshold]
        if len(spikes) > 0:
            print(f"🚨 Spike detected at: {spikes} MHz")
        
        plt.pause(0.05)

except KeyboardInterrupt:
    print("\n🛑 Stopping scan...")
finally:
    sdr.close()
    plt.close()

