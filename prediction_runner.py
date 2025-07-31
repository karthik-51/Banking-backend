import os
import json
import time
import joblib
import pandas as pd
import threading
from sklearn.preprocessing import LabelEncoder, StandardScaler

# === Paths ===
BASE_DIR = os.path.dirname(__file__)

# Software paths
SOFTWARE_METRICS_PATH = os.path.join(BASE_DIR, 'software_metrics.json')
SOFTWARE_OUTPUT_PATH = os.path.join(BASE_DIR, 'predicted_software_status.json')
SOFTWARE_MODELS_DIR = os.path.join(BASE_DIR, 'classification_methods', 'software_predictions')

# Hardware paths
HARDWARE_METRICS_PATH = os.path.join(BASE_DIR, 'hardware_metrics.json')
HARDWARE_OUTPUT_PATH = os.path.join(BASE_DIR, 'prediction_hardware_status.json')
HARDWARE_MODELS_DIR = os.path.join(BASE_DIR, 'classification_methods', 'hardware_prediction')

# === Load Software Models ===
software_models = {
    'Random Forest': joblib.load(os.path.join(SOFTWARE_MODELS_DIR, 'Random_forest_software.pkl')),
    'Decision Tree': joblib.load(os.path.join(SOFTWARE_MODELS_DIR, 'Decision_tree_software.pkl')),
    'XGBoost': joblib.load(os.path.join(SOFTWARE_MODELS_DIR, 'XGBoost_software.pkl')),
    'Logistic Regression': joblib.load(os.path.join(SOFTWARE_MODELS_DIR, 'Logistic_regression_software.pkl'))
}
software_scaler = joblib.load(os.path.join(SOFTWARE_MODELS_DIR, 'software_scaler.pkl'))
software_encoder = joblib.load(os.path.join(SOFTWARE_MODELS_DIR, 'software_label_encoder.pkl'))

# === Load Hardware Models ===
hardware_models = {
    'Random Forest': joblib.load(os.path.join(HARDWARE_MODELS_DIR, 'random_forest_hardware.pkl')),
    'SVM': joblib.load(os.path.join(HARDWARE_MODELS_DIR, 'svm_hardware.pkl')),
    'ANN': joblib.load(os.path.join(HARDWARE_MODELS_DIR, 'ann_hardware.pkl'))
}
hardware_scaler = joblib.load(os.path.join(HARDWARE_MODELS_DIR, 'hardware_scaler.pkl'))
hardware_encoder = joblib.load(os.path.join(HARDWARE_MODELS_DIR, 'hardware_label_encoder.pkl'))

def predict_software():
    try:
        with open(SOFTWARE_METRICS_PATH, 'r') as f:
            data = json.load(f)

        results = {}

        for bank, softwares in data.items():
            results[bank] = {}
            for software, systems in softwares.items():
                results[bank][software] = {}
                for system, features in systems.items():
                    df = pd.DataFrame([features])
                    scaled = software_scaler.transform(df)
                    predictions = {
                        name: software_encoder.inverse_transform([model.predict(scaled)[0]])[0]
                        for name, model in software_models.items()
                    }
                    results[bank][software][system] = {
                        "features": features,
                        **predictions
                    }
        # print("[✓] Software predictions generated",results)
        with open(SOFTWARE_OUTPUT_PATH, 'w') as f:
            json.dump(results, f, indent=2)
            

        print("[✓] Software predictions updated")
    except Exception as e:
        print("[Error in software prediction]:", e)

def predict_hardware():
    try:
        with open(HARDWARE_METRICS_PATH, 'r') as f:
            data = json.load(f)

        results = {}

        for bank, atms in data.items():
            results[bank] = {}
            for atm, metrics in atms.items():
                try:
                    vibration = metrics.get('vibration', 0)
                    power = metrics.get('power', 0)

                    # Aggregate CPU, Memory, Storage from all components
                    components = metrics.get('components', {})
                    cpu = memory = storage = count = 0

                    for comp_data in components.values():
                        cpu += comp_data.get('cpu', 0)
                        memory += comp_data.get('memory', 0)
                        storage += comp_data.get('storage', 0)
                        count += 1

                    if count == 0:
                        avg_cpu = avg_memory = avg_storage = 0
                    else:
                        avg_cpu = cpu // count
                        avg_memory = memory // count
                        avg_storage = storage // count

                    df = pd.DataFrame([[vibration, power, avg_cpu, avg_memory, avg_storage]],
                        columns=['ATM Vibration', 'Power Supply', 'CPU Usage', 'Memory', 'Storage']
                    )

                    scaled = hardware_scaler.transform(df)
                    predictions = {
                        name: hardware_encoder.inverse_transform([model.predict(scaled)[0]])[0]
                        for name, model in hardware_models.items()
                    }

                    results[bank][atm] = {
                        "features": df.iloc[0].to_dict(),
                        **predictions
                    }

                except Exception as atm_error:
                    print(f"[Error processing {bank} - {atm}]: {atm_error}")
        # print("[✓] Hardware predictions generated", results)
        with open(HARDWARE_OUTPUT_PATH, 'w') as f:
            json.dump(results, f, indent=2)

        print("[✓] Hardware predictions updated")

    except Exception as e:
        print("[Error in hardware prediction]:", e)

def run_predictions_every(interval=20):
    while True:
        predict_software()
        predict_hardware()
        time.sleep(interval)

if __name__ == "__main__":
    thread = threading.Thread(target=run_predictions_every, daemon=True)
    thread.start()
    print("[✓] Prediction runner started")
    while True:
        time.sleep(3600)  # Keep main thread alive
