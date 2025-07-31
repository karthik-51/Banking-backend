import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier
import joblib
import os

# Load the data
df = pd.read_csv("banking_software_unbalanced_dataset.csv")

# Define features and target
X = df[["Error Rate", "Response Time", "Crashes/Week", "Uptime"]]
y = df["Status"]

# Encode the target
label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)

# Standardize features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y_encoded, test_size=0.2, random_state=42)

# Output directory
output_dir = "banking_prediction/backend/classification_methods/software_predictions"

os.makedirs(output_dir, exist_ok=True)

# ------ Model Training ------

# 1. Random Forest
rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
rf_model.fit(X_train, y_train)
joblib.dump(rf_model, os.path.join(output_dir, "Random_forest_software.pkl"))

# 2. Decision Tree
dt_model = DecisionTreeClassifier(random_state=42)
dt_model.fit(X_train, y_train)
joblib.dump(dt_model, os.path.join(output_dir, "Decision_tree_software.pkl"))

# 3. XGBoost
xgb_model = XGBClassifier(use_label_encoder=False, eval_metric='mlogloss', random_state=42)
xgb_model.fit(X_train, y_train)
joblib.dump(xgb_model, os.path.join(output_dir, "XGBoost_software.pkl"))

# 4. Logistic Regression
lr_model = LogisticRegression(max_iter=200, random_state=42)
lr_model.fit(X_train, y_train)
joblib.dump(lr_model, os.path.join(output_dir, "Logistic_regression_software.pkl"))

# Save encoder and scaler for inference
joblib.dump(label_encoder, os.path.join(output_dir, "software_label_encoder.pkl"))
joblib.dump(scaler, os.path.join(output_dir, "software_scaler.pkl"))

print("All software models trained and exported to:")
print(f"📁 {output_dir}")
