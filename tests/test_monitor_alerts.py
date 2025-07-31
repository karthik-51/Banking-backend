from monitor_alerts import detect_software_alerts

def test_detect_software_alerts():
    sample_data = {
        "Test Bank": {
            "TestSoft": {
                "TestSystem": {
                    "Random Forest": "Warning",
                    "Decision Tree": "Critical",
                    "XGBoost": "Critical",
                    "Logistic Regression": "Critical"
                }
            }
        }
    }
    alerts = detect_software_alerts(sample_data)
    assert "Test Bank" in alerts
    assert len(alerts["Test Bank"]) > 0
    assert alerts["Test Bank"][0]['status'] == "Critical"