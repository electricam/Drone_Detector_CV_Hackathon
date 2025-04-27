import pandas as pd
import matplotlib.pyplot as plt

def analyze_rf_data(csv_file):
    df = pd.read_csv(csv_file)
    # Example structure, adapt depending on your rtl_power format:
    frequencies = df['frequency']  
    signal_strengths = df['signal_strength']

    plt.plot(frequencies, signal_strengths)
    plt.title('RF Signal Scan')
    plt.xlabel('Frequency (Hz)')
    plt.ylabel('Signal Strength (dB)')
    plt.show()

    # Simple threshold-based detection
    threshold = -40  # Example: detect strong signals
    detections = df[df['signal_strength'] > threshold]
    if not detections.empty:
        print("🚨 Potential Drone Activity Detected!")
        print(detections)

if __name__ == "__main__":
    analyze_rf_data("drone_scan.csv")

pip install pyrtlsdr