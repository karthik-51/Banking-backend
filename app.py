from flask import Flask, request, jsonify, make_response, send_file
import numpy as np
from werkzeug.exceptions import HTTPException
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, create_access_token,
    jwt_required, get_jwt_identity, get_jwt
)
from pymongo import MongoClient
from datetime import timedelta
import os
import json
import threading
import time
import random
import bcrypt
from generatepdf import generate_pdf_report  # Import your PDF generation function


# ✅ Flask App Setup
app = Flask(__name__)

# Global error handler for HTTPException (e.g., 404, 400)
@app.errorhandler(HTTPException)
def handle_http_exception(e):
    response = e.get_response()
    response.data = json.dumps({
        "error": e.description,
        "code": e.code
    })
    response.content_type = "application/json"
    return response

# Global error handler for unhandled exceptions
@app.errorhandler(Exception)
def handle_generic_exception(e):
    return jsonify({
        "error": str(e) or "Internal server error",
        "code": 500
    }), 500

# ✅ Enable CORS for frontend origin & allow credentials
CORS(app, origins=["http://localhost:5173"], supports_credentials=True)



# ✅ JWT Config
app.config["JWT_SECRET_KEY"] = "12345678"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=10)
app.config["JWT_BLACKLIST_ENABLED"] = True
app.config["JWT_BLACKLIST_TOKEN_CHECKS"] = ["access"]
jwt = JWTManager(app)
jwt_blacklist = set()

# ✅ MongoDB Setup
#MONGO_URI = "mongodb+srv://user1:pass1@cluster0.ueflwgp.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
MONGO_URI="mongodb+srv://mandhalakarthikreddy:UY0ka5VMDsXKXX74@cluster0.9idd88a.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client["user_db"]
users_collection = db["users"]

# Existing software metrics file
FILE_PATH = 'software_metrics.json'

# ✅ New hardware metrics file
FILE_PATH_HARDWARE =  'hardware_metrics.json'

banks = {
    'State Bank of India (SBI)': ['YONO SBI', 'Online SBI'],
    'HDFC Bank': ['PayZapp', 'HDFC Sky'],
    'ICICI Bank': ['iMobile', 'Pockets'],
    'Axis Bank': ['Axis Mobile'],
    'Punjab National Bank (PNB)': ['PNB One'],
    'Kotak Mahindra Bank': ['Kotak 811'],
    'Bank of Baroda': ['Baroda Connect'],
    'Union Bank of India': ['Union Mobile'],
    'Canara Bank': ['Canara mBanking'],
    'IDBI Bank': ['IDBI Go']
}

atms = ['ATM 1', 'ATM 2']  # ✅ New list of ATMs

systems = [
    'Core Banking System',
    'Payment Gateway',
    'Mobile App Services',
    'Notification Engine',
    'Fraud Detection Engine',
    'Loan Approval System'
]

import random

def generate_random_metrics():
    if random.random() < 0.95:
        # Healthy-like metrics (60% of the time)
        return {
            "Error Rate": round(random.uniform(0.1, 1.5), 2),
            "Response Time": random.randint(200, 400),
            "Crashes/Week": 0,
            "Uptime": round(random.uniform(98.0, 100.0), 2)
        }
    else:
        # Warning or Critical metrics (40% of the time)
        return {
            "Error Rate": round(random.uniform(3.0, 5.0), 2),
            "Response Time": random.randint(800, 1200),
            "Crashes/Week": random.randint(1, 3),
            "Uptime": round(random.uniform(95.0, 97.0), 2)
        }


def build_full_metrics():
    metrics_data = {}
    for bank, softwares in banks.items():
        metrics_data[bank] = {}
        for software in softwares:
            metrics_data[bank][software] = {}
            for system in systems:
                metrics_data[bank][software][system] = generate_random_metrics()
    return metrics_data

# ✅ Hardware metrics generator
def generate_hardware_metrics():
    if random.random() < 0.6:  # 60% chance to generate healthy metrics
        return {
            "cpu": random.randint(10, 50),        # Healthy: Low to moderate CPU usage
            "memory": random.randint(20, 60),     # Healthy: Not maxing out memory
            "storage": random.randint(25, 70),    # Healthy: Below 70% usage
            "temperature": random.randint(30, 55) # Healthy: Cooler temperatures
        }
    else:  # 40% chance to generate non-healthy (Warning or Critical) metrics
        # Mix of warning/critical ranges
        return {
            "cpu": random.randint(60, 95),
            "memory": random.randint(70, 95),
            "storage": random.randint(75, 100),
            "temperature": random.randint(60, 85)
        }

def build_hardware_metrics():
    data = {}
    for bank in banks:
        data[bank] = {}
        for atm in atms:
            data[bank][atm] = {
                "vibration": random.randint(40, 90),
                "power": random.randint(50, 100),
                "components": {
                    "Server Cluster": generate_hardware_metrics(),
                    "Storage Array": generate_hardware_metrics(),
                    "Network Switch": generate_hardware_metrics()
                }
            }
    return data

# ✅ Update both metrics periodically
def update_metrics_periodically(interval=20):
    while True:
        updated_software = build_full_metrics()
        updated_hardware = build_hardware_metrics()

        with open(FILE_PATH, 'w') as f:
            json.dump(updated_software, f, indent=2)

        with open(FILE_PATH_HARDWARE, 'w') as f:
            json.dump(updated_hardware, f, indent=2)

        print("[Updated software and hardware metrics] at", time.strftime("%H:%M:%S"))
        time.sleep(interval)

# MongoDB Atlas connection


# MongoDB Connection

# Check if token is blacklisted or expired
@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    return jti in jwt_blacklist



@app.route('/api/signup', methods=['POST', 'OPTIONS'])
def signup():
    if request.method == 'OPTIONS':
        # Preflight request
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
        return response
    try:
        data = request.get_json()
        print(data)

        email = data.get('email')
        password = data.get('password')
        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
       
        name = data.get('name')
        phone_no = data.get('phone_no')
        bank = data.get('bank')
        designation = data.get('designation')

        if not email or not password:
            resp = jsonify({"error": "Email and password required"})
            resp.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
            resp.headers.add('Access-Control-Allow-Credentials', 'true')
            return resp, 400

        if users_collection.find_one({"email": email}):
            resp = jsonify({"error": "User already exists"})
            resp.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
            resp.headers.add('Access-Control-Allow-Credentials', 'true')
            return resp, 400

        users_collection.insert_one({
            "email": email,
            "password": hashed_pw,
            "username": name,
            "phone no": phone_no,
            "bank": bank,
            "designation": designation
        })

        access_token = create_access_token(identity=email)
        resp = jsonify({"message": "Signup successful", "access_token": access_token})
        resp.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
        resp.headers.add('Access-Control-Allow-Credentials', 'true')
        return resp, 200

    except Exception as e:
        resp = jsonify({"error": str(e)})
        resp.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
        resp.headers.add('Access-Control-Allow-Credentials', 'true')
        return resp, 500




@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({"error": "Email and password required"}), 400

        user = users_collection.find_one({"email": email})
        if not user or not bcrypt.checkpw(password.encode('utf-8'), user['password']):
        #if not user or not user['password']==password:
            return jsonify({"error": "Wrong credentials"}), 401

        access_token = create_access_token(identity=email,
                                           expires_delta=timedelta(hours=10))
        return jsonify(access_token=access_token), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    
@app.route('/api/logout', methods=['POST'])
@jwt_required()
def logout():
    try:
        jti = get_jwt()["jti"]  # Unique identifier for JWT
        jwt_blacklist.add(jti)
        return jsonify({"message": "Successfully logged out"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/change_password', methods=['POST'])
def change_password():
    try:
        # Get data from the request body
        data = request.get_json()
        email = data.get('emai')
        new_password = data.get('new_password')

        if not new_password:
            return jsonify({"error": "new password are required"}), 400

        user = users_collection.find_one({"email": email})

        if not user:
            return jsonify({"error": "No user found"}), 401
        hashed_new_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())

        users_collection.update_one(
            {"email": email},
            {"$set": {"password": hashed_new_password}}
        )

        return jsonify({"message": "Password changed successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

#timer 
@app.route('/api/timer',methods=['PUT'])
@jwt_required()
def add_timer():
    try:
        data=request.get_json()
        email=get_jwt_identity()
        timer=data.get('timer')
        
        user = users_collection.find_one({"email": email})
        if not timer:
            return jsonify({"error":"Timer value is Requierd "}),401
        if not user:
            return jsonify({"error": "Not found email"}), 404
        users_collection.update_one({"email":email}, {"$set": {"timer": timer}})
        return jsonify({"message": "Successfully  added timer "}), 200
        
    except Exception as e:
        return jsonify({"error":str(e)}),500

@app.route("/api/get-bank",methods=['GET'])
@jwt_required()
def get_bank():
    try:
        email=get_jwt_identity()
        user = users_collection.find_one({"email": email})
        
        if not user:
            return jsonify({"error": "Not found email"}), 404
        return jsonify(bank=user["bank"]),200
    except Exception as e:
        return jsonify({"error": str(e)}), 500 
         


@app.route("/api/software-metrics", methods=["GET"])
def get_metrics():
    try:
        with open(FILE_PATH, 'r') as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/hardware-metrics", methods=["GET"])
def get_hardware_metrics():
    try:
        with open(FILE_PATH_HARDWARE, 'r') as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/software-alerts')
def get_software_alerts():
    try:
        with open('software_alerts_history.json') as f:
            data = json.load(f)
        return jsonify(data)
    except FileNotFoundError:
        return jsonify({"error": "software_alerts_history.json not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/hardware-alerts')
def get_hardware_alerts():
    try:
        with open('hardware_alerts_history.json') as f:
            data = json.load(f)
        return jsonify(data)
    except FileNotFoundError:
        return jsonify({"error": "hardware_alerts_history.json not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/generate-report-pdf', methods=['POST'])
@jwt_required()
def generate_report_pdf_endpoint():
    try:
        bank_name = None
        current_user_email = get_jwt_identity()
        
        if current_user_email:
            user = users_collection.find_one({"email": current_user_email})  # ✅ FIXED HERE
            if user and "bank" in user:
                bank_name = user.get("bank")

        data = request.get_json()
        if not bank_name:
            bank_name = data.get('bankName')

        if not bank_name:
            return jsonify({
                "error": "Bank name not provided in JWT or request body. Please provide 'bankName' in the JSON body or ensure a valid JWT is supplied with bank information."
            }), 400

        from_date_str = data.get('fromDate')
        to_date_str = data.get('toDate')

        pdf_buffer, error_message = generate_pdf_report(bank_name, from_date_str, to_date_str)

        if error_message:
            return jsonify({"error": error_message}), 500

        filename_bank_part = bank_name.replace(" ", "_")
        filename_date_part = ""
        if from_date_str and to_date_str:
            filename_date_part = f"{from_date_str.replace('-', '')}_to{to_date_str.replace('-', '')}"
        elif from_date_str:
            filename_date_part = f"from{from_date_str.replace('-', '')}_to_Current"
        elif to_date_str:
            filename_date_part = f"From_Start_to{to_date_str.replace('-', '')}"
        else:
            filename_date_part = "_All_Time"

        download_name = f"{filename_bank_part}_Performance_Report{filename_date_part}.pdf"

        return send_file(pdf_buffer, download_name=download_name, as_attachment=True, mimetype='application/pdf')

    except Exception as e:
        print(f"Error generating PDF: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # Initialize both files if not present
    if not os.path.exists(FILE_PATH):
        with open(FILE_PATH, 'w') as f:
            json.dump(build_full_metrics(), f, indent=2)

    if not os.path.exists(FILE_PATH_HARDWARE):
        with open(FILE_PATH_HARDWARE, 'w') as f:
            json.dump(build_hardware_metrics(), f, indent=2)

    # Start background thread to update both
    thread = threading.Thread(target=update_metrics_periodically, daemon=True)
    thread.start()

    app.run(debug=True, port=5000)