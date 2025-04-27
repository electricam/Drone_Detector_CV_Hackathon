from flask import Flask, send_from_directory, render_template_string
import os
import time

app = Flask(__name__)

DETECTIONS_FOLDER = "detections"

HTML_TEMPLATE = """
<!doctype html>
<title>🛰️ RF Detection Dashboard</title>
<h1>📡 Latest RF Snapshots</h1>
{% for file in images %}
  <div style="margin-bottom:20px;">
    <img src="/detections/{{ file }}" width="600"><br>
    {{ file }}
  </div>
{% endfor %}
<h2>📋 <a href="/detections/detections_log.csv" download>Download Detections Log (CSV)</a></h2>
<script>
  setTimeout(() => { location.reload(); }, 5000); // Refresh page every 5 seconds
</script>
"""

@app.route("/")
def index():
    images = sorted(
        [f for f in os.listdir(DETECTIONS_FOLDER) if f.endswith(".png")],
        key=lambda x: os.path.getmtime(os.path.join(DETECTIONS_FOLDER, x)),
        reverse=True
    )[:10]  # Show only last 10 snapshots
    return render_template_string(HTML_TEMPLATE, images=images)

@app.route("/detections/<path:filename>")
def detections(filename):
    return send_from_directory(DETECTIONS_FOLDER, filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
