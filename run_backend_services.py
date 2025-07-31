
import subprocess
import time
from pathlib import Path

# Define the base path to backend folder
BASE_DIR = Path(__file__).resolve().parent

# List of Python files to run
scripts = [
    "app.py",
    "Hardware_models.py",
     "monitor_alerts.py",
    "prediction_runner.py",
    "recent_alerts.py",
    "Software_models.py",
    "alert_scheduler.py"
]

# Dictionary to store running processes
processes = {}

try:
    print(" Starting all backend services...\n")

    for script in scripts:
        script_path = BASE_DIR / script
        if not script_path.exists():
            print(f"⚠  {script} not found.")
            continue

        # Start each script in a new subprocess
        process = subprocess.Popen(["python", str(script_path)])
        processes[script] = process
        print(f"✅ Launched: {script}")

    print("\n📡 All services running. Press Ctrl+C to stop.")

    # Keep the main process alive
    while True:
        time.sleep(10)

except KeyboardInterrupt:
    print("\n🛑 Shutting down all services...")
    for name, process in processes.items():
        process.terminate()
        print(f"⛔ Stopped: {name}")
    print("✅ All services stopped.")

except Exception as e:
    print(f"❌ Error occurred: {e}")