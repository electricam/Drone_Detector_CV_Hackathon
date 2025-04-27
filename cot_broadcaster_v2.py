# cot_broadcaster_v2.py

import socket
from datetime import datetime, timedelta

# Settings
ATAK_BROADCAST_IP = "134.199.213.125"  # WebTAK server IP
ATAK_BROADCAST_PORT = 4242             # Standard ATAK port
DEVICE_UID = "rf-sensor-001"            # Unique ID for your device

def send_event(lat, lon, freq_mhz, power_dbm):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    now = datetime.utcnow()
    time_str = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    stale_str = (now + timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%SZ")

    cot_xml = f"""<event version="2.0" uid="{DEVICE_UID}" type="b-r-f" how="m-g" time="{time_str}" start="{time_str}" stale="{stale_str}">
  <point lat="{lat}" lon="{lon}" hae="10.0" ce="50.0" le="9999.0"/>
  <detail>
    <contact callsign="RF {freq_mhz:.2f}MHz {power_dbm:.2f}dB"/>
    <remarks>RF detection at {freq_mhz:.2f} MHz with strength {power_dbm:.2f} dB</remarks>
    <takv device="RF Scanner" version="1.0" platform="Pi"/>
    <__group role="Team Member" name="RF Detection"/>
  </detail>
</event>"""

    sock.sendto(cot_xml.encode(), (ATAK_BROADCAST_IP, ATAK_BROADCAST_PORT))
    sock.close()
