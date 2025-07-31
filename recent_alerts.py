from flask import Flask, jsonify
from datetime import datetime, timedelta
import json
import os

app = Flask(__name__)

def parse_timestamp(ts):
    try:
        return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None

@app.route('/recent-alerts', methods=['GET'])
def get_recent_alerts():
    now = datetime.now()
    threshold = timedelta(seconds=20)

    software_path = os.path.join(app.root_path, 'software_alerts_history.json')
    hardware_path = os.path.join(app.root_path, 'hardware_alerts_history.json')

    try:
        with open(software_path, 'r') as sf:
            software_data = json.load(sf)
        with open(hardware_path, 'r') as hf:
            hardware_data = json.load(hf)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    alerts = []

    # Process software alerts
    for bank, records in software_data.items():
        for alert in records:
            timestamp = parse_timestamp(alert.get('timestamp', ''))
            if timestamp and (now - timestamp) <= threshold:
                alerts.append({
                    'bank': bank,
                    'component': f"{alert.get('software')} - {alert.get('system')}",
                    'severity': alert.get('status'),
                    'type': 'Software',
                    'time': alert.get('timestamp'),
                    'message': f"{alert.get('system')} in {alert.get('software')} is {alert.get('status')}"
                })

    # Process hardware alerts
    for bank, records in hardware_data.items():
        for alert in records:
            timestamp = parse_timestamp(alert.get('timestamp', ''))
            if timestamp and (now - timestamp) <= threshold:
                alerts.append({
                    'bank': bank,
                    'component': alert.get('atm'),
                    'severity': alert.get('status'),
                    'type': 'Hardware',
                    'time': alert.get('timestamp'),
                    'message': f"{alert.get('atm')} in {bank} is {alert.get('status')}"
                })

    return jsonify(alerts)
