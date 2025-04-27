import socket
from datetime import datetime, timedelta

# Settings
ATAK_BROADCAST_IP = "134.199.213.125"  # Multicast group common for ATAK (or use your phone IP if needed)
ATAK_BROADCAST_PORT = 4242        # Standard port ATAK listens on
DEVICE_UID = "rf-sensor-001"      # Unique ID for your Pi sensor (can be anything)

def send_event(lat, lon, freq_mhz, power_dbm):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    now = datetime.utcnow()
    start = now.isoformat() + "Z"
    stale = (now + timedelta(seconds=30)).isoformat() + "Z"

    cot_xml = f"""<event version="2.0" uid="{DEVICE_UID}" type="b-r-f" how="m-g" time="{start}" start="{start}" stale="{stale}">
  <point lat="{lat}" lon="{lon}" hae="10.0" ce="9999999.0" le="9999999.0"/>
  <detail>
    <contact callsign="RF Spike {freq_mhz:.2f}MHz"/>
    <remarks>Power: {power_dbm:.2f} dBm</remarks>
  </detail>
</event>"""

    sock.sendto(cot_xml.encode(), (ATAK_BROADCAST_IP, ATAK_BROADCAST_PORT))
    sock.close()

