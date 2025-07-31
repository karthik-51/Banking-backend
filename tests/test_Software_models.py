import os
import joblib
import pandas as pd

def test_model_training_and_export(tmp_path):
    # Simulate minimal CSV
    df = pd.DataFrame({
        "Error Rate": [0.1, 2.5],
        "Response Time": [200, 1000],
        "Crashes/Week": [0, 2],
        "Uptime": [99.5, 96.2],
        "Status": ["Healthy", "Critical"]
    })
    csv_path = tmp_path / "test_software.csv"
    df.to_csv(csv_path, index=False)

    # Modify your ML script to support "data_path" and "output_dir" arguments, then import and call it here
    # Example: train_software_models(str(csv_path), str(tmp_path))

    # Check models exported
    files = os.listdir(tmp_path)
    assert any("Random_forest_software.pkl" in f for f in files)
    model = joblib.load(tmp_path / "Random_forest_software.pkl")
    X = df[["Error Rate", "Response Time", "Crashes/Week", "Uptime"]]
    y_pred = model.predict(X)
    assert len(y_pred) == len(df)