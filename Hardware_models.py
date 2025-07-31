import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
import joblib
import os

# Load dataset
df = pd.read_csv("hardware_maintenance_balanced_dataset.csv")

# Features and target
X = df[["ATM Vibration", "Power Supply", "CPU Usage", "Memory", "Storage"]]
y = df["Status"]

# Encode target labels
label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)

# Standardize features for SVM and ANN
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Train-Test split
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y_encoded, test_size=0.2, random_state=42)

# Directory to save models
model_dir = "banking_prediction/backend/classification_methods/hardware_prediction"
os.makedirs(model_dir, exist_ok=True)

# ----- SVM -----
svm_model = SVC(kernel='rbf', probability=True, random_state=42)
svm_model.fit(X_train, y_train)
joblib.dump(svm_model, os.path.join(model_dir, "svm_hardware.pkl"))

# ----- Random Forest -----
rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
rf_model.fit(X_train, y_train)
joblib.dump(rf_model, os.path.join(model_dir, "random_forest_hardware.pkl"))

# ----- ANN (MLPClassifier) -----
ann_model = MLPClassifier(hidden_layer_sizes=(64, 32), activation='relu', max_iter=500, random_state=42)
ann_model.fit(X_train, y_train)
joblib.dump(ann_model, os.path.join(model_dir, "ann_hardware.pkl"))

# Save Label Encoder and Scaler
joblib.dump(label_encoder, os.path.join(model_dir, "hardware_label_encoder.pkl"))
joblib.dump(scaler, os.path.join(model_dir, "hardware_scaler.pkl"))

print(" All models trained and saved successfully in the 'exported_models' directory.")
