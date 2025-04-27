# auto_upload_kml.py

import os
import time
import paramiko
from scp import SCPClient

def upload_file_to_mac(local_path, remote_path):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('134.199.213.125', port=22, username='sk123', password='9uBQxP@fPsV5#D0p#k2BrJ#gdrK3QrcM4%DuYKvM!8w')

    with SCPClient(ssh.get_transport()) as scp:
        scp.put(local_path, remote_path)


# === SETUP ===

def create_ssh_client(server, port, user, password):
    ssh = paramiko.SSHClient()
    ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(server, port, user, password)
    return ssh

uploaded_files = set()

print("\n✨ Auto-uploading KMLs enabled!")

try:
    while True:
        kml_files = [f for f in os.listdir(KML_FOLDER) if f.endswith(".kml")]

        for kml in kml_files:
            if kml not in uploaded_files:
                print(f"📂 Uploading {kml} to server...")
                try:
                    ssh = create_ssh_client(SERVER_IP, SERVER_PORT, USERNAME, PASSWORD)
                    scp = SCPClient(ssh.get_transport())
                    scp.put(os.path.join(KML_FOLDER, kml), remote_path=REMOTE_FOLDER)
                    uploaded_files.add(kml)
                    print(f"🚀 Uploaded: {kml}")
                    scp.close()
                    ssh.close()
                except Exception as e:
                    print(f"❌ Upload failed: {e}")

        time.sleep(10)  # Check for new files every 10 seconds

except KeyboardInterrupt:
    print("\n⏹️ Stopped auto-uploader.")
