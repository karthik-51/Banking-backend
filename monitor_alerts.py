import json
import time
from collections import Counter, defaultdict
from pathlib import Path

# === Paths ===
BASE_DIR = Path(__file__).resolve().parent
SOFTWARE_FILE = BASE_DIR / "predicted_software_status.json"
HARDWARE_FILE = BASE_DIR / "prediction_hardware_status.json"
SOFTWARE_ALERT_HISTORY = BASE_DIR / "software_alerts_history.json"
HARDWARE_ALERT_HISTORY = BASE_DIR / "hardware_alerts_history.json"

# === Config ===
SOFTWARE_MODELS = ["Random Forest", "Decision Tree", "XGBoost", "Logistic Regression"]
HARDWARE_MODELS = ["Random Forest", "SVM", "ANN"]
ALERT_STATUSES = ["Critical", "Warning"]
SLEEP_INTERVAL = 20  # seconds


def load_json(file_path):
    if file_path.exists():
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"[WARN] Corrupt JSON at {file_path}, reinitializing.")
            return {}
    return {}


def save_json(data, file_path):
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)


def detect_software_alerts(software_data):
    alerts = defaultdict(list)

    for bank, platforms in software_data.items():
        for software, systems in platforms.items():
            for system, preds in systems.items():
                if not isinstance(preds, dict):
                    continue
                model_votes = [preds.get(m) for m in SOFTWARE_MODELS if m in preds]
                status_counts = Counter(model_votes)

                if sum(status_counts[s] for s in ALERT_STATUSES) >=3:
                    if status_counts["Critical"] >= 2:
                        majority = "Critical"
                    else:
                        majority = status_counts.most_common(1)[0][0]

                    if majority in ALERT_STATUSES:
                        alerts[bank].append({
                            "software": software,
                            "system": system,
                            "status": majority,
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                        })

    return alerts


def detect_hardware_alerts(hardware_data):
    alerts = defaultdict(list)

    for bank, atms in hardware_data.items():
        for atm_name, preds in atms.items():
            if not isinstance(preds, dict):
                continue
            model_votes = [preds.get(m) for m in HARDWARE_MODELS if m in preds]
            status_counts = Counter(model_votes)

            if sum(status_counts[s] for s in ALERT_STATUSES) >= 3:
                majority = status_counts.most_common(1)[0][0]
                if majority in ALERT_STATUSES:
                    alerts[bank].append({
                        "atm": atm_name,
                        "status": majority,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    })
    return alerts


def append_alerts(history, new_alerts):
    updated = False
    for bank, entries in new_alerts.items():
        if bank not in history:
            history[bank] = []
        for alert in entries:
            if alert not in history[bank]:
                history[bank].append(alert)
                updated = True
    return updated


def monitor_loop():
    print("🔁 Continuous monitoring started (every 20 seconds)...\n")
    software_history = load_json(SOFTWARE_ALERT_HISTORY)
    hardware_history = load_json(HARDWARE_ALERT_HISTORY)

    while True:
        try:
            if not SOFTWARE_FILE.exists() or not HARDWARE_FILE.exists():
                print("[❌] Missing prediction files, retrying in 20 seconds...")
                time.sleep(SLEEP_INTERVAL)
                continue

            with open(SOFTWARE_FILE, "r") as f:
                software_data = json.load(f)

            with open(HARDWARE_FILE, "r") as f:
                hardware_data = json.load(f)

            new_software_alerts = detect_software_alerts(software_data)
            new_hardware_alerts = detect_hardware_alerts(hardware_data)

            # Append new software alerts
            if append_alerts(software_history, new_software_alerts):
                save_json(software_history, SOFTWARE_ALERT_HISTORY)
                print(f"✅ New software alerts saved at {time.strftime('%H:%M:%S')}")

            # Append new hardware alerts
            if append_alerts(hardware_history, new_hardware_alerts):
                save_json(hardware_history, HARDWARE_ALERT_HISTORY)
                print(f"✅ New hardware alerts saved at {time.strftime('%H:%M:%S')}")

        except Exception as e:
            print(f"[ERROR] {e}")

        time.sleep(SLEEP_INTERVAL)


if __name__ == "__main__":
    monitor_loop()
